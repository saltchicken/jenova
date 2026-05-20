from functools import wraps
import random

from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm


def require_confirmation(func):
    """Decorator to prompt the user before executing a tool."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"\n⚠️ The agent wants to use the tool: '{func.__name__}'")
        if args or kwargs:
            print(f"   Arguments: args={args}, kwargs={kwargs}")

        while True:
            choice = input("   Allow this tool to run? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                return func(*args, **kwargs)
            elif choice in ['n', 'no']:
                return "The user denied permission to run this tool."
            else:
                print("   Please enter 'y' or 'n'.")

    return wrapper


@require_confirmation
def pick_a_card() -> str:
    """Pick a random card from a standard 52-card deck.

    Returns:
        A string representing the picked card.
    """
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = [
        "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King",
        "Ace"
    ]
    print("This tool was used")
    return f"{random.choice(ranks)} of {random.choice(suits)}"


@require_confirmation
def roll_die(sides: int) -> int:
    """Roll a die and return the rolled result.

    Args:
        sides: The integer number of sides the die has.

    Returns:
        An integer of the result of rolling the die.
    """
    return random.randint(1, sides)


@require_confirmation
def check_prime(numbers: list[int]) -> str:
    """Check if a given list of numbers are prime.

    Args:
        numbers: The list of numbers to check.

    Returns:
        A str indicating which number is prime.
    """
    primes = set()
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
            primes.add(number)
    return ("No prime numbers found." if not primes else
            f"{', '.join(str(num) for num in primes)} are prime numbers.")


root_agent = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="dice_roll_agent",
    description=(
        "hello world agent that can roll a dice of any number of sides and"
        " check prime numbers."),
    instruction="""
      You are a helpful agent that can roll dice, check prime numbers, and pick playing cards.

      Tool Usage Rules:
      - roll_die: Always use this to roll a die. Pass the number of sides as an integer, not a string. Never roll a die on your own.
      - check_prime: Always use this to check if numbers are prime. Pass a list of integers. Never calculate primes on your own.
      - pick_a_card: Use this to pick a random card from a standard deck.
      - You may use multiple tools in parallel when applicable.

      Workflow for "Roll and Check Prime":
      1. Call `roll_die` first to get a roll. Wait for the response.
      2. Call `check_prime` with the integer result from `roll_die`. If asked to check previous rolls, include those in the list.
      3. In your final response, explicitly state the die roll result and whether it was prime.

      General Guidelines:
      - Feel free to discuss and comment on previous rolls or picks.
      - Do not rely on conversational history to remember prime status; use the tool if unsure.
    """,
    tools=[roll_die, check_prime, pick_a_card],
)
