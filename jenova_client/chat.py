"""
Chat interaction handling for the Jenova client.
"""

import json
import sys

import httpx
from httpx_sse import connect_sse
from loguru import logger

from jenova_client.constants import APP_NAME


def parse_event_parts(event_data: dict) -> tuple[str, str, str]:
    """
    Parses event payload and separates spoken text, tool logs, and agent thoughts.
    Returns:
        tuple[str, str, str]: (spoken_text, tool_log, thought_text)
    """
    parts = event_data.get("content", {}).get("parts", [])
    spoken_chunks = []
    tool_chunks = []
    thought_chunks = []

    for part in parts:
        if "text" in part:
            if part.get("thought", False):
                thought_chunks.append(part["text"])
            else:
                spoken_chunks.append(part["text"])

        # Capture the tool execution request
        elif "functionCall" in part:
            func_data = part["functionCall"]
            name = func_data.get("name", "UnknownTool")
            args = func_data.get("args", {})
            tool_chunks.append(f"⚡ [Executing Tool: {name} | Args: {args}] ⚡")

        # Capture the result returning from the tool
        elif "functionResponse" in part:
            func_data = part["functionResponse"]
            name = func_data.get("name", "UnknownTool")
            result = func_data.get("response", {}).get("result", "")
            tool_chunks.append(f"✅ [Tool Result ({name}): {result}] ✅")

    return "".join(spoken_chunks), "".join(tool_chunks), "".join(thought_chunks)


def _handle_streaming(url: str, payload: dict) -> None:
    """Handles a streaming chat request."""

    with httpx.Client() as client:
        with connect_sse(client, "POST", url, json=payload,
                         timeout=None) as event_source:
            for sse in event_source.iter_sse():
                data = json.loads(sse.data)

                node_name = data.get("author")
                is_partial = data.get("partial")

                if not node_name:
                    logger.warning("node_name was not successfully parsed")
                    continue

                is_internal = node_name.startswith("_")

                # Fetch separated data payloads
                spoken_text, tool_log, thought_text = parse_event_parts(data)

                if is_partial:
                    if spoken_text and not is_internal:
                        logger.opt(raw=True).info(spoken_text)
                else:
                    if spoken_text and is_internal:
                        logger.debug(spoken_text)
                    if tool_log:
                        logger.debug(tool_log)
                    if thought_text:
                        logger.debug(thought_text)


def _handle_blocking(url: str, payload: dict) -> None:
    """Handles a blocking chat request."""
    response = httpx.post(url, json=payload, timeout=None)
    response.raise_for_status()

    data = response.json()
    if isinstance(data, list):
        for event in data:
            node_name = event.get("author")

            if not node_name:
                continue

            is_internal = node_name.startswith("_")

            # Fetch separated data payloads
            spoken_text, tool_log, thought_text = parse_event_parts(event)

            if spoken_text and not is_internal:
                logger.opt(raw=True).info(spoken_text)
            if spoken_text and is_internal:
                logger.debug(spoken_text)
            if tool_log:
                logger.debug(tool_log)
            if thought_text:
                logger.debug(thought_text)

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
