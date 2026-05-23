from typing import Literal

from google.adk import Agent
from google.adk import Event
from google.adk import Workflow
from google.adk.models.lite_llm import LiteLlm
from pydantic import BaseModel


# 1. Categories updated to match realistic user intents
class IntentCategory(BaseModel):
    intent: Literal["action", "question", "other"]


def process_input(node_input: str):
    return Event(state={"input": node_input})


# 2. Classifier prompt updated to explain HOW to categorize
classify_intent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="classify_intent",
    instruction=(
        "You are a routing assistant. Based on the input, decide the intent: {input}\n"
        "- Choose 'action' if they requesting for you to take an action.\n"
        "- Choose 'question' if they are asking a question.\n"
        "- Choose 'other' for anything else."
    ),
    output_schema=IntentCategory,
    output_key="intent",
)


def route_on_intent(intent: IntentCategory):
    """Yields an Event with a specific route based on the classification."""
    yield Event(route=intent.intent)


def turn_on_lights(room: str) -> str:
    """
    Turns on lights in the specified room.
    """
    print(f"\n[Tool Execution] Turning on {room} lights...")
    return f"The {room} lights are now on."

def turn_off_lights(room: str) -> str:
    """
    Turns off lights in the specified room.
    """
    print(f"\n[Tool Execution] Turning off {room} lights...")
    return f"The {room} lights are now off."

take_action = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="take_action",
    instruction="Figure out what the user wants you to do and take that action based on this input: {input}",
    tools=[turn_on_lights, turn_off_lights]
)

# 4. A dedicated agent for answering actual questions
answer_question = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="answer_question",
    instruction="Please answer the following user question clearly and concisely: {input}",
)


def handle_other():
    yield Event(
        message="I am a customer support bot. I can help you manage your account or answer general questions."
    )


# 5. The root workflow routes intents to their logical destinations
root_agent = Workflow(
    name="ai_assistant",
    edges=[
        ("START", process_input, classify_intent, route_on_intent),
        (
            route_on_intent,
            {
                "action": take_action,
                "question": answer_question,
                "other": handle_other,
            },
        ),
    ],
)
