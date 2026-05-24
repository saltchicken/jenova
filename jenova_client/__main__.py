"""
Client script for interacting with the Jenova AI Assistant via the ADK API.
"""

import argparse
import json
import sys

import httpx
from loguru import logger

from jenova_client.chat import chat
from jenova_client.constants import DEFAULT_BASE_URL
from jenova_client.constants import DEFAULT_USER_ID
from jenova_client.session import SessionManager


def main():
    """Main entry point for the client application."""
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
            logger.info(json.dumps(manager.list(), indent=2))
        elif args.action == "create":
            logger.info(manager.create(args.session_id))
        elif args.action == "delete":
            if not args.session_id:
                logger.error("--session-id is required for delete.")
            else:
                logger.info(manager.delete(args.session_id))

    elif args.command == "chat":
        # Check if the session exists, and if not, create it
        try:
            session = manager.get(args.session_id)
            if session is None:
                logger.info(
                    f"Session '{args.session_id}' not found. Creating a new one..."
                )
                manager.create(args.session_id)
        except httpx.RequestError as exc:
            logger.error(
                f"Unable to connect to server to check session: {exc}"
            )
            sys.exit(1)
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Failed to get session: {exc.response.status_code} - {exc.response.text}"
            )
            sys.exit(1)

        chat(user_input=args.prompt,
             is_blocking=args.blocking,
             session_id=args.session_id,
             base_url=args.url,
             user_id=args.user_id)


if __name__ == "__main__":
    main()
