from decimal import Decimal
from .exceptions import InvalidAmountError, InsufficientFundsError

class Account:
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    SUSPENDED = "SUSPENDED"

    def __init__(self, balance: Decimal = Decimal("0.00"), status: str = ACTIVE):
        if status not in {self.ACTIVE, self.LOCKED, self.SUSPENDED}:
            raise ValueError("Unsupported account status.")
        self._balance = Decimal(balance)
        self.status = status

    @property
    def balance(self) -> Decimal:
        return self._balance

    @staticmethod
    def validate_deposit_amount(amount: Decimal) -> Decimal:
        amount = Decimal(amount)
        if not amount.is_finite() or amount <= 10:
            raise InvalidAmountError("Deposit amount must be greater than 10")
        return amount

    @staticmethod
    def validate_withdrawal_amount(amount: Decimal) -> Decimal:
        amount = Decimal(amount)
        if not amount.is_finite() or amount <= 10:
            raise InvalidAmountError("Withdrawal amount must be greater than 10")
        return amount

    def deposit(self, amount: Decimal) -> None:
        self._balance += self.validate_deposit_amount(amount)

    def withdraw(self, amount: Decimal) -> None:
        amount = self.validate_withdrawal_amount(amount)
        if amount > self._balance:
            raise InsufficientFundsError("Insufficient funds")
        self._balance -= amount

    def get_balance(self) -> Decimal:
        return self._balance