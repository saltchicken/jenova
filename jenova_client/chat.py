"""
Chat interaction handling for the Jenova client.
"""

import json
import sys

import httpx
from httpx_sse import connect_sse
from loguru import logger

from jenova_client.constants import APP_NAME


def get_text_from_event(event_data: dict, is_internal: bool = False, apply_colors: bool = False) -> str | None:
    """Safely extracts and combines text from all parts of an event payload."""
    parts = event_data.get("content", {}).get("parts", [])
    text_chunks = []
    
    magenta = "\033[35m"
    reset = "\033[0m"
    
    # Only apply magenta if it's an external node AND colors are requested
    c_start = magenta if (apply_colors and not is_internal) else ""
    c_end = reset if (apply_colors and not is_internal) else ""

    for part in parts:
        if "text" in part:
            if part.get("thought", False):
                pass
            else:
                # Color standard text
                text_chunks.append(f"{c_start}{part['text']}{c_end}")

        # Capture the tool execution request (Uncolored)
        elif "functionCall" in part:
            func_data = part["functionCall"]
            name = func_data.get("name", "UnknownTool")
            args = func_data.get("args", {})
            text_chunks.append(
                f"\n⚡ [Executing Tool: {name} | Args: {args}] ⚡")

        # Capture the result returning from the tool (Uncolored)
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
    current_printing_node = None

    with httpx.Client() as client:
        with connect_sse(client, "POST", url, json=payload,
                         timeout=None) as event_source:
            for sse in event_source.iter_sse():
                data = json.loads(sse.data)

                node_name = data.get("author")
                is_partial = data.get("partial")
                
                if not node_name:
                    continue
                    
                is_internal = node_name.startswith("_")
                
                # Fetch text chunks formatted for their specific destinations
                ui_text_chunk = get_text_from_event(data, is_internal=is_internal, apply_colors=True)
                tts_text_chunk = get_text_from_event(data, is_internal=is_internal, apply_colors=False)

                if not ui_text_chunk:
                    continue

                # ==========================================
                # 1. TERMINAL UI: Formatting and Logging
                # ==========================================
                if current_printing_node != node_name:
                    if current_printing_node is not None:
                        logger.opt(raw=True).info("\n")  
                    
                    logger.opt(raw=True).info(f"[{node_name}]: ")
                    current_printing_node = node_name
                    streamed_nodes.clear()

                if is_partial:
                    streamed_nodes.add(node_name)
                    logger.opt(raw=True).info(f"{ui_text_chunk}")
                elif not is_partial and node_name not in streamed_nodes:
                    logger.opt(raw=True).info(f"{ui_text_chunk}")

                # ==========================================
                # 2. AUDIO ROUTING: Pure TTS Payload
                # ==========================================
                if not is_internal and tts_text_chunk:
                    # The tts_text_chunk here is completely clean of formatting.
                    pass


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
            
            ui_text_chunk = get_text_from_event(event, is_internal=is_internal, apply_colors=True)
            tts_text_chunk = get_text_from_event(event, is_internal=is_internal, apply_colors=False)

            if not ui_text_chunk:
                continue

            # ==========================================
            # 1. TERMINAL UI: Formatting and Logging
            # ==========================================
            logger.info(f"[{node_name}]: {ui_text_chunk}")

            # ==========================================
            # 2. AUDIO ROUTING: Pure TTS Payload
            # ==========================================
            if not is_internal and tts_text_chunk:
                pass
                
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
