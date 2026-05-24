"""
An example Master/Orchestrator Agent that delegates tasks to Jenova via A2A HTTP.
"""

import uuid

from google.adk import Agent
from google.adk import Context
from google.adk import Event
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import Session
import httpx

# Using the same model configuration you use for Jenova
llm_client = LiteLlm(model="ollama_chat/gemma4:e4b")


def ask_jenova(task_description: str) -> str:
    """
    Delegates a task to Jenova via the standard A2A JSON-RPC Protocol (v0.3.0).
    """
    print(
        f"\n[Orchestrator is calling Jenova via A2A with task: '{task_description}']..."
    )

    url = "http://localhost:8000/"

    # 3. Construct the strict A2A Protocol JSON-RPC Payload
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",  # The official A2A v0.3.0 method
        "params": {
            "message": {
                "kind": "message",
                "contextId":
                    "a2a_shared_session",  # Ensures Jenova remembers the thread
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{
                    "kind": "text",
                    "text": task_description
                }]
            }
        }
    }

    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        response.raise_for_status()

        # 4. Parse the standard A2A JSON-RPC Response
        data = response.json()

        if "error" in data:
            return f"Jenova A2A Error: {data['error']}"

        # 5. Extract the assistant's reply from the A2A response structure
        # The A2A protocol returns the result inside a mirrored 'message' object
        result_message = data.get("result", {}).get("message", {})
        parts = result_message.get("parts", [])

        final_answer = "".join(
            part.get("text", "")
            for part in parts
            if part.get("kind") == "text")

        return final_answer.strip(
        ) or "Jenova successfully completed the action but returned no text."

    except Exception as exc:
        return f"A2A System Error: {exc}"


# Define the Orchestrator Agent
root_agent = Agent(
    name="Orchestrator",
    model=llm_client,
    tools=[ask_jenova],
    instruction=
    ("You are the Master Orchestrator Agent. Your job is to chat with the user naturally.\n"
     "You possess general knowledge, but you CANNOT control smart home devices.\n"
     "If the user asks to control the lights (turn on/off), you MUST use the `ask_jenova` tool.\n"
     "If you use the tool, briefly summarize Jenova's response to the user."))
