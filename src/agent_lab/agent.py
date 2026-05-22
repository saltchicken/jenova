from typing import Literal

from google.adk import Agent
from google.adk import Event
from google.adk import Workflow
from google.adk.events import RequestInput
from google.adk.models.lite_llm import LiteLlm
from pydantic import BaseModel


class InputCategory(BaseModel):
    category: Literal["question", "statement", "other"]


def process_input(node_input: str):
    return Event(state={"input": node_input})


classify_input = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="classify_input",
    instruction=(
        "Based on this input, decide which category it belongs to: {input}"),
    output_schema=InputCategory,
    output_key="category",
)


def route_on_category(category: InputCategory):
    """Yields an Event with a specific route based on the classification."""
    yield Event(route=category.category)


def collect_info():
    yield RequestInput(message="Please provide your 6-digit account PIN:",
                       response_schema=int)


def process_account(node_input):
    return f"Processing account: {node_input}"


answer_question = Workflow(name="agent_lab",
                           edges=[('START', collect_info, process_account)])

comment_on_statement = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="comment_on_statement",
    instruction="""Comment on the statement: {input}""",
)


def handle_other():
    yield Event(
        message="Sorry I can only anwer questions or comment on statements.")


root_agent = Workflow(
    name="root_agent",
    edges=[
        ("START", process_input, classify_input, route_on_category),
        (
            route_on_category,
            {
                "question": answer_question,
                "statement": comment_on_statement,
                "other": handle_other,
            },
        ),
    ],
)
