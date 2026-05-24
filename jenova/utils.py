"""
Utility functions for the agent.
"""

from google.adk import Context

def get_full_history(ctx: Context, max_messages: int = 10) -> list[dict]:
    """
    Extracts the conversation history, ignoring internal nodes (starting with '_'),
    and trims it to the last `max_messages` to fit the context window.
    """
    history = []

    for event in ctx.session.events:
        author = event.author or ""
        
        if author.startswith("_"):
            continue
            
        if event.content and event.content.parts:
            text = "".join(part.text for part in event.content.parts if part.text)
            
            if text:
                role = "user" if author == "user" else "assistant"
                history.append({"role": role, "content": text})

    if max_messages > 0:
        return history[-max_messages:]
        
    return history
