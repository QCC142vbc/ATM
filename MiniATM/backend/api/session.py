from typing import Optional
from dataclasses import dataclass


@dataclass
class Session:
    user_id: str
    name: str


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(self, user_id: str, name: str) -> str:
        """Create a new session and return session ID."""
        session_id = self._generate_session_id()
        self._sessions[session_id] = Session(user_id=user_id, name=name)
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID, returns None if not found."""
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete session, returns True if existed."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def _generate_session_id(self) -> str:
        """Generate a simple session ID."""
        import secrets
        return secrets.token_urlsafe(32)


# Global session manager instance
session_manager = SessionManager()
