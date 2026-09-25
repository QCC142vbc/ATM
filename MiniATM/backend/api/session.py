from dataclasses import dataclass
from typing import Optional


@dataclass
class Session:
    user_id: str
    name: str


class LoginAttemptTracker:
    MAX_ATTEMPTS = 3

    def __init__(self):
        self._failed_attempts: dict[str, int] = {}

    def record_failure(self, user_id: str) -> int:
        attempts = self._failed_attempts.get(user_id, 0) + 1
        self._failed_attempts[user_id] = attempts
        return attempts

    def record_success(self, user_id: str) -> None:
        self._failed_attempts.pop(user_id, None)

    def remaining_attempts(self, user_id: str) -> int:
        failed = self._failed_attempts.get(user_id, 0)
        return max(0, self.MAX_ATTEMPTS - failed)

    def is_locked(self, user_id: str) -> bool:
        return self._failed_attempts.get(user_id, 0) >= self.MAX_ATTEMPTS


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


session_manager = SessionManager()
login_attempt_tracker = LoginAttemptTracker()
