from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool

from .tools import add_numbers
from .tools import multiply_numbers

root_agent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="calculator_agent",
    description="An agent that performs basic math operations like addition and multiplication.",
    instruction="""
    You are a calculator agent. You answer math questions by using your tools.
    Always use the provided tools for addition and multiplication. Do not calculate the result yourself.
    """,
    tools=[
        FunctionTool(add_numbers),
        FunctionTool(multiply_numbers)
    ],
)
