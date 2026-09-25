from decimal import Decimal

from domain.account import Account


class ATMService:
    def __init__(self, user_repository, transaction_service):
        self.user_repository = user_repository
        self.transaction_service = transaction_service

    def get_balance(self, user_id: str) -> Decimal:
        user = self._get_user(user_id)

        return user.account.get_balance()

    def deposit(self, user_id: str, amount: Decimal) -> Decimal:
        user = self._get_user(user_id)

        user.account.deposit(amount)

        balance_after = user.account.get_balance()

        self.user_repository.save(user)

        self.transaction_service.record_deposit(
            user_id,
            amount,
            balance_after,
        )

        return balance_after

    def withdraw(self, user_id: str, amount: Decimal) -> Decimal:
        user = self._get_user(user_id)

        user.account.withdraw(amount)

        balance_after = user.account.get_balance()

        self.user_repository.save(user)

        self.transaction_service.record_withdrawal(
            user_id,
            amount,
            balance_after,
        )

        return balance_after

    def _get_user(self, user_id: str):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        return user