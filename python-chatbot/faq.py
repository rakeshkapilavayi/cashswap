import os
import re
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_FAQ_PATH = Path(__file__).parent / "resources" / "cashswap_chatbot_faq.csv"
_faq_df: pd.DataFrame = pd.DataFrame()

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
    # Remove very common words that add no signal
    tokens -= {"the", "a", "an", "is", "it", "i", "my", "me", "to", "do", "can", "how", "what", "why"}
    if not tokens:
        return []
    scores = _faq_df["question"].apply(lambda q: _score(tokens, q))
    best_score = scores.max()
    # Only return results if there's at least 1 keyword match
    if best_score == 0:
        return []
    top_idx = scores.nlargest(n).index
    return _faq_df.loc[top_idx, "answer"].tolist()


def faq_chain(query):
    answers = get_relevant_faqs(query)

    if answers:
        context = " ".join(answers)
        prompt = (
            "You are a helpful CashSwap assistant. Answer the question using the context provided. "
            "If the context doesn't fully answer it, use your general knowledge about CashSwap "
            "(a peer-to-peer cash/UPI exchange platform) to help. Be friendly and concise.\n\n"
            f"QUESTION: {query}\nCONTEXT: {context}"
        )
    else:
        # No FAQ match — use Groq as a general CashSwap assistant
        prompt = (
            "You are a helpful assistant for CashSwap, a peer-to-peer platform where users swap "
            "physical cash for UPI digital money and vice versa. "
            "Answer the following question helpfully and concisely. "
            "If it's completely unrelated to CashSwap, politely redirect to CashSwap topics.\n\n"
            f"QUESTION: {query}"
        )

    resp = _get_client().chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    ingest_faq_data()
    print(faq_chain("What is CashSwap?"))
    print(faq_chain("what is this website"))
