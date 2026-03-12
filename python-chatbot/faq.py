"""
Lightweight FAQ handler.
Uses keyword search over CSV + Groq for answer generation.
No chromadb or sentence-transformers — keeps memory well under 512 MB.
"""
import os
import re
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_FAQ_PATH = Path(__file__).parent / "resources" / "cashswap_chatbot_faq.csv"
_faq_df: pd.DataFrame = pd.DataFrame()

# Lazy Groq client — NOT initialized at module level (avoids --preload crash)
_groq_client = None

def _get_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client


def ingest_faq_data(path=None):
    global _faq_df
    p = Path(path) if path else _FAQ_PATH
    _faq_df = pd.read_csv(p)
    print(f"✅ Loaded {len(_faq_df)} FAQ entries")


def _score(query_tokens, text):
    text_lower = text.lower()
    return sum(1 for tok in query_tokens if tok in text_lower)


def get_relevant_faqs(query, n=2):
    if _faq_df.empty:
        ingest_faq_data()
    tokens = set(re.findall(r"\w+", query.lower()))
    scores = _faq_df["question"].apply(lambda q: _score(tokens, q))
    top_idx = scores.nlargest(n).index
    return _faq_df.loc[top_idx, "answer"].tolist()


def faq_chain(query):
    answers = get_relevant_faqs(query)
    context = " ".join(answers)
    prompt = (
        "Given the question and context below, answer based only on the context. "
        "If the answer isn't in the context, say \"I don't know\".\n\n"
        f"QUESTION: {query}\nCONTEXT: {context}"
    )
    resp = _get_client().chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    ingest_faq_data()
    print(faq_chain("What is CashSwap?"))
