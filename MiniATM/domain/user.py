from decimal import Decimal

from .account import Account
from .transaction import Transaction


class User:
    def __init__(
        self,
        user_id: str,
        name: str,
        pin: str,
        account: Account | None = None,
        transactions: list[Transaction] | None = None,
    ):
        self.user_id = user_id
        self.name = name
        self._pin = pin
        self.account = account or Account()
        self.transactions = transactions or []

    def verify_pin(self, pin: str) -> bool:
        return self._pin == pin

    def add_transaction(self, transaction: Transaction) -> None:
        self.transactions.append(transaction)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "pin": self._pin,
            "account": {
                "balance": str(self.account.balance),
            },
            "transactions": [
                transaction.to_dict()
                for transaction in self.transactions
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        account_data = data.get("account", {})

        account = Account(
            Decimal(account_data.get("balance", "0.00"))
        )

        transactions = [
            Transaction.from_dict(transaction)
            for transaction in data.get("transactions", [])
        ]

        return cls(
            user_id=data["user_id"],
            name=data["name"],
            pin=data["pin"],
            account=account,
            transactions=transactions,
        )