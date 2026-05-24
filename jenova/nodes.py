"""
Defines the individual agents and nodes for the workflow.
"""

from typing import Literal

from google.adk import Agent
from google.adk import Event
from google.adk.models.lite_llm import LiteLlm
from pydantic import BaseModel

from jenova.tools.lights import turn_off_lights
from jenova.tools.lights import turn_on_lights


class IntentCategory(BaseModel):
    """Schema for categorizing user intent."""
    intent: Literal["action", "question", "other"]


classify_intent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="_classify_intent",
    instruction=
    ("You are a routing assistant. Based on the input, decide the intent: {input}\n"
     "- Choose 'action' if they requesting for you to take an action.\n"
     "- Choose 'question' if they are asking a question.\n"
     "- Choose 'other' for anything else."),
    output_schema=IntentCategory,
    output_key="intent",
)

take_action = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="take_action",
    instruction=
    "Figure out what the user wants you to do and take that action based on this input: {input}",
    tools=[turn_on_lights, turn_off_lights])

answer_question = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="answer_question",
    instruction=
    ("You are a helpful assistant. Here is the conversation history so far:\n"
     "{history?}\n\n"
     "Based on the history, please answer the latest user question clearly: {input}"
    ),
)


handle_other = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="handle_other",
    instruction=(
        "You are the Jenova AI assistant. The user just said something that isn't a direct question or action command.\n"
        "Here is the conversation history:\n"
        "{history?}\n\n"
        "Respond naturally to the user's input: {input}\n"
        "If it is a greeting or small talk, reply politely in kind. If their intent is unclear, gently remind them you can answer questions or control the lights.\n"
        "Talk to the user, don't include your thinking process\n"
    )
)
