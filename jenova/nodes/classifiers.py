"""
Routing logic and Pydantic schemas.
"""

from typing import Literal

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from pydantic import BaseModel

# DEFAULT_MODEL = "ollama_chat/devstral-small-2"
DEFAULT_MODEL = "ollama_chat/gemma4:e4b"
llm_client = LiteLlm(model=DEFAULT_MODEL)


class IntentCategory(BaseModel):
    """Schema for categorizing user intent."""
    intent: Literal["action", "question", "other"]


class QuestionCategory(BaseModel):
    """Schema for categorizing the type of question."""
    category: Literal["tech", "math", "general"]


classify_intent = Agent(
    model=llm_client,
    name="_classify_intent",
    instruction=
    ("You are a routing assistant. Based on the input, decide the intent: {input}\n"
     "- Choose 'action' if they requesting for you to take an action.\n"
     "- Choose 'question' if they are asking a question.\n"
     "- Choose 'other' for anything else.\n"
     "CRITICAL: You MUST respond with ONLY a valid JSON object containing a single key 'intent'. "
     "Example: {\"intent\": \"action\"}"),
    output_schema=IntentCategory,
    output_key="intent",
)

classify_question = Agent(
    model=llm_client,
    name="_classify_question",
    instruction=
    ("You are a sub-routing assistant. Categorize the user's question: {input}\n"
     "- Choose 'tech' if it's about programming, software, or operating systems.\n"
     "- Choose 'math' if it involves calculations or mathematical concepts.\n"
     "- Choose 'general' for anything else.\n"
     "CRITICAL: You MUST respond with ONLY a valid JSON object. Example: {\"category\": \"tech\"}"
    ),
    output_schema=QuestionCategory,
    output_key="category",
)
