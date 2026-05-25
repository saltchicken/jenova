"""
Domain-specific expert subagents.
"""

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm

from jenova.tools.search import restricted_web_search

# DEFAULT_MODEL = "ollama_chat/devstral-small-2"
DEFAULT_MODEL = "ollama_chat/gemma4:e4b"
llm_client = LiteLlm(model=DEFAULT_MODEL)

tech_expert = Agent(
    model=llm_client,
    name="_tech_expert",
    instruction=
    ("You are a senior software engineer. Answer the following technical question "
     "clearly and concisely: {input}\n\nHere is the conversation history:\n{history?}"
    ),
)

math_expert = Agent(
    model=llm_client,
    name="_math_expert",
    instruction=(
        "You are a mathematician. Solve or answer the following math question "
        "step-by-step: {input}\n\nHere is the conversation history:\n{history?}"
    ),
)

general_expert = Agent(
    model=llm_client,
    name="_general_expert",
    instruction=
    ("You are a helpful AI assistant. Answer the following general question: {input}\n\n"
     "If you need current information, facts, or news, use the restricted_web_search tool.\n"
     "IMPORTANT: Once you have gathered enough information from the search results, "
     "you MUST stop calling tools. Synthesize the results and reply directly to the user.\n\n"
     "Here is the conversation history:\n{history?}"),
    tools=[restricted_web_search],
)
