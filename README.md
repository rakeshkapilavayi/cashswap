# 💬 CashSwap AI Chatbot

> An intelligent AI-powered chatbot built for **[CashSwap](https://cashswapp.vercel.app/)** — a peer-to-peer platform that connects users to swap physical cash ↔ UPI money.

[![Live Website](https://img.shields.io/badge/CashSwap-Live%20Website-purple?style=for-the-badge)](https://cashswapp.vercel.app/)
[![Chatbot API](https://img.shields.io/badge/Chatbot%20API-Render-blue?style=for-the-badge)](https://cashswap-chatbot.onrender.com/)
[![Backend API](https://img.shields.io/badge/Backend%20API-Render-green?style=for-the-badge)](https://datapulse-backend-ojwl.onrender.com/)
[![LLaMA](https://img.shields.io/badge/LLaMA-3.1%20via%20GROQ-orange?style=for-the-badge)](https://groq.com/)

---

## 📌 What is CashSwap?

**CashSwap** is a peer-to-peer (P2P) exchange platform — think of it like OLX, but instead of goods, users exchange **cash and UPI money**. It connects nearby users who want to swap physical cash with those who need digital UPI transfers, and vice versa.

This chatbot is the AI assistant embedded inside the CashSwap platform. It helps users:
- Find nearby people available for exchange
- Get answers to platform-related FAQs
- Have natural conversations while using the app

---

## 🌐 Links

| Resource | URL |
|----------|-----|
| 🌍 CashSwap Website | [cashswapp.vercel.app](https://cashswapp.vercel.app/) |
| 🤖 Chatbot API | [cashswap-chatbot.onrender.com](https://cashswap-chatbot.onrender.com/) |
| ⚙️ Backend API | [datapulse-backend-ojwl.onrender.com](https://datapulse-backend-ojwl.onrender.com/) |

---

## ▶️ How to Use CashSwap + Chatbot

> ⚠️ **Important:** The servers are hosted on Render's free tier and may be in a sleep state. You must wake them up before using the app.

### Step 1 — Wake Up the Backend Servers

Open both of these links in your browser **before** visiting the website. Wait until each one shows a response (may take 30–60 seconds on first load):

1. 👉 [cashswap-chatbot.onrender.com](https://cashswap-chatbot.onrender.com/) — Chatbot API
2. 👉 [datapulse-backend-ojwl.onrender.com](https://datapulse-backend-ojwl.onrender.com/) — Main Backend

> Once you see a response (e.g., `{"status": "ok"}` or a welcome message), the servers are awake and ready.

---

### Step 2 — Visit the CashSwap Website

Go to 👉 **[cashswapp.vercel.app](https://cashswapp.vercel.app/)**

---

### Step 3 — Create an Account

- Click **Sign Up**
- Enter your name, email, and phone number
- Verify and complete your profile
- Set up your **wallet** — add how much cash or UPI balance you're willing to exchange

---

### Step 4 — Open the Chatbot

- Look for the **💬 chat icon** at the bottom-right corner of the page
- Click it to open the CashSwap AI Chatbot
- Start chatting!

---

### Step 5 — Try It Out

Here are some things you can ask:

| What you want | Example query |
|---------------|--------------|
| Find nearby users | *"I need to exchange ₹500 cash to UPI"* |
| Platform FAQ | *"Is CashSwap safe to use?"* |
| Wallet help | *"Why is my wallet showing 0 balance?"* |
| Expand search | *"Show me users within 25 km"* |
| Casual chat | *"Hey, how does this work?"* |

---

### 🎥 Video Demo

> Not sure how it works? Watch the demo video to see the full walkthrough of the chatbot in action.

[![CashSwap Chatbot Demo](https://img.youtube.com/vi/PI1X0xdHDb0/0.jpg)](https://www.youtube.com/watch?v=PI1X0xdHDb0)

---

## 🧩 Chatbot Intents

The chatbot uses **Semantic Routing** to understand what you're asking and routes it to the right handler:

| Intent | What it handles | Example |
|--------|----------------|---------|
| 🗂️ **FAQ** | Platform questions & policies | *"Does CashSwap charge any fees?"* |
| 🛍️ **SQL** | Finding nearby users for exchange | *"Find people with ₹1000 UPI near me"* |
| 🔄 **Radius Change** | Expanding the search area | *"Increase the search radius to 30 km"* |
| 💬 **Small Talk** | Casual conversation | *"Hi! How are you?"* |

---

## ✨ Features

- **Semantic Intent Routing** — Understands the meaning behind user queries, not just keywords
- **RAG-based FAQ** — Uses ChromaDB + Sentence Transformers to find the best FAQ answer
- **Natural Language to SQL** — Converts exchange requests into live database queries
- **Location-aware Search** — Finds users near you based on your location and search radius
- **LLaMA 3.1 via GROQ** — Fast, accurate LLM responses
- **Embedded in CashSwap UI** — Seamlessly integrated into the React frontend

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + Tailwind CSS |
| Backend | Node.js + Express |
| Chatbot API | Python + Flask + Gunicorn |
| LLM | LLaMA 3.1 (8B) via GROQ API |
| Intent Routing | Semantic Router |
| FAQ Retrieval | ChromaDB + Sentence Transformers |
| Database | SQLite (user matching) |
| Hosting | Vercel (frontend) + Render (backend + chatbot) |

---

## 🧠 How the Chatbot Works

```
User Message
     │
     ▼
┌──────────────────────┐
│   Semantic Router    │  ← Classifies user intent
└───┬──────┬──────┬────┘
    │      │      │      │
   FAQ    SQL  Radius  Small
          Query Change  Talk
    │      │      │      │
    ▼      ▼      ▼      ▼
ChromaDB SQLite Updated LLaMA
RAG      Query  Radius  Response
Search   Result
```

1. Every user message is passed through the **Semantic Router**
2. The router classifies it into: `faq`, `sql`, `radius_change`, or `small_talk`
3. Each route has its own handler that produces a tailored response
4. SQL queries hit the live SQLite database for real-time user matching

---

## 📂 Project Structure

```
CashSwap/
│
├── python-chatbot/                    # Chatbot backend (Flask API)
│   ├── app.py                         # Main Flask app & chat endpoint
│   ├── faq.py                         # FAQ handling via RAG (ChromaDB)
│   ├── sql.py                         # NL-to-SQL query handler
│   ├── smalltalk.py                   # Small talk responses via LLaMA
│   ├── router.py                      # Semantic intent router
│   ├── preload_model.py               # Model warm-up on server start
│   └── resources/
│       └── cashswap_chatbot_faq.csv   # FAQ dataset
│
├── backend/                           # Node.js backend (user/auth/data)
│   └── server.js
│
├── src/                               # React frontend
│   ├── components/
│   │   ├── ChatBot.jsx                # Chatbot UI component
│   │   └── ChatWindow.jsx             # Chat window UI
│   └── pages/
│       ├── HomePage.jsx
│       └── AboutPage.jsx
│
├── render.yaml                        # Render deployment config
├── index.html
└── README.md
```

---

## ⚙️ Local Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd CashSwap
```

### 2. Start the Chatbot API (Python)

```bash
cd python-chatbot
pip install -r requirements.txt
```

Create a `.env` file inside `python-chatbot/`:

```env
GROQ_API_KEY=<your_groq_api_key>
GROQ_MODEL=llama-3.1-8b-instant
```

```bash
python app.py
```

### 3. Start the Backend (Node.js)

```bash
cd backend
npm install
node server.js
```

### 4. Start the Frontend (React)

```bash
npm install
npm run dev
```

> 🔑 Get your GROQ API key at [console.groq.com](https://console.groq.com)

---

## 🚀 Deployment

This project is deployed using:

- **Vercel** → React frontend at [cashswapp.vercel.app](https://cashswapp.vercel.app/)
- **Render** → Python chatbot + Node.js backend (configured via `render.yaml`)

> ⚠️ Free-tier Render services spin down after inactivity. Always wake the servers before using the app (see Step 1 above).

---

<div align="center">
  Built with ❤️ for <strong>CashSwap</strong> — Swap cash, the smart way.
</div>
