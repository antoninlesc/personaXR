from typing import Dict

# Simple memory storage for POC dev (session_id, system prompt)
# In production, this should be replaced with a more robust solution (e.g., Redis, database) to handle multiple concurrent users and sessions.

session_storage: Dict[str, str] = {}

def get_system_prompt(session_id: str = "Default") -> str:
    """ Retrieve the system prompt for a given session ID. """
    return session_storage.get(session_id, "")

def set_system_prompt(system_prompt: str, session_id: str = "Default"):
    """ Set the system prompt for a given session ID. """
    session_storage[session_id] = system_prompt