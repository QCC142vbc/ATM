from decimal import Decimal

import pytest

from backend.application.atm_service import ATMService
from backend.application.transaction_service import TransactionService
from backend.application.transaction_limits import TransactionLimits
from backend.domain.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    TransactionLimitError,
)
from backend.domain.transaction import Transaction
from backend.domain.user import User


class FakeUserRepository:
    def __init__(self, user=None):
        self.user = user

    def get_by_id(self, user_id: str):
        if self.user and self.user.user_id == user_id:
            return self.user
        return None

    def save(self, user):
        self.user = user


def test_get_balance(tmp_path):
    user = User("user001", "Test User", "1234")
    user.account.deposit(Decimal("1000.00"))
    repository = FakeUserRepository(user)
    
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    balance = atm_service.get_balance("user001")
    
    assert balance == Decimal("1000.00")


def test_get_balance_unknown_user(tmp_path):
    repository = FakeUserRepository()
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    with pytest.raises(ValueError, match="User not found"):
        atm_service.get_balance("unknown")


def test_successful_deposit(tmp_path):
    user = User("user001", "Test User", "1234")
    repository = FakeUserRepository(user)
    
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    balance = atm_service.deposit("user001", Decimal("500.00"))
    
    assert balance == Decimal("500.00")
    assert user.account.balance == Decimal("500.00")
    assert len(user.transactions) == 1
    assert user.transactions[0].transaction_type == "deposit"


def test_deposit_updates_balance(tmp_path):
    user = User("user001", "Test User", "1234")
    user.account.deposit(Decimal("1000.00"))
    repository = FakeUserRepository(user)
    
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    balance = atm_service.deposit("user001", Decimal("500.00"))
    
    assert balance == Decimal("1500.00")
    assert user.account.balance == Decimal("1500.00")


def test_deposit_invalid_amount(tmp_path):
    user = User("user001", "Test User", "1234")
    repository = FakeUserRepository(user)
    
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    with pytest.raises(InvalidAmountError):
        atm_service.deposit("user001", Decimal("5.00"))
    
    assert user.account.balance == Decimal("0.00")
    assert len(user.transactions) == 0


def test_deposit_unknown_user(tmp_path):
    repository = FakeUserRepository()
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    with pytest.raises(ValueError, match="User not found"):
        atm_service.deposit("unknown", Decimal("500.00"))


def test_successful_withdrawal(tmp_path):
    user = User("user001", "Test User", "1234")
    user.account.deposit(Decimal("1000.00"))
    repository = FakeUserRepository(user)
    
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    balance = atm_service.withdraw("user001", Decimal("300.00"))
    
    assert balance == Decimal("700.00")
    assert user.account.balance == Decimal("700.00")
    assert len(user.transactions) == 1
    assert user.transactions[0].transaction_type == "withdrawal"


def test_withdrawal_of_exact_balance_is_allowed(tmp_path):
    user = User("user001", "Test User", "1234")
    user.account.deposit(Decimal("100"))
    repository = FakeUserRepository(user)
    atm_service = ATMService(repository, TransactionService(repository))

    balance = atm_service.withdraw("user001", Decimal("100"))

    assert balance == Decimal("0.00")
    assert len(user.transactions) == 1


def test_withdrawal_daily_limit_exact_boundary_and_overage(tmp_path):
    user = User("user001", "Test User", "1234")
    user.account.deposit(Decimal("300"))
    repository = FakeUserRepository(user)
    limits = TransactionLimits(
        max_withdrawal=Decimal("100"),
        daily_withdrawal=Decimal("100"),
    )
    atm_service = ATMService(repository, TransactionService(repository), limits)

    assert atm_service.withdraw("user001", Decimal("100")) == Decimal("200")
    with pytest.raises(TransactionLimitError):
        atm_service.withdraw("user001", Decimal("11"))


def test_withdrawal_insufficient_funds(tmp_path):
    user = User("user001", "Test User", "1234")
    user.account.deposit(Decimal("100.00"))
    repository = FakeUserRepository(user)
    
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    with pytest.raises(InsufficientFundsError):
        atm_service.withdraw("user001", Decimal("500.00"))
    
    assert user.account.balance == Decimal("100.00")
    assert len(user.transactions) == 0


def test_withdrawal_invalid_amount(tmp_path):
    user = User("user001", "Test User", "1234")
    user.account.deposit(Decimal("1000.00"))
    repository = FakeUserRepository(user)
    
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    with pytest.raises(InvalidAmountError):
        atm_service.withdraw("user001", Decimal("5.00"))
    
    assert user.account.balance == Decimal("1000.00")
    assert len(user.transactions) == 0


def test_withdrawal_unknown_user(tmp_path):
    repository = FakeUserRepository()
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    with pytest.raises(ValueError, match="User not found"):
        atm_service.withdraw("unknown", Decimal("500.00"))


def test_transaction_creation_on_deposit(tmp_path):
    user = User("user001", "Test User", "1234")
    repository = FakeUserRepository(user)
    
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    atm_service.deposit("user001", Decimal("500.00"))
    
    assert len(user.transactions) == 1
    transaction = user.transactions[0]
    assert transaction.transaction_type == "deposit"
    assert transaction.amount == Decimal("500.00")
    assert transaction.balance_after == Decimal("500.00")


def test_transaction_creation_on_withdrawal(tmp_path):
    user = User("user001", "Test User", "1234")
    user.account.deposit(Decimal("1000.00"))
    repository = FakeUserRepository(user)
    
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    atm_service.withdraw("user001", Decimal("300.00"))
    
    assert len(user.transactions) == 1
    transaction = user.transactions[0]
    assert transaction.transaction_type == "withdrawal"
    assert transaction.amount == Decimal("300.00")
    assert transaction.balance_after == Decimal("700.00")


def test_multiple_transactions(tmp_path):
    user = User("user001", "Test User", "1234")
    repository = FakeUserRepository(user)
    
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    
    atm_service.deposit("user001", Decimal("1000.00"))
    atm_service.withdraw("user001", Decimal("200.00"))
    atm_service.deposit("user001", Decimal("500.00"))
    
    assert len(user.transactions) == 3
    assert user.transactions[0].transaction_type == "deposit"
    assert user.transactions[1].transaction_type == "withdrawal"
    assert user.transactions[2].transaction_type == "deposit"
    assert user.account.balance == Decimal("1300.00")
