from decimal import Decimal

from backend.domain.transaction import Transaction
from backend.domain.user import User


class TransactionService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def record_deposit(
        self,
        user: User,
        amount: Decimal,
        balance_after: Decimal,
        description: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            transaction_type="deposit",
            amount=amount,
            balance_after=balance_after,
            user_id=user.user_id,
            description=description,
        )

        user.add_transaction(transaction)
        return transaction

    def record_withdrawal(
        self,
        user: User,
        amount: Decimal,
        balance_after: Decimal,
        description: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            transaction_type="withdrawal",
            amount=amount,
            balance_after=balance_after,
            user_id=user.user_id,
            description=description,
        )

        user.add_transaction(transaction)
        return transaction

    def get_transactions(self, user_id: str) -> list[Transaction]:
        user = self._get_user(user_id)

        return user.transactions

    def _get_user(self, user_id: str):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        return user