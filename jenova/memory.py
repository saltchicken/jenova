import json
import os
from loguru import logger

MEMORY_FILE = "jenova_memory.json"

def load_memories() -> list[str]:
    """Loads all saved user facts."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load memory: {e}")
        return []

def save_memory(fact: str) -> str:
    """Appends a new fact to the memory file."""
    memories = load_memories()
    if fact not in memories:
        memories.append(fact)
        with open(MEMORY_FILE, "w") as f:
            json.dump(memories, f, indent=4)
        logger.info(f"New memory saved: {fact}")
        return f"Successfully remembered: {fact}"
    return "I already know that fact."
