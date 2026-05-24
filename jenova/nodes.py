"""
Defines the individual agents and nodes for the workflow.
"""

from typing import Literal

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from pydantic import BaseModel

from jenova.tools.lights import turn_off_lights
from jenova.tools.lights import turn_on_lights

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

take_action = Agent(
    model=llm_client,
    name="take_action",
    instruction=
    ("Figure out what the user wants you to do and take that action based on this input: {input}\n"
     "IMPORTANT: Once the tool has been executed and you receive the result, you MUST stop calling tools. "
     "Reply directly to the user with a natural, conversational message confirming the action was completed."
    ),
    tools=[turn_on_lights, turn_off_lights])

classify_question = Agent(
    model=llm_client,
    name="_classify_question",
    instruction=(
        "You are a sub-routing assistant. Categorize the user's question: {input}\n"
        "- Choose 'tech' if it's about programming, software, or operating systems.\n"
        "- Choose 'math' if it involves calculations or mathematical concepts.\n"
        "- Choose 'general' for anything else.\n"
        "CRITICAL: You MUST respond with ONLY a valid JSON object. Example: {\"category\": \"tech\"}"
    ),
    output_schema=QuestionCategory,
    output_key="category",
)

tech_expert = Agent(
    model=llm_client,
    name="tech_expert",
    instruction=(
        "You are a senior software engineer. Answer the following technical question "
        "clearly and concisely: {input}\n\nHere is the conversation history:\n{history?}"
    ),
)

math_expert = Agent(
    model=llm_client,
    name="math_expert",
    instruction=(
        "You are a mathematician. Solve or answer the following math question "
        "step-by-step: {input}\n\nHere is the conversation history:\n{history?}"
    ),
)

general_expert = Agent(
    model=llm_client,
    name="general_expert",
    instruction=(
        "You are a helpful AI assistant. Answer the following general question: {input}\n\n"
        "Here is the conversation history:\n{history?}"
    ),
)

handle_other = Agent(
    model=llm_client,
    name="handle_other",
    instruction=
    ("You are the Jenova AI assistant. The user just said something that isn't a direct question or action command.\n"
     "Here is the conversation history:\n"
     "{history?}\n\n"
     "Respond naturally to the user's input: {input}\n"
     "If it is a greeting or small talk, reply politely in kind. If their intent is unclear, gently remind them you can answer questions or control the lights.\n"
     "Talk to the user, don't include your thinking process\n"))
