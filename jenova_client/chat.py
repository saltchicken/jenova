"""
Chat interaction handling for the Jenova client.
"""

from dataclasses import dataclass
import json
import sys
from typing import Literal

import httpx
from httpx_sse import connect_sse
from loguru import logger

from jenova_client.constants import APP_NAME


@dataclass
class ParsedChunk:
    """Structured representation of a parsed event chunk."""
    node_name: str
    chunk_type: Literal["spoken", "thought", "tool_call", "tool_result"]
    text: str
    is_internal: bool


def parse_event_chunks(event_data: dict) -> list[ParsedChunk]:
    """
    Parses an event payload into an ordered list of strongly-typed chunks.
    """
    node_name = event_data.get("author")
    if not node_name:
        return []

    is_internal = node_name.startswith("_")
    parts = event_data.get("content", {}).get("parts", [])
    chunks = []

    for part in parts:
        if "text" in part:
            chunk_type = "thought" if part.get("thought", False) else "spoken"
            chunks.append(
                ParsedChunk(node_name, chunk_type, part["text"], is_internal))

        elif "functionCall" in part:
            func_data = part["functionCall"]
            name = func_data.get("name", "UnknownTool")
            args = func_data.get("args", {})
            text = f"⚡ [Executing Tool: {name} | Args: {args}] ⚡"
            chunks.append(ParsedChunk(node_name, "tool_call", text,
                                      is_internal))

        elif "functionResponse" in part:
            func_data = part["functionResponse"]
            name = func_data.get("name", "UnknownTool")
            
            # Grab the raw response object
            response_data = func_data.get("response", {})
            
            # If it's a dictionary, stringify it so we can see all keys (like 'stdout', 'error', etc.)
            if isinstance(response_data, dict):
                # Using json.dumps to make it readable in the terminal
                result = json.dumps(response_data) 
            else:
                result = str(response_data)
                
            text = f"✅ [Tool Result ({name}): {result}] ✅"
            chunks.append(
                ParsedChunk(node_name, "tool_result", text, is_internal))

    return chunks


def _log_chunk(chunk: ParsedChunk) -> None:
    """Helper utility to uniformly format and log parsed chunks."""
    if chunk.chunk_type == "spoken":
        if chunk.is_internal:
            logger.opt(raw=True,
                       colors=True).debug("<light-blue>{}</light-blue>",
                                          chunk.text)
        else:
            logger.opt(raw=True, colors=True).info(chunk.text)

    elif chunk.chunk_type == "thought":
        logger.opt(raw=True, colors=True).debug("<magenta>{}</magenta>",
                                                chunk.text)

    elif chunk.chunk_type in ("tool_call", "tool_result"):
        logger.opt(raw=True, colors=True).debug("<yellow>{}</yellow>",
                                                chunk.text)


def _handle_streaming(url: str, payload: dict) -> None:
    """Handles a streaming chat request."""
    current_node = None
    current_chunk_type = None

    with httpx.Client() as client:
        with connect_sse(client, "POST", url, json=payload,
                         timeout=None) as event_source:
            for sse in event_source.iter_sse():
                data = json.loads(sse.data)

                if "author" not in data:
                    logger.warning("node_name was not successfully parsed")
                    continue

                is_partial = data.get("partial", False)
                chunks = parse_event_chunks(data)

                for chunk in chunks:
                    if chunk.chunk_type in ("spoken",
                                            "thought") and not is_partial:
                        continue

                    # Log the node name and chunk type whenever either changes
                    if current_node != chunk.node_name or current_chunk_type != chunk.chunk_type:
                        current_node = chunk.node_name
                        current_chunk_type = chunk.chunk_type
                        logger.opt(raw=True, colors=True).debug(
                            "\n<blue>[{} | {}]</blue>\n", current_node,
                            current_chunk_type)

                    # Handle streaming vs. discrete chunks
                    if chunk.chunk_type in ("spoken", "thought"):
                        # Streamed text should only print partials to avoid
                        # duplicating the final accumulated message
                        if is_partial:
                            _log_chunk(chunk)

                    elif chunk.chunk_type in ("tool_call", "tool_result"):
                        # Tools are discrete events and typically do not carry the partial flag
                        if not is_partial:
                            _log_chunk(chunk)


def _handle_blocking(url: str, payload: dict) -> None:
    """Handles a blocking chat request."""
    response = httpx.post(url, json=payload, timeout=None)
    response.raise_for_status()

    data = response.json()
    current_node = None
    current_chunk_type = None

    if isinstance(data, list):
        for event in data:
            if "author" not in event:
                continue

            chunks = parse_event_chunks(event)

            for chunk in chunks:
                # Log the node name and chunk type whenever either changes
                if current_node != chunk.node_name or current_chunk_type != chunk.chunk_type:
                    current_node = chunk.node_name
                    current_chunk_type = chunk.chunk_type
                    logger.opt(raw=True,
                               colors=True).debug("\n<blue>[{} | {}]</blue>\n",
                                                  current_node,
                                                  current_chunk_type)

                _log_chunk(chunk)
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
