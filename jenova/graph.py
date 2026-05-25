"""
Defines the main agent workflow graph and routing logic.
"""

from datetime import datetime
from typing import Generator

from google.adk import Context
from google.adk import Event
from google.adk import Workflow

from jenova.nodes import classify_intent
from jenova.nodes import classify_question
from jenova.nodes import general_expert
from jenova.nodes import handle_other
from jenova.nodes import IntentCategory
from jenova.nodes import math_expert
from jenova.nodes import QuestionCategory
from jenova.nodes import search_agent
from jenova.nodes import take_action
from jenova.nodes import tech_expert
from jenova.nodes import tts_formatter
from jenova.utils import get_full_history
from jenova.memory import load_memories


def process_input(node_input: str, ctx: Context) -> Event:
    """Processes the input string and updates the conversation history."""
    history = get_full_history(ctx)
    
    # Generate dynamic context
    current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
    
    # Load all saved memories
    saved_facts = load_memories()
    
    # Format them into a readable string for the LLM
    if saved_facts:
        user_context = "Here are known facts about the user:\n- " + "\n- ".join(saved_facts)
    else:
        user_context = "No personal facts are known about the user yet."

    return Event(state={
        "input": node_input, 
        "history": history,
        "current_date": current_date,
        "user_context": user_context
    })


def route_on_intent(intent: IntentCategory) -> Generator[Event, None, None]:
    """Yields an Event with a specific route based on the classification."""
    yield Event(route=intent.intent)


def route_on_question_type(
        category: QuestionCategory) -> Generator[Event, None, None]:
    """Yields an Event routing to a specific expert based on the question category."""
    yield Event(route=category.category)


root_agent = Workflow(
    name="jenova",
    edges=[
        ("START", process_input, classify_intent, route_on_intent),
        (
            route_on_intent,
            {
                "action": take_action,
                "question":
                    classify_question,  # Routes to sub-classifier instead of answering directly
                "other": handle_other,
            },
        ),
        # New Sub-Routing Layer
        (classify_question, route_on_question_type),
        (
            route_on_question_type,
            {
                "tech": tech_expert,
                "math": math_expert,
                "general": general_expert,
                "search": search_agent,
            },
        ),
        (take_action, tts_formatter),
        (handle_other, tts_formatter),
        (tech_expert, tts_formatter),
        (math_expert, tts_formatter),
        (general_expert, tts_formatter),
        (search_agent, tts_formatter),
    ],
)
