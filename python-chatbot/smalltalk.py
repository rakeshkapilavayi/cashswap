import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Lazy init — do NOT create Groq() at module level.
# gunicorn --preload runs imports before env vars are set, which crashes the app.
_groq_client = None

def _get_client():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    return _groq_client


def talk(query):
    prompt = (
        "You are a helpful and friendly chatbot. Besides answering FAQs and suggesting persons, "
        "you can engage in light small talk to make the usage of this CashSwap experience more pleasant. "
        "Keep your responses concise—no more than two lines—and stay relevant to your role as a CashSwap assistant. "
        "CashSwap is a peer-to-peer (P2P) exchange platform that connects users who want to swap physical cash "
        "for digital UPI money and vice versa.\n\n"
        f"QUESTION: {query}"
    )
    completion = _get_client().chat.completions.create(
        model=os.environ.get("GROQ_MODEL", "llama3-8b-8192"),
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content


if __name__ == "__main__":
    print(talk("Hi!"))
