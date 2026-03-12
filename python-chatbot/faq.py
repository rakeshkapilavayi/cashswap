import os
import re
import pandas as pd
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Load FAQ CSV once at import time ─────────────────────────────────────────
_FAQ_PATH = Path(__file__).parent / "resources" / "cashswap_chatbot_faq.csv"
_faq_df: pd.DataFrame = pd.DataFrame()


def ingest_faq_data(path: Path | str | None = None):
    """Load the FAQ CSV into memory (called once on startup)."""
    global _faq_df
    p = Path(path) if path else _FAQ_PATH
    _faq_df = pd.read_csv(p)
    print(f"✅ Loaded {len(_faq_df)} FAQ entries from {p.name}")


# ── Simple keyword-based retrieval (no vector DB needed) ─────────────────────

def _score(query_tokens: set[str], text: str) -> int:
    """Count how many query words appear in text (case-insensitive)."""
    text_lower = text.lower()
    return sum(1 for tok in query_tokens if tok in text_lower)


def get_relevant_faqs(query: str, n: int = 2) -> list[str]:
    """Return the top-n FAQ answers most relevant to the query."""
    if _faq_df.empty:
        ingest_faq_data()

    tokens = set(re.findall(r"\w+", query.lower()))
    scores = _faq_df["question"].apply(lambda q: _score(tokens, q))
    top = _faq_df.nlargest(n, scores.name if hasattr(scores, "name") else 0)

    # nlargest on a Series — use index trick
    top_idx = scores.nlargest(n).index
    answers = _faq_df.loc[top_idx, "answer"].tolist()
    return answers


# ── Groq answer generation ────────────────────────────────────────────────────

def _generate_answer(query: str, context: str) -> str:
    groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = (
        "Given the question and context below, answer based only on the context. "
        "If the answer isn't in the context, say \"I don't know\".\n\n"
        f"QUESTION: {query}\n"
        f"CONTEXT: {context}"
    )
    resp = groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
    )
    return resp.choices[0].message.content


def faq_chain(query: str) -> str:
    answers = get_relevant_faqs(query)
    context = " ".join(answers)
    return _generate_answer(query, context)


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ingest_faq_data()
    print(faq_chain("What is CashSwap?"))
