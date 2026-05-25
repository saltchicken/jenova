"""
Domain-specific expert subagents.
"""

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm

# DEFAULT_MODEL = "ollama_chat/devstral-small-2"
DEFAULT_MODEL = "ollama_chat/gemma4:e4b"
llm_client = LiteLlm(model=DEFAULT_MODEL)

from jenova.tools import search_duckduckgo
from jenova.tools import scrape_website


search_agent = Agent(
    model=llm_client,
    name="search_agent",
    instruction=(
        "You are an autonomous research compiler working in a machine-to-machine pipeline. \n"
        "The current date and time is {current_date}.\n\n"
        "The user's input: {input}\n\n"
        "Your workflow:\n"
        "1. Determine the proper research query from the user's input.\n"
        "2. Use the `search_duckduckgo` tool to find the most relevant sources.\n"
        "3. Use the `scrape_website` tool to extract the raw text from the most promising URLs.\n"
        "4. Synthesize the findings into a strict JSON payload.\n\n"
        "You must output ONLY valid JSON. Do not include markdown code blocks or conversational text.\n"
        "Your JSON must follow this exact schema:\n"
        "{\n"
        "  \"topic\": \"The exact topic researched\",\n"
        "  \"executive_summary\": \"A dense, high-level summary of the findings\",\n"
        "  \"key_data_points\": [\"fact 1\", \"fact 2\", \"fact 3\"],\n"
        "  \"sources_used\": [\"url1\", \"url2\"]\n"
        "}"
    ),
    tools=[search_duckduckgo, scrape_website],
)


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
     "System Context:\n{user_context}\n"
     "The current date and time is {current_date}.\n\n"
     "Answer the following general question: {input}\n\n"
     "Here is the conversation history:\n{history?}"),
)
