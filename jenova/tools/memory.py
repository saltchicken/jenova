from loguru import logger
from jenova.memory import save_memory

def remember_user_fact(fact: str) -> str:
    """
    Saves an important fact about the user to long-term memory.
    Use this tool ONLY when the user explicitly states a preference, 
    important personal detail, or asks you to remember something.
    Keep the fact concise (e.g., "User's favorite color is blue").
    """
    logger.info(f"Agent requested to remember: {fact}")
    return save_memory(fact)
