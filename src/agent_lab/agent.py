from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm

from agent_lab.sub_agents.dice.agent import agent as dice_agent
from agent_lab.sub_agents.calculator.agent import agent as calculator_agent
from agent_lab.sub_agents.coder.agent import agent as coder_agent

# The framework natively registers this agent as a tool for the manager.
# You don't need a custom function wrapper!
root_agent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="manager_agent",
    description="A helpful coordinator that delegates tasks to sub-agents.",
    instruction="""
    You are the primary manager agent. You coordinate requests for the user.
    If the user asks to roll a die or check primes, you must delegate the task to the dice_roll_agent.
    If the user asks for math operations like addition or multiplication, delegate to the calculator_agent.
    If the user asks to write, review, or refactor code, you must delegate to the coder_agent.
    Do not try to roll dice, calculate primes, perform math, or write code yourself.
    """,
    # This automatically wires up the sub-agents so the manager can call them like tools,
    # while preserving conversation history and session state perfectly.
    sub_agents=[dice_agent, calculator_agent, coder_agent],
)
