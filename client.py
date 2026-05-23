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

    def get(self, session_id: str) -> dict:
        return httpx.get(f"{self.prefix}/{session_id}").json()

    def create(self,
               session_id: Optional[str] = None,
               data: Optional[dict] = None) -> dict:
        url = f"{self.prefix}/{session_id}" if session_id else self.prefix
        return httpx.post(url, json=data or {}).json()

    def update(self, session_id: str, data: dict) -> dict:
        return httpx.patch(f"{self.prefix}/{session_id}", json=data).json()

    def delete(self, session_id: str) -> dict:
        return httpx.delete(f"{self.prefix}/{session_id}").json()


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

    print(f"\nUser:  {user_input}")
    print("Agent: ", end="", flush=True)

    try:
        if not is_blocking:
            # --- STREAMING LOGIC ---
            intent_buffer = ""

            with httpx.Client() as client:
                with connect_sse(client,
                                 "POST",
                                 url,
                                 json=payload,
                                 timeout=None) as event_source:
                    for sse in event_source.iter_sse():
                        data = json.loads(sse.data)

                        node_name = data.get("author")
                        # print(node_name)

                        if data.get("partial"):
                            parts = data.get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                text_chunk = parts[0]["text"]

                                # If it's from the intent classifier, buffer it instead of printing
                                if node_name == "classify_intent":
                                    intent_buffer += text_chunk
                                elif node_name == "answer_question":
                                    print(text_chunk, end="", flush=True)
                                else:
                                    print(f"Haven't handled {node_name} yet")

                        # Once the classifier node finishes, parse the buffered JSON
                        elif node_name == "classify_intent" and not data.get(
                                "partial") and intent_buffer:
                            try:
                                parsed_data = json.loads(intent_buffer)
                                parsed_intent = parsed_data.get("intent")
                                # Optional: Do something programmatically with parsed_intent here
                                # print(f"[Debug: Parsed intent is '{parsed_intent}'] ")
                                intent_buffer = ""  # Reset buffer
                            except json.JSONDecodeError:
                                pass
                        else:
                            parts = data.get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                text_chunk = parts[0]["text"]
                                print(text_chunk, end="", flush=True)
            print("\n")

        else:
            # --- BLOCKING LOGIC ---
            response = httpx.post(url, json=payload, timeout=None)
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list):
                for event in data:
                    node_name = event.get("author")
                    # if node_name == "classify_intent":
                    #     continue
                    print("------------")
                    print(f"Node name: {node_name}")
                    parts = event.get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        print(parts[0]["text"])
                    print("----------")
            else:
                print("Unexpected response format:", data)
            print("\n")

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
    chat_parser.add_argument("--session-id",
                             default="default_session",
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
        chat(user_input=args.prompt,
             is_blocking=args.blocking,
             session_id=args.session_id,
             base_url=args.url,
             user_id=args.user_id)


if __name__ == "__main__":
    main()
