# src/tools/nlu_tool.py ✅

from pydantic import BaseModel
from typing import Literal
from agents import function_tool

class NLUInput(BaseModel):
    message: str

class NLUOutput(BaseModel):
    intent: str
    sentiment: Literal["positive", "negative", "neutral", "angry", "frustrated", "happy"]


def analyze_nlu(data: NLUInput) -> NLUOutput:
    """
    Analyze the given text message and detect its intent and sentiment.

    Supported intents are:
        - buy_product
        - raise_complaint
        - greet
        - support_request
        - ask_price
        - track_order
        - asked_about_product
        - unknown


    Supported sentiments are:
        - positive
        - negative
        - neutral
        - angry
        - frustrated
        - happy
    """
    message = data.message.lower()

    # Determine intent
    if any(word in message for word in ["buy", "purchase", "place an order"]):
        intent = "buy_product"
    elif any(word in message for word in ["complaint", "issue", "problem", "not working", "defect"]):
        intent = "raise_complaint"
    elif any(word in message for word in ["hello", "hi", "hey"]):
        intent = "greet"
    elif any(word in message for word in ["help", "support", "assistance"]):
        intent = "support_request"
    elif any(word in message for word in ["price", "cost", "quote", "how much"]):
        intent = "ask_price"
    elif any(word in message for word in ["shipped", "delivery", "delivered", "track", "tracking", "quote id"]):
        intent = "track_order"
    elif any(word in message for word in ["Product","inventory"]):
        intent = "asked_about_product"
    else:
        intent = "unknown"

    # Determine sentiment
    if any(word in message for word in ["angry", "furious", "mad", "frustrated"]):
        sentiment = "angry"
    elif any(word in message for word in ["happy", "glad", "thank", "awesome"]):
        sentiment = "happy"
    elif any(word in message for word in ["hate", "bad", "worst", "terrible"]):
        sentiment = "negative"
    elif any(word in message for word in ["great", "love", "excellent", "nice"]):
        sentiment = "positive"
    else:
        sentiment = "neutral"

    return NLUOutput(intent=intent, sentiment=sentiment)

get_all_nlu_tool = function_tool(
    analyze_nlu,
    )