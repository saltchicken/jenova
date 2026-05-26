"""
Agent discovery module for finding and creating dynamic tools from ADK agent cards.
"""

import uuid

import httpx
from loguru import logger


def discover_adk_agents(start_port: int = 8000,
                        end_port: int = 8010) -> list[dict]:
    """
    Sweeps localhost ports looking for the standard .well-known agent card.
    """
    active_cards = []

    for port in range(start_port, end_port + 1):
        manifest_url = f"http://localhost:{port}/.well-known/agent-card.json"
        try:
            response = httpx.get(manifest_url, timeout=0.5)
            if response.status_code == 200:
                card = response.json()
                
                card["url"] = f"http://localhost:{port}"
                print(f"PORT: {port}")
                
                active_cards.append(card)
                logger.info(f"Discovered '{card.get('name')}' on port {port}")
        except httpx.RequestError:
            continue  
        except Exception as e:
            logger.warning(f"Error parsing card on port {port}: {e}")

    return active_cards


def create_adk_tool(card: dict):
    """
    Dynamically generates a callable function from an ADK Agent Card 
    using the A2A JSON-RPC Protocol (v0.3.0).
    """
    agent_name = card.get("name", "UnknownAgent")
    # Clean the name so it's a valid Python function name
    safe_name = agent_name.replace(" ", "_").lower()

    # Extract the base URL from the agent card
    target_url = card.get("url", "http://localhost:8000")

    def dynamic_caller(query: str) -> str:
        logger.debug(
            f"[Orchestrator is calling {agent_name} via A2A with task: '{query}']..."
        )

        # Construct the strict A2A Protocol JSON-RPC Payload
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": {
                "message": {
                    "kind": "message",
                    "contextId": f"a2a_shared_session_{safe_name}",
                    "messageId": str(uuid.uuid4()),
                    "role": "user",
                    "parts": [{
                        "kind": "text",
                        "text": query
                    }]
                }
            }
        }

        try:
            # Note: 120s timeout, as A2A agent research tasks can be slow
            response = httpx.post(target_url, json=payload, timeout=120.0)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                return f"{agent_name} A2A Error: {data['error']}"

            result_data = data.get("result", {})
            parts = []

            # Your robust parsing logic to handle different A2A response shapes
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
                part.get("text", "") for part in parts if "text" in part and
                not part.get("metadata", {}).get("adk_thought"))

            return final_answer.strip(
            ) or f"{agent_name} successfully completed the action but returned no text."

        except Exception as exc:
            return f"A2A System Error contacting {agent_name}: {exc}"

    # --- CRITICAL: Inject Metadata for the LLM ---
    # Set the function name for the LLM schema
    dynamic_caller.__name__ = f"call_{safe_name}"

    # Extract the primary skill description to act as the tool's docstring
    skills = card.get("skills", [])
    if skills and len(skills) > 0 and "description" in skills[0]:
        dynamic_caller.__doc__ = (
            f"Passes a query to the {agent_name}. "
            f"Agent Description: {skills[0]['description']}")
    else:
        dynamic_caller.__doc__ = card.get("description",
                                          "Calls a remote A2A JSON-RPC agent.")

    return dynamic_caller
