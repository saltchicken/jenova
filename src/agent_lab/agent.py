import random
from typing import Literal

from google.adk import Agent, Event, Workflow
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool
from pydantic import BaseModel


# ==========================================
# 1. TOOLS & TRACKERS
# ==========================================
class DiceTracker:
    def __init__(self):
        self.total_rolls = 0

    def roll_die(self, sides: int) -> int:
        """Roll a die and return the rolled result."""
        self.total_rolls += 1  # Updates the counter every time the tool is called
        return random.randint(1, sides)

# Instantiate the tracker so it persists while the script runs
tracker = DiceTracker()

def check_prime(numbers: list[int]) -> dict[str, list[int]]:
    """Check if a given list of numbers are prime."""
    primes = []
    for number in numbers:
        number = int(number)
        if number <= 1:
            continue
        is_prime = True
        for i in range(2, int(number**0.5) + 1):
            if number % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(number)
    return {"primes_found": primes}

def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b


# ==========================================
# 2. STATE INITIALIZATION & ROUTING
# ==========================================
class TaskCategory(BaseModel):
    category: Literal["dice", "calculator", "coding", "general"]

def process_input(node_input: str):
    """Saves the initial user request and the current roll count to the shared state."""
    return Event(state={
        "input": node_input,
        "total_rolls": tracker.total_rolls
    })

classify_input = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="classify_input",
    instruction=(
        "Based on this input, decide which category it belongs to:\n"
        "- 'dice' if the user asks to roll a die or check primes.\n"
        "- 'calculator' if the user asks for math operations.\n"
        "- 'coding' if the user asks to write, review, or refactor code.\n"
        "- 'general' for anything else.\n"
        "Input: {input}"
    ),
    output_schema=TaskCategory,
    output_key="category",
)

def route_on_category(category: TaskCategory):
    """Reads the category from state and dictates the next edge."""
    yield Event(route=category.category)


# ==========================================
# 3. TOOL-CALLING AGENTS (Leaves)
# ==========================================
dice_agent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="dice_roll_agent",
    instruction="""
    You roll dice and answer questions about the outcome.
    You have rolled {total_rolls} dice so far in this session.
    
    When you are asked to roll a die, call the roll_die tool.
    When checking prime numbers, call the check_prime tool.
    Handle this request: {input}
    """,
    tools=[
        tracker.roll_die,  # Using the stateful tracker method here
        check_prime
    ],
    output_key="rolled_dice"
)

calculator_agent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="calculator_agent",
    instruction="""
    You are a calculator agent. Use tools for addition and multiplication.
    Handle this request: {input}
    """,
    tools=[FunctionTool(add_numbers), FunctionTool(multiply_numbers)],
)

general_agent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="general_agent",
    instruction="Respond to this general request: {input}",
)


# ==========================================
# 4. SEQUENTIAL CODER PIPELINE
# ==========================================
code_writer = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="code_writer",
    instruction="Write clean, functional code to solve: {input}",
    output_key="draft_code", # Saves output to state for the reviewer
)

code_reviewer = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="code_reviewer",
    instruction="Review this code for bugs and optimization:\n{draft_code}",
    output_key="review_feedback", # Saves output to state for the refactorer
)

code_refactorer = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="code_refactorer",
    instruction=(
        "Original code:\n{draft_code}\n\n"
        "Reviewer Feedback:\n{review_feedback}\n\n"
        "Output the final refactored code."
    ),
    output_key="refactored_code",
)

code_output_formatter = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="code_output_formatter",
    instruction="Output only the final code. Format this properly: {refactored_code}",
)


# ==========================================
# 5. THE WORKFLOW GRAPH
# ==========================================
root_agent = Workflow(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="root_agent",
    edges=[
        ("START", process_input, classify_input, route_on_category),
        (
            route_on_category,
            {
                "dice": dice_agent,
                "calculator": calculator_agent,
                "coding": code_writer,
                "general": general_agent,
            },
        ),
        # By passing these nodes as a tuple, the Workflow chains them sequentially!
        (code_writer, code_reviewer, code_refactorer, code_output_formatter),
    ],
)
