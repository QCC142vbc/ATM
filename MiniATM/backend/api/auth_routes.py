from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

from backend.application.auth_service import AuthService
from backend.domain.account import Account
from backend.domain.exceptions import AccountUnavailableError, DataCorruptionError
from backend.infrastructure.json_storage import JSONStorage
from backend.infrastructure.paths import USERS_FILE
from backend.infrastructure.repositories import UserRepository
from backend.api.session import login_attempt_tracker, session_manager


router = APIRouter()

storage = JSONStorage(USERS_FILE)
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


class ChangePinRequest(BaseModel):
    current_pin: str
    new_pin: str
    confirm_pin: str


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
    except AccountUnavailableError as exc:
        raise HTTPException(status_code=403, detail={
            "error": {"code": "ACCOUNT_UNAVAILABLE", "message": str(exc)}
        })
    except DataCorruptionError:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Unable to read authentication data"}
        })
    except OSError as exc:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "PERSISTENCE_ERROR", "message": "Unable to read authentication data"}
        }) from exc
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

    user = _get_active_account(session.user_id)

    return {"user_id": session.user_id, "name": session.name, "status": user.account.status}


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

    _get_active_account(session.user_id)
    return session.user_id


def _get_active_account(user_id: str):
    try:
        user = user_repository.get_by_id(user_id)
    except DataCorruptionError:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Unable to read account data"}
        })
    except OSError as exc:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "PERSISTENCE_ERROR", "message": "Unable to read account data"}
        }) from exc
    if user is None:
        raise HTTPException(status_code=401, detail={
            "error": {"code": "SESSION_EXPIRED", "message": "Session account is unavailable"}
        })
    if user.account.status != Account.ACTIVE:
        raise HTTPException(status_code=403, detail={
            "error": {
                "code": "ACCOUNT_UNAVAILABLE",
                "message": f"Account is {user.account.status.lower()}.",
            }
        })
    return user


@router.post("/change-pin")
def change_pin(request: ChangePinRequest, session_id: str = Cookie(None)):
    user_id = get_current_user(session_id)
    if request.new_pin != request.confirm_pin:
        raise HTTPException(status_code=400, detail={
            "error": {
                "code": "PIN_CONFIRMATION_MISMATCH",
                "message": "New PIN and confirmation do not match.",
            }
        })
    try:
        auth_service.change_pin(user_id, request.current_pin, request.new_pin)
    except AccountUnavailableError as exc:
        raise HTTPException(status_code=403, detail={
            "error": {"code": "ACCOUNT_UNAVAILABLE", "message": str(exc)}
        })
    except ValueError as exc:
        code = "INVALID_CURRENT_PIN" if "Current PIN" in str(exc) else "INVALID_NEW_PIN"
        raise HTTPException(status_code=400, detail={
            "error": {"code": code, "message": str(exc)}
        })
    except DataCorruptionError:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Unable to read account data"}
        })
    except OSError as exc:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "PERSISTENCE_ERROR", "message": "Unable to save the new PIN"}
        }) from exc
    return {"message": "PIN changed successfully."}
