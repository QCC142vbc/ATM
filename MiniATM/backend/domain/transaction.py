from datetime import datetime
from decimal import Decimal


class Transaction:
    def __init__(
        self,
        transaction_type: str,
        amount: Decimal,
        balance_after: Decimal,
        timestamp: datetime | None = None,
    ):
        self.transaction_type = transaction_type
        self.amount = Decimal(amount)
        self.balance_after = Decimal(balance_after)
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> dict:
        return {
            "transaction_type": self.transaction_type,
            "amount": str(self.amount),
            "balance_after": str(self.balance_after),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            transaction_type=data["transaction_type"],
            amount=Decimal(data["amount"]),
            balance_after=Decimal(data["balance_after"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )