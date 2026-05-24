"""
Chat interaction handling for the Jenova client.
"""

import json
import sys

import httpx
from httpx_sse import connect_sse
from loguru import logger

from jenova_client.constants import APP_NAME


def get_text_from_event(event_data: dict) -> str | None:
    """Safely extracts and combines text from all parts of an event payload."""
    parts = event_data.get("content", {}).get("parts", [])
    text_chunks = []

    for part in parts:
        if "text" in part:
            if part.get("thought", False):
                pass
            else:
                text_chunks.append(part["text"])

        # Capture the tool execution request
        elif "functionCall" in part:
            func_data = part["functionCall"]
            name = func_data.get("name", "UnknownTool")
            args = func_data.get("args", {})
            text_chunks.append(
                f"\n⚡ [Executing Tool: {name} | Args: {args}] ⚡")

        # Capture the result returning from the tool
        elif "functionResponse" in part:
            func_data = part["functionResponse"]
            name = func_data.get("name", "UnknownTool")
            result = func_data.get("response", {}).get("result", "")
            text_chunks.append(f"\n✅ [Tool Result ({name}): {result}] ✅")

    if text_chunks:
        return "".join(text_chunks)

    return None


def _handle_streaming(url: str, payload: dict) -> None:
    """Handles a streaming chat request."""
    streamed_nodes = set()
    current_printing_node = None  # Track which node is outputting

    with httpx.Client() as client:
        with connect_sse(client, "POST", url, json=payload,
                         timeout=None) as event_source:
            for sse in event_source.iter_sse():
                data = json.loads(sse.data)

                # # TODO: Enable this for figuring out how to parse events. Remove when needed.
                # print("RAW EVENT:", json.dumps(data, indent=2))

                node_name = data.get("author")
                is_partial = data.get("partial")
                text_chunk = get_text_from_event(data)

                if not node_name or not text_chunk:
                    continue

                # If a different node starts talking, print a new prefix
                if current_printing_node != node_name:
                    if current_printing_node is not None:
                        logger.opt(raw=True).info("\n")  # Add a newline to close out the previous node
                    logger.opt(raw=True).info(f"[{node_name}]: ")
                    current_printing_node = node_name

                    # TODO: Make sure this isn't a bug
                    streamed_nodes.clear()

                if is_partial:
                    streamed_nodes.add(node_name)
                    logger.opt(raw=True).info(text_chunk)
                elif not is_partial and node_name not in streamed_nodes:
                    # ONLY print final events if we didn't already stream them
                    logger.opt(raw=True).info(text_chunk)


def _handle_blocking(url: str, payload: dict) -> None:
    """Handles a blocking chat request."""
    response = httpx.post(url, json=payload, timeout=None)
    response.raise_for_status()

    data = response.json()
    if isinstance(data, list):
        for event in data:
            node_name = event.get("author")
            text_chunk = get_text_from_event(event)

            if text_chunk and node_name:
                logger.info(f"[{node_name}]: {text_chunk}")
    else:
        logger.warning(f"Unexpected response format: {data}")


def chat(user_input: str, is_blocking: bool, session_id: str, base_url: str,
         user_id: str):
    """Sends a chat message to the agent."""
    endpoint = "/run" if is_blocking else "/run_sse"
    url = f"{base_url}{endpoint}"

    payload = {
        "app_name": APP_NAME,
        "newMessage": {
            "role": "user",
            "parts": [{
                "text": user_input
            }]
        },
        "userId": user_id,
        "sessionId": session_id,
        "streaming": not is_blocking
    }

    try:
        if not is_blocking:
            _handle_streaming(url, payload)
        else:
            _handle_blocking(url, payload)
    except httpx.RequestError as exc:
        logger.error(f"Unable to connect to server: {exc}")
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        logger.error(
            f"Server returned an error: {exc.response.status_code} - {exc.response.text}"
        )
        sys.exit(1)
    except json.JSONDecodeError as exc:
        logger.error(f"Error parsing JSON data: {exc}")
        sys.exit(1)
