"""
Defines the main agent workflow graph and routing logic.
"""

from google.adk import Context
from google.adk import Event
from google.adk import Workflow

from agent.nodes import answer_question
from agent.nodes import classify_intent
from agent.nodes import handle_other
from agent.nodes import IntentCategory
from agent.nodes import take_action


def process_input(node_input: str, ctx: Context):
    """Processes the input string and updates the conversation history."""
    history = ctx.state.get("history", [])

    history.append({"role": "user", "content": node_input})

    return Event(state={"input": node_input, "history": history})


def route_on_intent(intent: IntentCategory):
    """Yields an Event with a specific route based on the classification."""
    yield Event(route=intent.intent)


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
