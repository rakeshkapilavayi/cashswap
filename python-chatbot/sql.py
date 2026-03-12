from groq import Groq
import os
import re
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from geopy.distance import geodesic

load_dotenv()

# --- Lazy Groq client ---
# DO NOT create Groq() at module level — gunicorn --preload runs imports
# before env vars are available, which crashes the server.
_client_sql = None
GROQ_MODEL = None

def _get_client():
    global _client_sql, GROQ_MODEL
    if _client_sql is None:
        _client_sql = Groq(api_key=os.getenv("GROQ_API_KEY"))
        GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    return _client_sql

def _get_model():
    _get_client()  # ensure initialized
    return GROQ_MODEL


# --- Intent Detection Prompt ---
intent_prompt = """You are an expert at analyzing user questions about money exchange to determine what information is missing.

Analyze the user's question and determine:
1. What does the user HAVE? (what they want to give)
2. What does the user WANT? (what they want to receive)
3. Is the amount mentioned?

IMPORTANT: 
- "cash to UPI" means: user HAS cash, WANTS UPI (so find people with UPI available)
- "UPI to cash" means: user HAS UPI, WANTS cash (so find people with cash available)
- "I want cash" means: user WANTS cash (find people with cash)
- "I have UPI" means: user HAS UPI, WANTS cash (find people with cash)

Respond ONLY in this exact format:
USER_HAS: [cash/upi/not_specified]
USER_WANTS: [cash/upi/both/not_specified]
AMOUNT: [number or not_specified]
NEEDS_CLARIFICATION: [yes/no]

Examples:
Question: "Find people near me"
USER_HAS: not_specified
USER_WANTS: not_specified
AMOUNT: not_specified
NEEDS_CLARIFICATION: yes

Question: "I want to exchange cash to UPI"
USER_HAS: cash
USER_WANTS: upi
AMOUNT: not_specified
NEEDS_CLARIFICATION: yes

Question: "I need cash, I have UPI"
USER_HAS: upi
USER_WANTS: cash
AMOUNT: not_specified
NEEDS_CLARIFICATION: yes

Question: "Find people with 500 rupees cash to UPI"
USER_HAS: cash
USER_WANTS: upi
AMOUNT: 500
NEEDS_CLARIFICATION: no

Question: "I want to convert 1000 UPI to cash"
USER_HAS: upi
USER_WANTS: cash
AMOUNT: 1000
NEEDS_CLARIFICATION: no

Question: "Find people with cash"
USER_HAS: not_specified
USER_WANTS: cash
AMOUNT: not_specified
NEEDS_CLARIFICATION: yes

Question: "Show me people with UPI available"
USER_HAS: not_specified
USER_WANTS: upi
AMOUNT: not_specified
NEEDS_CLARIFICATION: yes
"""

# --- SQL Generation Prompt ---
sql_prompt = """You are an expert in understanding the database schema and generating SQL queries for a natural language question asked
pertaining to the data you have. The schema is provided in the schema tags.

<schema> 
table: users
fields: 
id - integer (primary key, user id)
name - string (name of the user)
email - string (email of the user)
phone - string (phone number of the user)
password_hash - string (hashed password)
latitude - float (latitude coordinate of user location)
longitude - float (longitude coordinate of user location)
profile_photo - string (path to profile photo)
created_at - datetime (account creation timestamp)

table: wallets
fields:
id - integer (primary key, wallet id)
user_id - integer (foreign key to users table)
cash_amount - float (amount of cash the user has available for exchange)
upi_amount - float (amount the user can exchange via UPI)
updated_at - datetime (last update timestamp)
</schema>

Important notes:
- When searching for users with cash, check: cash_amount > 0 (or cash_amount >= specified_amount)
- When searching for users with UPI, check: upi_amount > 0 (or upi_amount >= specified_amount)
- When searching for both cash AND UPI, check: (cash_amount > 0 OR upi_amount > 0)
- Always JOIN users and wallets tables using users.id = wallets.user_id
- For location-based queries, select all users with their coordinates
- Always exclude the current user if user_id is mentioned: WHERE users.id != user_id
- The query should have all relevant fields: users.id, users.name, users.email, users.phone, users.latitude, users.longitude, wallets.cash_amount, wallets.upi_amount

Just the SQL query is needed, nothing more. Always provide the SQL in between the <SQL></SQL> tags.
"""

