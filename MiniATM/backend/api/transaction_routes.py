from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

from backend.api.auth_routes import get_current_user
from backend.application.transaction_service import TransactionService
from backend.domain.exceptions import DataCorruptionError
from backend.infrastructure.json_storage import JSONStorage
from backend.infrastructure.repositories import UserRepository


router = APIRouter()

storage = JSONStorage("backend/data/users.json")
user_repository = UserRepository(storage)
transaction_service = TransactionService(user_repository)


class TransactionResponse(BaseModel):
    transaction_type: str
    amount: str
    balance_after: str
    timestamp: str


@router.get("", response_model=list[TransactionResponse])
def get_transactions(session_id: str = Cookie(None)):
    """Get transaction history for current user."""
    try:
        user_id = get_current_user(session_id)
        transactions = transaction_service.get_transactions(user_id)

        return [
            TransactionResponse(
                transaction_type=t.transaction_type,
                amount=str(t.amount),
                balance_after=str(t.balance_after),
                timestamp=t.timestamp.isoformat(),
            )
            for t in transactions
        ]
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "USER_NOT_FOUND", "message": str(exc)}
        })
    except (DataCorruptionError, Exception):
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to retrieve transactions"}
        })
