from decimal import Decimal

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

from backend.application.atm_service import ATMService
from backend.application.transaction_service import TransactionService
from backend.domain.exceptions import ATMError, DataCorruptionError
from backend.infrastructure.json_storage import JSONStorage
from backend.infrastructure.repositories import UserRepository
from backend.api.auth_routes import get_current_user


router = APIRouter()

storage = JSONStorage("backend/data/users.json")
user_repository = UserRepository(storage)
transaction_service = TransactionService(user_repository)
atm_service = ATMService(user_repository, transaction_service)


class AccountResponse(BaseModel):
    user_id: str
    name: str
    balance: str


class TransactionRequest(BaseModel):
    amount: str


class TransactionResponse(BaseModel):
    balance: str


@router.get("", response_model=AccountResponse)
def get_account(session_id: str = Cookie(None)):
    """Get current account information."""
    try:
        user_id = get_current_user(session_id)
        user = user_repository.get_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail={
                "error": {"code": "USER_NOT_FOUND", "message": "User account not found"}
            })

        return AccountResponse(
            user_id=user.user_id,
            name=user.name,
            balance=str(user.account.balance),
        )
    except HTTPException:
        raise
    except (DataCorruptionError, Exception):
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to retrieve account information"}
        })


@router.get("/balance")
def get_balance(session_id: str = Cookie(None)):
    """Get current account balance."""
    try:
        user_id = get_current_user(session_id)
        balance = atm_service.get_balance(user_id)
        return {"balance": str(balance)}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "USER_NOT_FOUND", "message": str(exc)}
        })
    except (DataCorruptionError, Exception):
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to retrieve balance"}
        })


@router.post("/deposit", response_model=TransactionResponse)
def deposit(request: TransactionRequest, session_id: str = Cookie(None)):
    """Deposit money into account."""
    try:
        user_id = get_current_user(session_id)
        amount = Decimal(request.amount)
        balance = atm_service.deposit(user_id, amount)
        return TransactionResponse(balance=str(balance))
    except HTTPException:
        raise
    except ATMError as exc:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_AMOUNT", "message": str(exc)}
        })
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "USER_NOT_FOUND", "message": str(exc)}
        })
    except (DataCorruptionError, Exception):
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to process deposit"}
        })


@router.post("/withdraw", response_model=TransactionResponse)
def withdraw(request: TransactionRequest, session_id: str = Cookie(None)):
    """Withdraw money from account."""
    try:
        user_id = get_current_user(session_id)
        amount = Decimal(request.amount)
        balance = atm_service.withdraw(user_id, amount)
        return TransactionResponse(balance=str(balance))
    except HTTPException:
        raise
    except ATMError as exc:
        error_msg = str(exc)
        if "Insufficient funds" in error_msg:
            raise HTTPException(status_code=400, detail={
                "error": {"code": "INSUFFICIENT_FUNDS", "message": "Insufficient funds"}
            })
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_AMOUNT", "message": error_msg}
        })
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "USER_NOT_FOUND", "message": str(exc)}
        })
    except (DataCorruptionError, Exception):
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to process withdrawal"}
        })
