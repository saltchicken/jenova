from typing import Literal

from google.adk import Agent
from google.adk import Event
from google.adk import Workflow
from google.adk.events import RequestInput
from google.adk.models.lite_llm import LiteLlm
from pydantic import BaseModel


# 1. Categories updated to match realistic user intents
class IntentCategory(BaseModel):
    intent: Literal["account_action", "general_question", "other"]


def process_input(node_input: str):
    return Event(state={"input": node_input})


# 2. Classifier prompt updated to explain HOW to categorize
classify_intent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="classify_intent",
    instruction=(
        "You are a routing assistant. Based on the input, decide the intent: {input}\n"
        "- Choose 'account_action' if they want to manage their account or check a balance.\n"
        "- Choose 'general_question' if they are asking for general information.\n"
        "- Choose 'other' for anything else."
    ),
    output_schema=IntentCategory,
    output_key="intent",
)


def route_on_intent(intent: IntentCategory):
    """Yields an Event with a specific route based on the classification."""
    yield Event(route=intent.intent)


# 3. Account workflow makes sense here (requires auth/PIN)
def collect_pin():
    yield RequestInput(
        message="I can help with your account. Please provide your 6-digit account PIN:",
        response_schema=int
    )


def process_account(node_input: int):
    # node_input automatically captures the response from collect_pin
    return f"Successfully authenticated with PIN: {node_input}. Retrieving account details..."


account_workflow = Workflow(
    name="account_management",
    edges=[('START', collect_pin, process_account)]
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
    name="customer_support_router",
    edges=[
        ("START", process_input, classify_intent, route_on_intent),
        (
            route_on_intent,
            {
                "account_action": account_workflow,
                "general_question": answer_question,
                "other": handle_other,
            },
        ),
    ],
)
