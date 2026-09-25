from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

from backend.application.atm_service import ATMService
from backend.application.transaction_service import TransactionService
from backend.application.transaction_limits import TransactionLimits
from backend.domain.exceptions import (
    AccountUnavailableError,
    ATMError,
    DataCorruptionError,
    TransactionLimitError,
)
from backend.infrastructure.json_storage import JSONStorage
from backend.infrastructure.repositories import UserRepository
from backend.api.auth_routes import get_current_user


router = APIRouter()

storage = JSONStorage("backend/data/users.json")
user_repository = UserRepository(storage)
transaction_service = TransactionService(user_repository)
limits = TransactionLimits.from_environment()
atm_service = ATMService(user_repository, transaction_service, limits)


class AccountResponse(BaseModel):
    user_id: str
    name: str
    balance: str
    status: str
    limits: dict[str, str]


class TransactionRequest(BaseModel):
    amount: str


class TransactionResponse(BaseModel):
    balance: str


def _parse_amount(raw_amount: str) -> Decimal:
    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_AMOUNT", "message": "Enter a valid amount."}
        }) from exc
    if not amount.is_finite():
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_AMOUNT", "message": "Enter a finite amount."}
        })
    return amount


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

        return AccountResponse(**atm_service.get_account_summary(user_id))
    except HTTPException:
        raise
    except DataCorruptionError:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to retrieve account information"}
        })
    except OSError as exc:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "PERSISTENCE_ERROR", "message": "Unable to read account data"}
        }) from exc


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
    except DataCorruptionError:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to retrieve balance"}
        })
    except OSError as exc:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "PERSISTENCE_ERROR", "message": "Unable to read account data"}
        }) from exc


@router.post("/deposit", response_model=TransactionResponse)
def deposit(request: TransactionRequest, session_id: str = Cookie(None)):
    """Deposit money into account."""
    try:
        user_id = get_current_user(session_id)
        amount = _parse_amount(request.amount)
        balance = atm_service.deposit(user_id, amount)
        return TransactionResponse(balance=str(balance))
    except HTTPException:
        raise
    except DataCorruptionError:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Unable to read account data"}
        })
    except OSError as exc:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "PERSISTENCE_ERROR", "message": "Unable to save the deposit"}
        }) from exc
    except TransactionLimitError as exc:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "TRANSACTION_LIMIT_EXCEEDED", "message": str(exc)}
        })
    except AccountUnavailableError as exc:
        raise HTTPException(status_code=403, detail={
            "error": {"code": "ACCOUNT_UNAVAILABLE", "message": str(exc)}
        })
    except ATMError as exc:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_AMOUNT", "message": str(exc)}
        })
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "USER_NOT_FOUND", "message": str(exc)}
        })


@router.post("/withdraw", response_model=TransactionResponse)
def withdraw(request: TransactionRequest, session_id: str = Cookie(None)):
    """Withdraw money from account."""
    try:
        user_id = get_current_user(session_id)
        amount = _parse_amount(request.amount)
        balance = atm_service.withdraw(user_id, amount)
        return TransactionResponse(balance=str(balance))
    except HTTPException:
        raise
    except DataCorruptionError:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Unable to read account data"}
        })
    except OSError as exc:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "PERSISTENCE_ERROR", "message": "Unable to save the withdrawal"}
        }) from exc
    except TransactionLimitError as exc:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "TRANSACTION_LIMIT_EXCEEDED", "message": str(exc)}
        })
    except AccountUnavailableError as exc:
        raise HTTPException(status_code=403, detail={
            "error": {"code": "ACCOUNT_UNAVAILABLE", "message": str(exc)}
        })
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
