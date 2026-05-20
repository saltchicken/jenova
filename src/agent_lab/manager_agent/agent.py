from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm

from agent_lab.dice_agent.agent import root_agent as dice_agent

# The framework natively registers this agent as a tool for the manager.
# You don't need a custom function wrapper!
root_agent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="manager_agent",
    description="A helpful coordinator that delegates dice and prime tasks.",
    instruction="""
    You are the primary manager agent. You coordinate requests for the user.
    If the user asks to roll a die or check primes, you must delegate the task to the dice_roll_agent.
    Do not try to roll dice or calculate primes yourself.
    """,
    # This automatically wires up the dice agent so the manager can call it like a tool,
    # while preserving conversation history and session state perfectly.
    sub_agents=[dice_agent], 
)
