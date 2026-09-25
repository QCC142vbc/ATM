from decimal import Decimal


class Account:
    def __init__(self, balance: Decimal = Decimal("0.00")):
        self._balance = Decimal(balance)

    @property
    def balance(self) -> Decimal:
        return self._balance

    def deposit(self, amount: Decimal) -> None:
        amount = Decimal(amount)
        if amount <= 10:
            raise ValueError("Deposit amount must be greater than 10")
        self._balance += amount

    def withdraw(self, amount: Decimal) -> None:
        amount = Decimal(amount)
        if amount <= 10:
            raise ValueError("Withdrawal amount must be greater than 10")
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount

    def get_balance(self) -> Decimal:
        return self._balance