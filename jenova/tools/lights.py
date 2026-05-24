"""
Tools for controlling lights.
"""

from loguru import logger


def turn_on_lights(room: str) -> str:
    """
    Turns on lights in the specified room.
    """
    logger.info(f"Turning on {room} lights...")
    return f"The {room} lights are now on."


def turn_off_lights(room: str) -> str:
    """
    Turns off lights in the specified room.
    """
    logger.info(f"Turning off {room} lights...")
    return f"The {room} lights are now off."
