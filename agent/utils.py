from google.adk import Context

def get_user_history(ctx: Context) -> list[dict]:
    """
    Filters the ADK session event log to return only user messages.
    """
    user_history = []
    
    # Iterate through the native framework event log
    for event in ctx.session.events:
        if event.author == "user":
            # Safely check if the event has readable text content
            if event.content and event.content.parts:
                # Combine the text from all parts (usually just one part)
                text = "".join(part.text for part in event.content.parts if part.text)
                
                user_history.append({
                    "role": "user",
                    "content": text
                })
                
    return user_history

