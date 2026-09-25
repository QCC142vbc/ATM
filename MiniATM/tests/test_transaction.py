from decimal import Decimal

from application.transaction_service import TransactionService
from domain.user import User


class FakeUserRepository:
    def __init__(self, user):
        self.user = user

    def get_by_id(self, user_id: str):
        if self.user.user_id == user_id:
            return self.user

        return None

    def save(self, user):
        self.user = user


def test_record_deposit():
    user = User("user001", "Test User", "1234")
    repository = FakeUserRepository(user)

    service = TransactionService(repository)

    transaction = service.record_deposit(
        user,
        Decimal("500.00"),
        Decimal("1500.00"),
    )

    assert transaction.transaction_type == "deposit"
    assert transaction.amount == Decimal("500.00")
    assert transaction.balance_after == Decimal("1500.00")

    assert len(user.transactions) == 1
    assert user.transactions[0] == transaction


def test_record_withdrawal():
    user = User("user001", "Test User", "1234")
    repository = FakeUserRepository(user)

    service = TransactionService(repository)

    transaction = service.record_withdrawal(
        user,
        Decimal("200.00"),
        Decimal("800.00"),
    )

    assert transaction.transaction_type == "withdrawal"
    assert transaction.amount == Decimal("200.00")
    assert transaction.balance_after == Decimal("800.00")

    assert len(user.transactions) == 1


def test_get_transactions():
    user = User("user001", "Test User", "1234")
    repository = FakeUserRepository(user)

    service = TransactionService(repository)

    service.record_deposit(
        user,
        Decimal("500.00"),
        Decimal("1500.00"),
    )

    service.record_withdrawal(
        user,
        Decimal("200.00"),
        Decimal("1300.00"),
    )

    transactions = service.get_transactions("user001")

    assert len(transactions) == 2
    assert transactions[0].transaction_type == "deposit"
    assert transactions[1].transaction_type == "withdrawal"