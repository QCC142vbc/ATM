from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import os

from backend.domain.exceptions import TransactionLimitError
from backend.domain.transaction import Transaction


@dataclass(frozen=True)
class TransactionLimits:
    max_withdrawal: Decimal = Decimal("1000")
    daily_withdrawal: Decimal = Decimal("1000")
    max_transfer: Decimal = Decimal("1000")
    daily_transfer: Decimal = Decimal("3000")
    max_deposit: Decimal = Decimal("5000")

    def __post_init__(self):
        values = (
            self.max_withdrawal,
            self.daily_withdrawal,
            self.max_transfer,
            self.daily_transfer,
            self.max_deposit,
        )
        if any(not value.is_finite() or value <= 0 for value in values):
            raise ValueError("Transaction limits must be finite positive amounts.")

    @classmethod
    def from_environment(cls) -> "TransactionLimits":
        return cls(
            max_withdrawal=Decimal(os.getenv("MINIATM_MAX_WITHDRAWAL", "1000")),
            daily_withdrawal=Decimal(os.getenv("MINIATM_DAILY_WITHDRAWAL", "1000")),
            max_transfer=Decimal(os.getenv("MINIATM_MAX_TRANSFER", "1000")),
            daily_transfer=Decimal(os.getenv("MINIATM_DAILY_TRANSFER", "3000")),
            max_deposit=Decimal(os.getenv("MINIATM_MAX_DEPOSIT", "5000")),
        )

    @staticmethod
    def daily_total(transactions: list[Transaction], transaction_types: set[str]) -> Decimal:
        today = datetime.now().date()
        return sum(
            (
                transaction.amount
                for transaction in transactions
                if transaction.transaction_type in transaction_types
                and transaction.timestamp.date() == today
                and transaction.status == "completed"
            ),
            Decimal("0"),
        )

    def check_deposit(self, amount: Decimal) -> None:
        if amount > self.max_deposit:
            raise TransactionLimitError(
                f"Deposit limit is {self.max_deposit} per transaction."
            )

    def check_withdrawal(self, amount: Decimal, transactions: list[Transaction]) -> None:
        if amount > self.max_withdrawal:
            raise TransactionLimitError(
                f"Withdrawal limit is {self.max_withdrawal} per transaction."
            )
        used = self.daily_total(transactions, {"withdrawal"})
        if used + amount > self.daily_withdrawal:
            raise TransactionLimitError(
                f"Daily withdrawal limit is {self.daily_withdrawal}; "
                f"{max(Decimal('0'), self.daily_withdrawal - used)} remains."
            )

    def check_transfer(self, amount: Decimal, transactions: list[Transaction]) -> None:
        if amount > self.max_transfer:
            raise TransactionLimitError(
                f"Transfer limit is {self.max_transfer} per transaction."
            )
        used = self.daily_total(transactions, {"transfer_sent"})
        if used + amount > self.daily_transfer:
            raise TransactionLimitError(
                f"Daily transfer limit is {self.daily_transfer}; "
                f"{max(Decimal('0'), self.daily_transfer - used)} remains."
            )

    def usage(self, transactions: list[Transaction]) -> dict:
        return {
            "withdrawal_used": str(self.daily_total(transactions, {"withdrawal"})),
            "withdrawal_limit": str(self.daily_withdrawal),
            "transfer_used": str(self.daily_total(transactions, {"transfer_sent"})),
            "transfer_limit": str(self.daily_transfer),
        }