# --- Comprehension Prompt ---
comprehension_prompt = """You are an expert in understanding the context of money exchange questions and replying based on the user data provided.

You will be provided with Question: and Data:. The data contains user information with their available cash/UPI amounts and distance from the requester.

Reply in natural, friendly language without technical jargon. Do not say "Based on the data" or similar phrases.

When listing users available for money exchange, format the response as:

Here are the people near you who can exchange money:

1. **[Name]**
   - Phone: [phone]
   - Available Cash: Rs. [cash_amount]
   - Available UPI: Rs. [upi_amount]
   - Distance: [distance] km away

If no users are found, reply: "Sorry, there are no users available near you for money exchange at the moment."

Be conversational and helpful in your response.
"""


# --- Intent Detection ---
def detect_intent(question):
    """Detect user intent from question using Groq"""
    try:
        response = _get_client().chat.completions.create(
            messages=[
                {"role": "system", "content": intent_prompt},
                {"role": "user", "content": f"Question: {question}"}
            ],
            model=_get_model(),
            temperature=0.1,
            max_tokens=100
        )

        result = response.choices[0].message.content.strip()
        lines = result.split('\n')

        intent = {
            'user_has': 'not_specified',
            'user_wants': 'not_specified',
            'amount': 'not_specified',
            'needs_clarification': True
        }

        for line in lines:
            if line.startswith('USER_HAS:'):
                intent['user_has'] = line.split(':', 1)[1].strip().lower()
            elif line.startswith('USER_WANTS:'):
                intent['user_wants'] = line.split(':', 1)[1].strip().lower()
            elif line.startswith('AMOUNT:'):
                amt = line.split(':', 1)[1].strip()
                intent['amount'] = amt if amt == 'not_specified' else amt
            elif line.startswith('NEEDS_CLARIFICATION:'):
                val = line.split(':', 1)[1].strip().lower()
                intent['needs_clarification'] = (val == 'yes')

        return intent

    except Exception as e:
        print(f"Intent detection error: {e}")
        return {
            'user_has': 'not_specified',
            'user_wants': 'not_specified',
            'amount': 'not_specified',
            'needs_clarification': True
        }


# --- Build Enhanced Question ---
def build_enhanced_question(original_question, intent_info, current_user_id):
    user_wants = intent_info['user_wants']
    amount = intent_info['amount']

    try:
        amount_val = float(amount) if amount != 'not_specified' else 0
    except Exception:
        amount_val = 0

    if user_wants == 'cash':
        enhanced = (f"Find all users who have at least {amount_val} rupees in cash_amount"
                    if amount_val > 0 else
                    "Find all users who have cash_amount greater than 0")
    elif user_wants == 'upi':
        enhanced = (f"Find all users who have at least {amount_val} rupees in upi_amount"
                    if amount_val > 0 else
                    "Find all users who have upi_amount greater than 0")
    else:
        enhanced = (f"Find all users who have at least {amount_val} rupees in either cash_amount or upi_amount"
                    if amount_val > 0 else
                    "Find all users who have either cash_amount greater than 0 or upi_amount greater than 0")

    if current_user_id:
        enhanced += f" and exclude user with id = {current_user_id}"

    return enhanced


# --- Generate SQL Query ---
def generate_sql_query(question):
    chat_completion = _get_client().chat.completions.create(
        messages=[
            {"role": "system", "content": sql_prompt},
            {"role": "user", "content": question},
        ],
        model=_get_model(),
        temperature=0.2,
        max_tokens=1024
    )
    return chat_completion.choices[0].message.content


# --- Distance Calculation ---
def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        return round(geodesic((lat1, lon1), (lat2, lon2)).kilometers, 2)
    except Exception:
        return None


# --- Filter by Radius ---
def filter_by_radius(df, user_lat, user_lon, radius_km=10):
    if df is None or df.empty:
        return df

    print(f"🔍 Filtering by radius: {radius_km} km from ({user_lat}, {user_lon})")

    distances = []
    for _, row in df.iterrows():
        d = calculate_distance(user_lat, user_lon, row['latitude'], row['longitude'])
        distances.append(d)

    df = df.copy()
    df['distance'] = distances
    df = df[df['distance'] <= radius_km]
    df = df.sort_values('distance')

    print(f"After filter: {len(df)} users within {radius_km} km")
    return df


# --- Run SQL Query ---
def run_query(query):
    try:
        db_path = Path(__file__).parent / "cashswap.db"
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        print(f"🔍 Query returned {len(df)} rows")
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return None


# --- Data Comprehension ---
def data_comprehension(question, context):
    chat_completion = _get_client().chat.completions.create(
        messages=[
            {"role": "system", "content": comprehension_prompt},
            {"role": "user", "content": f"QUESTION: {question}. DATA: {context}"},
        ],
        model=_get_model(),
        temperature=0.2,
    )
    return chat_completion.choices[0].message.content
