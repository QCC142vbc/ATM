from fastapi import APIRouter, HTTPException, Cookie, Response
from pydantic import BaseModel
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from application.auth_service import AuthService
from infrastructure.json_storage import JSONStorage
from infrastructure.repositories import UserRepository
from api.session import session_manager


router = APIRouter()

# Initialize services
storage = JSONStorage("backend/data/users.json")
user_repository = UserRepository(storage)
auth_service = AuthService(user_repository)


class LoginRequest(BaseModel):
    user_id: str
    pin: str


class LoginResponse(BaseModel):
    user_id: str
    name: str


class ErrorResponse(BaseModel):
    error: dict


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, response: Response):
    """Authenticate user and create session."""
    try:
        user = auth_service.login(request.user_id, request.pin)
        
        # Create session
        session_id = session_manager.create_session(user.user_id, user.name)
        
        # Set HTTP-only cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=3600  # 1 hour
        )
        
        return LoginResponse(user_id=user.user_id, name=user.name)
        
    except ValueError as e:
        error_msg = str(e)
        if "User not found" in error_msg:
            raise HTTPException(status_code=401, detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User account not found"
                }
            })
        elif "Invalid PIN" in error_msg:
            raise HTTPException(status_code=401, detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid credentials"
                }
            })
        else:
            raise HTTPException(status_code=401, detail={
                "error": {
                    "code": "AUTH_ERROR",
                    "message": error_msg
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
            "error": {
                "code": "UNAUTHORIZED",
                "message": "No active session"
            }
        })
    
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail={
            "error": {
                "code": "SESSION_EXPIRED",
                "message": "Session expired or invalid"
            }
        })
    
    return {
        "user_id": session.user_id,
        "name": session.name
    }


def get_current_user(session_id: str = Cookie(None)) -> str:
    """Helper function to get current user ID from session."""
    if not session_id:
        raise HTTPException(status_code=401, detail={
            "error": {
                "code": "UNAUTHORIZED",
                "message": "No active session"
            }
        })
    
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail={
            "error": {
                "code": "SESSION_EXPIRED",
                "message": "Session expired or invalid"
            }
        })
    
    return session.user_id
