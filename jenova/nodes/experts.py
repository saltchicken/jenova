"""
Domain-specific expert subagents.
"""

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm

import uuid, httpx, json

# DEFAULT_MODEL = "ollama_chat/devstral-small-2"
DEFAULT_MODEL = "ollama_chat/gemma4:e4b"
llm_client = LiteLlm(model=DEFAULT_MODEL)


def ask_search_agent(task_description: str) -> str:
    """
    Delegates a task to Search Agent via the standard A2A JSON-RPC Protocol (v0.3.0).
    """
    print(
        f"\n[Orchestrator is calling Search Agent via A2A with task: '{task_description}']..."
    )

    url = "http://localhost:8001/"

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

        # print(f"\n[RAW A2A RESPONSE from Search Agent]:\n{json.dumps(data, indent=2)}\n")

        if "error" in data:
            return f"Search Agent A2A Error: {data['error']}"

        result_data = data.get("result", {})
        parts = []

        # The ADK returns a 'Task' object when an agent completes a workflow.
        # Check 'artifacts' first, then fallback to the last message in 'history'.
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


tech_expert = Agent(
    model=llm_client,
    name="_tech_expert",
    instruction=
    ("You are a senior software engineer. Answer the following technical question "
     "clearly and concisely: {input}\n\nHere is the conversation history:\n{history?}"
    ),
)

math_expert = Agent(
    model=llm_client,
    name="_math_expert",
    instruction=(
        "You are a mathematician. Solve or answer the following math question "
        "step-by-step: {input}\n\nHere is the conversation history:\n{history?}"
    ),
)

general_expert = Agent(
    model=llm_client,
    name="_general_expert",
    instruction=
    ("You are a helpful AI assistant. Answer the following general question: {input}\n\n"
     "If you need current information, facts, or news, use the ask_search_agent tool.\n"
     "CRITICAL SEARCH RULES:\n"
     "1. Break complex questions into concise, keyword-heavy search queries.\n"
     "2. Do not use full sentences for search queries. (e.g., Use 'France capital population current' instead of 'What is the population of France').\n\n"
     "IMPORTANT: Once you have gathered enough information from the search results, "
     "you MUST stop calling tools. Synthesize the results and reply directly to the user.\n\n"
     "Here is the conversation history:\n{history?}"),
    tools=[ask_search_agent],
)
