from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

from backend.api.account_routes import atm_service
from backend.api.auth_routes import get_current_user
from backend.application.banknote_service import (
    ATMWithdrawalService,
    InvalidBanknoteWithdrawalError,
)
from backend.domain.exceptions import (
    AccountUnavailableError,
    ATMError,
    DataCorruptionError,
    InsufficientFundsError,
    TransactionLimitError,
)
from backend.infrastructure.atm_cash_storage import ATMCashStorage
from backend.infrastructure.paths import ATM_CASH_FILE

router = APIRouter()
atm_withdrawal_service = ATMWithdrawalService(
    atm_service,
    ATMCashStorage(ATM_CASH_FILE),
)


class ATMWithdrawalRequest(BaseModel):
    amount: str


@router.get("/cash")
def get_atm_cash(session_id: str = Cookie(None)):
    get_current_user(session_id)
    try:
        inventory = atm_withdrawal_service.get_inventory()
        total_cash = atm_withdrawal_service.total_cash()
    except DataCorruptionError:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "ATM inventory data is invalid."}
        })
    except OSError as exc:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "CASH_STORAGE_ERROR", "message": "Unable to read ATM cash inventory."}
        }) from exc
    return {
        "inventory": {str(denomination): count for denomination, count in inventory.items()},
        "total_cash": str(total_cash),
    }


@router.post("/withdraw")
def withdraw_cash(request: ATMWithdrawalRequest, session_id: str = Cookie(None)):
    user_id = get_current_user(session_id)
    try:
        amount = Decimal(request.amount)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_AMOUNT", "message": "Enter a valid amount."}
        }) from exc

    try:
        balance, notes = atm_withdrawal_service.withdraw(user_id, amount)
    except DataCorruptionError:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_ERROR", "message": "ATM inventory data is invalid."}
        })
    except InvalidBanknoteWithdrawalError as exc:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "UNAVAILABLE_DENOMINATIONS", "message": str(exc)}
        })
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
        raise HTTPException(status_code=404, detail={
            "error": {"code": "USER_NOT_FOUND", "message": str(exc)}
        })
    except OSError as exc:
        raise HTTPException(status_code=500, detail={
            "error": {"code": "CASH_STORAGE_ERROR", "message": "Unable to update ATM cash inventory."}
        }) from exc

    return {
        "balance": str(balance),
        "banknotes": {str(denomination): count for denomination, count in notes.items()},
        "total_cash": str(atm_withdrawal_service.total_cash()),
    }
