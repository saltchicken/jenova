from agent.graph import root_agent
from agent.services.db import DatabaseSessionService

def start_server():
    """
    Bootstraps and starts the API server for the agent.
    """
    db_service = DatabaseSessionService()
    db_service.connect()
    
    print("[Server] Initializing API server with root_agent...")
    # Intended location for actual API server framework launch (e.g., ADK api_server)

if __name__ == "__main__":
    start_server()
