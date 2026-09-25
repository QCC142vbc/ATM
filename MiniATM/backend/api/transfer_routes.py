from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field

from backend.api.auth_routes import get_current_user
from backend.application.transaction_limits import TransactionLimits
from backend.application.transfer_service import TransferService
from backend.domain.exceptions import (
    AccountUnavailableError,
    ATMError,
    DataCorruptionError,
    InsufficientFundsError,
    TransactionLimitError,
)
from backend.infrastructure.json_storage import JSONStorage
from backend.infrastructure.repositories import UserRepository

router = APIRouter()
user_repository = UserRepository(JSONStorage("backend/data/users.json"))
transfer_service = TransferService(user_repository, TransactionLimits.from_environment())


class TransferRequest(BaseModel):
    recipient_id: str = Field(min_length=1, max_length=64)
    amount: str
    description: str | None = Field(default=None, max_length=160)


@router.post("")
def transfer(request: TransferRequest, session_id: str = Cookie(None)):
    sender_id = get_current_user(session_id)
    try:
        amount = Decimal(request.amount)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_AMOUNT", "message": "Enter a valid amount."}
        }) from exc

    try:
        sender_balance, _recipient_balance, sent, _received = transfer_service.transfer(
            sender_id,
            request.recipient_id.strip(),
            amount,
            request.description.strip() if request.description else None,
        )
    except DataCorruptionError:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "Unable to read account records"}
        })
    except OSError as exc:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "PERSISTENCE_ERROR", "message": "Unable to save the transfer"}
        }) from exc
    except InsufficientFundsError as exc:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INSUFFICIENT_FUNDS", "message": str(exc)}
        })
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
        code = "SELF_TRANSFER" if "own account" in str(exc) else "USER_NOT_FOUND"
        status_code = 400 if code == "SELF_TRANSFER" else 404
        raise HTTPException(status_code=status_code, detail={
            "error": {"code": code, "message": str(exc)}
        })

    return {
        "balance": str(sender_balance),
        "transaction": sent.to_dict(),
    }
