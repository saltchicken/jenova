"""
Defines the main agent workflow graph and routing logic.
"""

import pathlib
from datetime import datetime
from typing import Any

from google.adk import Agent
from google.adk import Context
from google.adk import Event
from google.adk import Workflow
from google.adk.models.lite_llm import LiteLlm

# ADK Skill Modules
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset
from google.adk.code_executors.unsafe_local_code_executor import UnsafeLocalCodeExecutor

from jenova.utils import create_adk_tool
from jenova.utils import discover_adk_agents
from jenova.utils import get_full_history


def process_input(node_input: str, ctx: Context) -> Event:
    """Processes the input string and provides context to the orchestrator."""
    history = get_full_history(ctx)
    current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")

    return Event(state={
        "input": node_input,
        "history": history,
        "system_information": current_date
    })


DEFAULT_MODEL = "ollama_chat/gemma4:e4b"
llm_client = LiteLlm(model=DEFAULT_MODEL)

# 1. Discover your A2A agents
discovered_cards = discover_adk_agents()
dynamic_tools: list[Any] = [create_adk_tool(card) for card in discovered_cards]

# 2. Load your directory-based Skill from the filesystem (using kebab-case)
system_diagnostics_skill = load_skill_from_dir(
    pathlib.Path(__file__).parent / "skills" / "system-diagnostics"
)

# TODO: Remove this. Was just a test
def get_wind_speed(location: str) -> str:
  """Returns the current wind speed for a given location."""
  return f"The wind speed in {location} is 10 mph."


# 3. Combine the local Skill, the dynamic A2A tools, and the code executor
orchestrator_toolset = skill_toolset.SkillToolset(
    skills=[system_diagnostics_skill],
    code_executor=UnsafeLocalCodeExecutor(),
)


orchestrator = Agent(
    model=llm_client,
    name="orchestrator",
    instruction=(
        "You are the central orchestrator agent for the Jenova system. "
        "Your job is to analyze the user's request and delegate it to the appropriate "
        "specialized A2A agent to fulfill the request. \n\n"
        "System Information: {system_information}\n"
        "User Request: {input}\n"
        "Conversation History: {history?}\n\n"
        "Review your available tools and call the best expert. "
        "CRITICAL: Once you have successfully retrieved the information from a tool, "
        "you MUST stop calling tools immediately and output the final answer to the user."
    ),
    tools=[orchestrator_toolset, get_wind_speed] + dynamic_tools
)

root_agent = Workflow(
    name="jenova",
    edges=[
        ("START", process_input, orchestrator),
    ],
)
