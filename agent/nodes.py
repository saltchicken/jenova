from typing import Literal

from google.adk import Agent
from google.adk import Event
from google.adk.models.lite_llm import LiteLlm
from pydantic import BaseModel

from agent.tools.lights import turn_off_lights
from agent.tools.lights import turn_on_lights


class IntentCategory(BaseModel):
    intent: Literal["action", "question", "other"]


classify_intent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="classify_intent",
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


def handle_other():
    yield Event(
        message=
        "I am an ai assistant. I can answer your questions or take actions for you."
    )
