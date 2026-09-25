from datetime import datetime
from decimal import Decimal
from uuid import uuid4


class Transaction:
    def __init__(
        self,
        transaction_type: str,
        amount: Decimal,
        balance_after: Decimal,
        timestamp: datetime | None = None,
        transaction_id: str | None = None,
        user_id: str | None = None,
        counterparty_id: str | None = None,
        counterparty_name: str | None = None,
        description: str | None = None,
        status: str = "completed",
    ):
        if transaction_type not in {
            "deposit",
            "withdrawal",
            "transfer_sent",
            "transfer_received",
        }:
            raise ValueError("Unsupported transaction type.")

        self.transaction_id = transaction_id or str(uuid4())
        self.transaction_type = transaction_type
        self.amount = Decimal(amount)
        self.balance_after = Decimal(balance_after)
        self.timestamp = timestamp or datetime.now()
        self.user_id = user_id
        self.counterparty_id = counterparty_id
        self.counterparty_name = counterparty_name
        self.description = description
        self.status = status

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type,
            "amount": str(self.amount),
            "balance_after": str(self.balance_after),
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "counterparty_id": self.counterparty_id,
            "counterparty_name": self.counterparty_name,
            "description": self.description,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            transaction_type=data["transaction_type"],
            amount=Decimal(data["amount"]),
            balance_after=Decimal(data["balance_after"]),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            transaction_id=data.get("transaction_id"),
            user_id=data.get("user_id"),
            counterparty_id=data.get("counterparty_id"),
            counterparty_name=data.get("counterparty_name"),
            description=data.get("description"),
            status=data.get("status", "completed"),
        )