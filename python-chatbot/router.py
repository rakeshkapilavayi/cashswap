import re


_GREETING_RE = re.compile(
    r"""
    ^[\s!]*                         # optional leading whitespace/punctuation
    (
        h[aei]+[iy]*                # hi, hii, hai, haii, haiiii, hey, heyy
      | h[e]+llo+                   # hello, helloo
      | h[ae]y+                     # hey, heyy, hay
      | sup+                        # sup, supp
      | yo+                         # yo, yoo
      | namaste                     # namaste
      | good\s*(morning|afternoon|evening|night)
      | greetings?
      | howdy
      | what['\s]*s\s*up           # what's up / whats up
      | how\s+are\s+you
      | how\s+r\s+u
    )
    [\s!?.,]*$                      # optional trailing punctuation
    """,
    re.IGNORECASE | re.VERBOSE
)

_FAREWELL_RE = re.compile(
    r"^[\s!]*(bye+|goodbye|see\s+you|later|cya|take\s+care|thanks?|thank\s+you|ty|thx)[\s!.?]*$",
    re.IGNORECASE
)

_SMALLTALK_PHRASES = [
    "what is your name", "what's your name", "who are you", "what are you",
    "are you a bot", "are you a robot", "are you human", "are you ai",
    "nice to meet", "how are you", "how r u", "how do you do",
    "you there", "anyone there",
]

_SQL_KEYWORDS = [
    "exchange", "find people", "find users", "find someone", "near me",
    "nearby", "cash", "upi", "rupees", "rs.", "₹", "amount", "balance",
    "who has", "show me users", "show users", "list users", "people with",
    "someone who", "anyone with", "convert", "swap", "wallet",
    "kilometer", "radius", "within", "distance", "money",
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
]

_FAQ_KEYWORDS = [
    "what is cashswap", "how does cashswap", "how does it work", "how it works",
    "is it safe", "safe to exchange", "fee", "fees", "charge", "cancel",
    "report", "block", "trust", "verify", "password", "account", "delete",
    "dark mode", "light mode", "theme", "about", "contact", "support",
    "security", "data", "privacy", "terms", "conditions", "chatbot",
    "what can i do", "how do i", "why is my", "what should i do",
    "what is this", "what is this website", "what is this app",
    "what does", "what can",
]



class _Route:
    def __init__(self, name: str):
        self.name = name



def router(query: str) -> _Route:
    q = query.strip()
    ql = q.lower()

    # 1. Pure greeting (regex — catches haii, haiiii, heyy, etc.)
    if _GREETING_RE.match(q):
        return _Route("small_talk")

    # 2. Pure farewell / thanks
    if _FAREWELL_RE.match(q):
        return _Route("small_talk")

    # 3. Small talk phrases
    for phrase in _SMALLTALK_PHRASES:
        if phrase in ql:
            return _Route("small_talk")

    # 4. Radius change
    for kw in _RADIUS_KEYWORDS:
        if kw in ql:
            return _Route("radius_change")
    for pat in _RADIUS_PATTERNS:
        if re.search(pat, ql):
            if not re.search(r"\d+\s*(rupees?|rs\.?|₹)", ql):
                return _Route("radius_change")

    # 5. SQL / money exchange
    for kw in _SQL_KEYWORDS:
        if kw in ql:
            return _Route("sql")

    # 6. FAQ
    for kw in _FAQ_KEYWORDS:
        if kw in ql:
            return _Route("faq")

    # 7. Very short messages (≤3 words) that didn't match anything → small_talk
    if len(ql.split()) <= 3:
        return _Route("small_talk")

    # 8. Fallback → faq (Groq will handle it)
    return _Route("faq")


# Alias for backwards compatibility
def get_router():
    return router


# ── self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        ("Haii", "small_talk"),
        ("Haiiii", "small_talk"),
        ("hi", "small_talk"),
        ("Hey!", "small_talk"),
        ("heyyyy", "small_talk"),
        ("Hello", "small_talk"),
        ("Good morning", "small_talk"),
        ("How are you", "small_talk"),
        ("Thanks", "small_talk"),
        ("bye", "small_talk"),
        ("What is CashSwap?", "faq"),
        ("what is this website", "faq"),
        ("How does it work?", "faq"),
        ("Find people near me who have cash", "sql"),
        ("I want to exchange 500 rupees UPI to cash", "sql"),
        ("i need to exchange money", "sql"),
        ("Increase the radius to 30 km", "radius_change"),
        ("show more in 25 km", "radius_change"),
        ("Is it safe to exchange money?", "faq"),
    ]
    print("Router self-test:")
    all_pass = True
    for query, expected in tests:
        result = router(query).name
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_pass = False
        print(f"  {status}  [{result:13s}] expected=[{expected:13s}]  {query}")
    print("\n✅ All tests passed!" if all_pass else "\n❌ Some tests failed.")
