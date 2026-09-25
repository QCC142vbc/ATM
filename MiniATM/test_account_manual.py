from decimal import Decimal

from domain.account import Account


account = Account(Decimal("1000.00"))

print(account.balance)

account.deposit(Decimal("500.00"))
print(account.balance)

account.withdraw(Decimal("200.00"))
print(account.balance)