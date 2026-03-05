from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

# FAQ Route
faq = Route(
    name='faq',
    utterances=[
        "What is CashSwap?",
        "what can i do with CashSwap?",
        "How does CashSwap work?",
        "How it works?",
        "Is the money exchange safe?",
        "What is the process to exchange money?",
        "How do I verify the other person?",
        "What are the terms and conditions?",
        "Is there any fee for using CashSwap?",
        "How can I trust the person exchanging money?",
        "What should I do if there's a problem with exchange?",
        "How do I report a fraudulent user?",
        "Can I cancel an exchange request?",
        "What are the payment security measures?",
    ],
    score_threshold=0.2
)

# SQL Route
sql = Route(
    name='sql',
    utterances=[
        "i need to exchange 400 cash to upi",
        "Find people near me who can exchange money",
        "Is there anyone with cash available?",
        "Show me users who have UPI",
        "Find people with at least 500 rupees cash",
        "Who can exchange 1000 rupees nearby?",
        "Are there people with cash within 5 km?",
        "Show me users with UPI amount above 2000",
        "Find someone who can give me cash for UPI",
        "Is there anyone near me with money to exchange?",
        "Show people who have both cash and UPI",
        "Find users within 10 km with cash",
        "Who has the most cash available?",
        "List all users with money near my location",
        "Find people who can exchange 300 rupees",
        "Show me nearby users with at least 100 rupees",
    ],
    score_threshold=0.2
)

# Radius Change Route
radius_change = Route(
    name='radius_change',
    utterances=[
        "increase the radius",
        "expand the search radius",
        "show more users",
        "show more people",
        "increase search area",
        "show users in 25 km",
        "show more users in 30 km",
        "find people within 40 km",
        "search within 50 km",
        "expand to 20 km",
        "wider search",
        "increase distance",
        "show results in larger area",
        "more results please",
        "find more nearby users",
        "search in 25 kilometer radius",
        "look further away",
        "extend search to 30 km",
    ],
    score_threshold=0.2
)

# Small Talk Route
small_talk = Route(
    name='small_talk',
    utterances=[
        "How are you?",
        "What is your name?",
        "Are you a robot?",
        "Hi",
        "Hello",
        "Hey there",
        "Good morning",
        "What are you?",
        "What do you do?",
        "Nice to meet you",
        "How's it going?",
        "What's up?",
        "Thanks",
        "Thank you for your help!",
        "Bye",
        "Goodbye",
        "See you later",
    ],
    score_threshold=0.2
)

# Lazy-loaded router - only loads the heavy model on first request
_router_instance = None

def get_router():
    global _router_instance
    if _router_instance is None:
        encoder = HuggingFaceEncoder(
            name="sentence-transformers/all-MiniLM-L6-v2"
        )
        _router_instance = SemanticRouter(
            routes=[faq, sql, small_talk, radius_change],
            encoder=encoder,
            auto_sync="local"
        )
    return _router_instance
