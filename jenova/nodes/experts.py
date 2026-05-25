"""
Domain-specific expert subagents.
"""

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm

import uuid, httpx, json

# DEFAULT_MODEL = "ollama_chat/devstral-small-2"
DEFAULT_MODEL = "ollama_chat/gemma4:e4b"
llm_client = LiteLlm(model=DEFAULT_MODEL)

from jenova.tools import ask_search_agent


tech_expert = Agent(
    model=llm_client,
    name="_tech_expert",
    instruction=
    ("You are a senior software engineer.\n"
     "System Context: The current date and time is {current_date}.\n\n"
     "Answer the following technical question "
     "clearly and concisely: {input}\n\nHere is the conversation history:\n{history?}"
    ),
)

math_expert = Agent(
    model=llm_client,
    name="_math_expert",
    instruction=(
        "You are a mathematician.\n"
        "System Context: The current date and time is {current_date}.\n\n"
        "Solve or answer the following math question "
        "step-by-step: {input}\n\nHere is the conversation history:\n{history?}"
    ),
)

general_expert = Agent(
    model=llm_client,
    name="_general_expert",
    instruction=
    ("You are a helpful AI assistant.\n"
     "System Context: The current date and time is {current_date}.\n\n"
     "Answer the following general question: {input}\n\n"
     "If you need current information, facts, or news, use the ask_search_agent tool.\n"
     "CRITICAL SEARCH RULES:\n"
     "1. Break complex questions into concise, keyword-heavy search queries.\n"
     "2. Do not use full sentences for search queries. (e.g., Use 'France capital population current' instead of 'What is the population of France').\n\n"
     "IMPORTANT: Once you have gathered enough information from the search results, "
     "you MUST stop calling tools. Synthesize the results and reply directly to the user.\n\n"
     "Here is the conversation history:\n{history?}"),
    tools=[ask_search_agent],
)
