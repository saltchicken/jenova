"""
Session management for the Jenova client.
"""

from typing import Optional

import httpx

from jenova_client.constants import APP_NAME
from jenova_client.constants import DEFAULT_BASE_URL
from jenova_client.constants import DEFAULT_USER_ID


class SessionManager:
    """Manages sessions for the client."""

    def __init__(self,
                 base_url: str = DEFAULT_BASE_URL,
                 user_id: str = DEFAULT_USER_ID):
        """Initializes the session manager."""
        self.base_url = base_url
        self.prefix = f"{self.base_url}/apps/{APP_NAME}/users/{user_id}/sessions"

    def list(self) -> dict | list:
        """Lists all sessions for the user."""
        return httpx.get(self.prefix).json()

    def get(self, session_id: str) -> Optional[dict]:
        """Gets a session by ID."""
        response = httpx.get(f"{self.prefix}/{session_id}")
        if response.status_code == 404:
            return None

        # Raise an exception for any other HTTP errors (e.g., 500)
        response.raise_for_status()
        return response.json()

    def create(self,
               session_id: Optional[str] = None,
               data: Optional[dict] = None) -> dict:
        """Creates a new session."""
        url = f"{self.prefix}/{session_id}" if session_id else self.prefix
        return httpx.post(url, json=data or {}).json()

    def update(self, session_id: str, data: dict) -> dict:
        """Updates a session."""
        return httpx.patch(f"{self.prefix}/{session_id}", json=data).json()

    def delete(self, session_id: str) -> dict:
        """Deletes a session."""
        return httpx.delete(f"{self.prefix}/{session_id}").json()
