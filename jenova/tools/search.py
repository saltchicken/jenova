"""
Tools for external agent delegation and searching.
"""

import uuid
import httpx
import json

def ask_search_agent(task_description: str) -> str:
    """
    Delegates a task to Search Agent via the standard A2A JSON-RPC Protocol (v0.3.0).
    """
    print(
        f"\n[Orchestrator is calling Search Agent via A2A with task: '{task_description}']..."
    )

    url = "http://localhost:8001/"

    # Construct the strict A2A Protocol JSON-RPC Payload
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "contextId": "a2a_shared_session",
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
        data = response.json()

        if "error" in data:
            return f"Search Agent A2A Error: {data['error']}"

        result_data = data.get("result", {})
        parts = []

        if "artifacts" in result_data and result_data["artifacts"]:
            parts = result_data["artifacts"][0].get("parts", [])
        elif "history" in result_data and result_data["history"]:
            parts = result_data["history"][-1].get("parts", [])
        elif "message" in result_data:
            parts = result_data["message"].get("parts", [])
        else:
            parts = result_data.get("parts", [])

        # Extract text, specifically ignoring internal "adk_thought" processes
        final_answer = "".join(
            part.get("text", "") 
            for part in parts 
            if "text" in part and not part.get("metadata", {}).get("adk_thought")
        )

        return final_answer.strip() or "Search Agent successfully completed the action but returned no text."

    except Exception as exc:
        return f"A2A System Error: {exc}"
