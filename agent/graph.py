from google.adk import Event, Workflow, Context

from agent.nodes import (
    IntentCategory,
    classify_intent,
    take_action,
    answer_question,
    handle_other,
)

def process_input(node_input: str, ctx: Context):
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
