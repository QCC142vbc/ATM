from decimal import Decimal
from threading import RLock

from backend.domain.account import Account
from backend.domain.exceptions import AccountUnavailableError
from backend.application.transaction_limits import TransactionLimits


class ATMService:
    def __init__(self, user_repository, transaction_service, limits: TransactionLimits | None = None):
        self.user_repository = user_repository
        self.transaction_service = transaction_service
        self.limits = limits or TransactionLimits()
        self._lock = getattr(user_repository, "transaction_lock", RLock())

    def get_balance(self, user_id: str) -> Decimal:
        user = self._get_user(user_id)

        return user.account.get_balance()

    def deposit(self, user_id: str, amount: Decimal, description: str | None = None) -> Decimal:
        with self._lock:
            user = self._get_user(user_id)
            self._ensure_active(user)
            amount = user.account.validate_deposit_amount(Decimal(amount))
            self.limits.check_deposit(amount)

            user.account.deposit(amount)

            balance_after = user.account.get_balance()

            self.transaction_service.record_deposit(
                user,
                amount,
                balance_after,
                description,
            )

            self.user_repository.save(user)

            return balance_after

    def withdraw(self, user_id: str, amount: Decimal, description: str | None = None) -> Decimal:
        with self._lock:
            user = self._get_user(user_id)
            self._ensure_active(user)
            amount = user.account.validate_withdrawal_amount(Decimal(amount))
            self.limits.check_withdrawal(amount, user.transactions)

            user.account.withdraw(amount)

            balance_after = user.account.get_balance()

            self.transaction_service.record_withdrawal(
                user,
                amount,
                balance_after,
                description,
            )

            self.user_repository.save(user)

            return balance_after

    def get_account_summary(self, user_id: str) -> dict:
        user = self._get_user(user_id)
        return {
            "user_id": user.user_id,
            "name": user.name,
            "balance": str(user.account.balance),
            "status": user.account.status,
            "limits": self.limits.usage(user.transactions),
        }

    @staticmethod
    def _ensure_active(user) -> None:
        if user.account.status != Account.ACTIVE:
            raise AccountUnavailableError(
                f"Account is {user.account.status.lower()}."
            )

    def _get_user(self, user_id: str):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        return user