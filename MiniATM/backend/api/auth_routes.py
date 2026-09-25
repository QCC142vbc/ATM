from pathlib import Path
import sys

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.application.auth_service import AuthService
from backend.infrastructure.json_storage import JSONStorage
from backend.infrastructure.repositories import UserRepository
from backend.api.session import login_attempt_tracker, session_manager


router = APIRouter()

storage = JSONStorage("backend/data/users.json")
user_repository = UserRepository(storage)
auth_service = AuthService(user_repository)


class LoginRequest(BaseModel):
    user_id: str
    pin: str


class LoginResponse(BaseModel):
    user_id: str
    name: str


class LoginSuccessResponse(BaseModel):
    user: LoginResponse


class ErrorResponse(BaseModel):
    error: dict


@router.post("/login", response_model=LoginSuccessResponse)
def login(request: LoginRequest, response: Response):
    """Authenticate user and create session."""
    user_id = request.user_id.strip()
    pin = request.pin.strip()

    if not user_id:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_USER_ID", "message": "User ID is required"}
        })

    if login_attempt_tracker.is_locked(user_id):
        raise HTTPException(status_code=401, detail={
            "error": {"code": "MAX_ATTEMPTS_REACHED", "message": "Maximum login attempts reached."}
        })

    try:
        user = auth_service.login(user_id, pin)
        login_attempt_tracker.record_success(user_id)
        session_id = session_manager.create_session(user.user_id, user.name)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=3600,
        )
        return LoginSuccessResponse(user=LoginResponse(user_id=user.user_id, name=user.name))
    except ValueError as exc:
        attempts_used = login_attempt_tracker.record_failure(user_id)
        remaining = max(0, 3 - attempts_used)
        if "User not found" in str(exc):
            raise HTTPException(status_code=401, detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User account not found",
                    "remaining_attempts": remaining,
                }
            })
        raise HTTPException(status_code=401, detail={
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Incorrect credentials.",
                "remaining_attempts": remaining,
            }
        })


@router.post("/logout")
def logout(response: Response, session_id: str = Cookie(None)):
    """Logout user and clear session."""
    if session_id:
        session_manager.delete_session(session_id)

    response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}


@router.get("/session")
def get_session(session_id: str = Cookie(None)):
    """Get current session information."""
    if not session_id:
        raise HTTPException(status_code=401, detail={
            "error": {"code": "UNAUTHORIZED", "message": "No active session"}
        })

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail={
            "error": {"code": "SESSION_EXPIRED", "message": "Session expired or invalid"}
        })

    return {"user_id": session.user_id, "name": session.name}


def get_current_user(session_id: str = Cookie(None)) -> str:
    """Helper function to get current user ID from session."""
    if not session_id:
        raise HTTPException(status_code=401, detail={
            "error": {"code": "UNAUTHORIZED", "message": "No active session"}
        })

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail={
            "error": {"code": "SESSION_EXPIRED", "message": "Session expired or invalid"}
        })

    return session.user_id
