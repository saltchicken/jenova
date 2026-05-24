"""
Defines the main agent workflow graph and routing logic.
"""

from typing import Generator

from google.adk import Context
from google.adk import Event
from google.adk import Workflow

from jenova.nodes import answer_question
from jenova.nodes import classify_intent
from jenova.nodes import handle_other
from jenova.nodes import IntentCategory
from jenova.nodes import take_action
from jenova.utils import get_full_history


def process_input(node_input: str, ctx: Context) -> Event:
    """Processes the input string and updates the conversation history."""
    history = get_full_history(ctx)

    return Event(state={"input": node_input, "history": history})


def route_on_intent(intent: IntentCategory) -> Generator[Event, None, None]:
    """Yields an Event with a specific route based on the classification."""
    yield Event(route=intent.intent)


root_agent = Workflow(
    name="jenova",
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
