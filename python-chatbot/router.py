"""
Lightweight keyword-based router — replaces semantic-router + HuggingFaceEncoder.
No local ML model loaded, so memory stays well under Render's 512 MB free tier.
"""

import re


# ── keyword lists ────────────────────────────────────────────────────────────

_SQL_KEYWORDS = [
    "exchange", "find people", "find users", "find someone", "near me",
    "nearby", "cash", "upi", "rupees", "rs.", "₹", "amount", "balance",
    "who has", "show me users", "show users", "list users", "people with",
    "someone who", "anyone with", "convert", "swap", "wallet", "km",
    "kilometer", "radius", "within", "distance",
]

_RADIUS_KEYWORDS = [
    "increase radius", "expand radius", "expand search", "wider search",
    "increase distance", "more users", "more people", "more results",
    "larger area", "further away", "search in", "look further",
    "extend search",
]

_RADIUS_PATTERNS = [
    r"\d+\s*km",
    r"\d+\s*kms?",
    r"\d+\s*kilometers?",
    r"\d+\s*kilometres?",
    r"in\s+\d+",
    r"within\s+\d+",
]

_SMALLTALK_KEYWORDS = [
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "how are you", "what's up", "whats up", "nice to meet", "bye", "goodbye",
    "see you", "thanks", "thank you", "what is your name", "who are you",
    "what are you", "are you a bot", "are you a robot",
]

_FAQ_KEYWORDS = [
    "what is cashswap", "how does cashswap", "how does it work", "how it works",
    "is it safe", "safe to exchange", "fee", "fees", "charge", "cancel",
    "report", "block", "trust", "verify", "password", "account", "delete",
    "dark mode", "light mode", "theme", "about", "contact", "support",
    "security", "data", "privacy", "terms", "conditions", "chatbot",
    "what can i do", "how do i", "why is my", "what should i do",
]


# ── simple route object (duck-types semantic_router's RouteChoice) ───────────

class _Route:
    def __init__(self, name: str):
        self.name = name


# ── routing logic ─────────────────────────────────────────────────────────────

def router(query: str) -> _Route:
    """
    Return a _Route whose .name is one of:
        'sql' | 'radius_change' | 'faq' | 'small_talk'
    """
    q = query.lower().strip()

    # 1. radius_change: explicit radius keywords OR a bare number + distance word
    for kw in _RADIUS_KEYWORDS:
        if kw in q:
            return _Route("radius_change")
    for pat in _RADIUS_PATTERNS:
        if re.search(pat, q):
            # Make sure it's not just a money amount like "500 rupees"
            if not re.search(r"\d+\s*(rupees?|rs\.?|₹)", q):
                return _Route("radius_change")

    # 2. small_talk: greetings / farewells first (short messages)
    for kw in _SMALLTALK_KEYWORDS:
        if kw in q:
            return _Route("small_talk")

    # 3. sql: money/exchange/user-search intent
    for kw in _SQL_KEYWORDS:
        if kw in q:
            return _Route("sql")

    # 4. faq: product / how-to questions
    for kw in _FAQ_KEYWORDS:
        if kw in q:
            return _Route("faq")

    # 5. fallback — treat unknown questions as FAQ so Groq can attempt an answer
    return _Route("faq")


# Alias so app.py works whether it does:
#   from router import router   (original)
#   from router import get_router  (alternate style)
def get_router():
    """Returns the router callable. Use router() directly instead if possible."""
    return router


# ── quick self-test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        ("How does CashSwap work?", "faq"),
        ("Find people near me who have cash", "sql"),
        ("I want to exchange 500 rupees UPI to cash", "sql"),
        ("Increase the radius to 30 km", "radius_change"),
        ("Show more users in 25 km", "radius_change"),
        ("Hi there!", "small_talk"),
        ("Thanks for your help", "small_talk"),
        ("Is it safe to exchange money?", "faq"),
    ]
    print("Router self-test:")
    for query, expected in tests:
        result = router(query).name
        status = "✅" if result == expected else "❌"
        print(f"  {status}  [{result:13s}]  {query}")
