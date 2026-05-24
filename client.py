import argparse
import json
import sys
from typing import Optional

import httpx
from httpx_sse import connect_sse

APP_NAME = "agent"
DEFAULT_USER_ID = "test_user"
DEFAULT_BASE_URL = "http://localhost:8000"


class SessionManager:

    def __init__(self,
                 base_url: str = DEFAULT_BASE_URL,
                 user_id: str = DEFAULT_USER_ID):
        self.base_url = base_url
        self.prefix = f"{self.base_url}/apps/{APP_NAME}/users/{user_id}/sessions"

    def list(self) -> dict | list:
        return httpx.get(self.prefix).json()

    def get(self, session_id: str) -> Optional[dict]:
        response = httpx.get(f"{self.prefix}/{session_id}")
        if response.status_code == 404:
            return None
        
        # Raise an exception for any other HTTP errors (e.g., 500)
        response.raise_for_status()
        return response.json()

    def create(self,
               session_id: Optional[str] = None,
               data: Optional[dict] = None) -> dict:
        url = f"{self.prefix}/{session_id}" if session_id else self.prefix
        return httpx.post(url, json=data or {}).json()

    def update(self, session_id: str, data: dict) -> dict:
        return httpx.patch(f"{self.prefix}/{session_id}", json=data).json()

    def delete(self, session_id: str) -> dict:
        return httpx.delete(f"{self.prefix}/{session_id}").json()


def get_text_from_event(event_data: dict) -> str | None:
    """Safely extracts and combines text from all parts of an event payload."""
    parts = event_data.get("content", {}).get("parts", [])

    # Extract text from every part that has a 'text' key, and join them together
    text_chunks = [part["text"] for part in parts if "text" in part]

    if text_chunks:
        return "".join(text_chunks)

    return None


def chat(user_input: str, is_blocking: bool, session_id: str, base_url: str,
         user_id: str):
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
            # --- STREAMING LOGIC ---
            streamed_nodes = set()
            current_printing_node = None  # Track which node is outputting

            with httpx.Client() as client:
                with connect_sse(client,
                                 "POST",
                                 url,
                                 json=payload,
                                 timeout=None) as event_source:
                    for sse in event_source.iter_sse():
                        data = json.loads(sse.data)

                        node_name = data.get("author")
                        is_partial = data.get("partial")
                        text_chunk = get_text_from_event(data)

                        if not node_name or not text_chunk:
                            continue

                        # If a different node starts talking, print a new prefix
                        if current_printing_node != node_name:
                            if current_printing_node is not None:
                                print() # Add a newline to close out the previous node
                            print(f"[{node_name}]: ", end="", flush=True)
                            current_printing_node = node_name

                        if is_partial:
                            streamed_nodes.add(node_name)
                            print(text_chunk, end="", flush=True)
                        elif not is_partial and node_name not in streamed_nodes:
                            # ONLY print final events if we didn't already stream them
                            print(text_chunk, end="", flush=True)

        else:
            # --- BLOCKING LOGIC ---
            response = httpx.post(url, json=payload, timeout=None)
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list):
                for event in data:
                    node_name = event.get("author")
                    text_chunk = get_text_from_event(event)
                    
                    if text_chunk and node_name:
                        print(f"[{node_name}]: {text_chunk}")
            else:
                print("Unexpected response format:", data)

    except httpx.RequestError as exc:
        print(f"\n[Error] Unable to connect to server: {exc}")
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        print(
            f"\n[Error] Server returned an error: {exc.response.status_code} - {exc.response.text}"
        )
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"\n[Error] Error parsing JSON data: {exc}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Chat with Jenova AI Assistant")
    parser.add_argument("--url",
                        default=DEFAULT_BASE_URL,
                        help="Base URL of the agent server")
    parser.add_argument("--user-id",
                        default=DEFAULT_USER_ID,
                        help="User ID for the session")

    subparsers = parser.add_subparsers(dest="command",
                                       help="Available commands")

    # Command: chat
    chat_parser = subparsers.add_parser("chat",
                                        help="Send a message to the agent")
    chat_parser.add_argument("prompt", type=str, help="The message to send")
    
    # REQUIRE the session-id flag without a default
    chat_parser.add_argument("--session-id",
                             required=True,
                             help="The session ID to use")
    chat_parser.add_argument(
        "--blocking",
        action="store_true",
        help="Use blocking /run instead of streaming /run_sse")

    # Command: sessions
    session_parser = subparsers.add_parser("sessions", help="Manage sessions")
    session_parser.add_argument("action",
                                choices=["list", "create", "delete"],
                                help="Session action to perform")
    session_parser.add_argument("--session-id",
                                help="Session ID (required for create/delete)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = SessionManager(base_url=args.url, user_id=args.user_id)

    if args.command == "sessions":
        if args.action == "list":
            print(json.dumps(manager.list(), indent=2))
        elif args.action == "create":
            print(manager.create(args.session_id))
        elif args.action == "delete":
            if not args.session_id:
                print("Error: --session-id is required for delete.")
            else:
                print(manager.delete(args.session_id))

    elif args.command == "chat":
        # Check if the session exists, and if not, create it
        try:
            session = manager.get(args.session_id)
            if session is None:
                print(f"[Info] Session '{args.session_id}' not found. Creating a new one...")
                manager.create(args.session_id)
        except httpx.RequestError as exc:
            print(f"\n[Error] Unable to connect to server to check session: {exc}")
            sys.exit(1)
        except httpx.HTTPStatusError as exc:
            print(f"\n[Error] Failed to get session: {exc.response.status_code} - {exc.response.text}")
            sys.exit(1)

        chat(user_input=args.prompt,
             is_blocking=args.blocking,
             session_id=args.session_id,
             base_url=args.url,
             user_id=args.user_id)


if __name__ == "__main__":
    main()
