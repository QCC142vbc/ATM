from decimal import Decimal

import pytest

from domain.account import Account
from domain.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
)


def test_account_starts_with_zero_balance():
    account = Account()

    assert account.balance == Decimal("0.00")


def test_account_can_deposit():
    account = Account(Decimal("100.00"))

    account.deposit(Decimal("50.00"))

    assert account.balance == Decimal("150.00")


def test_account_can_withdraw():
    account = Account(Decimal("100.00"))

    account.withdraw(Decimal("40.00"))

    assert account.balance == Decimal("60.00")


def test_deposit_rejects_zero():
    account = Account()

    with pytest.raises(InvalidAmountError):
        account.deposit(Decimal("0"))


def test_deposit_rejects_negative_amount():
    account = Account()

    with pytest.raises(InvalidAmountError):
        account.deposit(Decimal("-10"))


def test_withdraw_rejects_zero():
    account = Account(Decimal("100.00"))

    with pytest.raises(InvalidAmountError):
        account.withdraw(Decimal("0"))


def test_withdraw_rejects_negative_amount():
    account = Account(Decimal("100.00"))

    with pytest.raises(InvalidAmountError):
        account.withdraw(Decimal("-10"))


def test_withdraw_rejects_insufficient_funds():
    account = Account(Decimal("100.00"))

    with pytest.raises(InsufficientFundsError):
        account.withdraw(Decimal("150.00"))

    assert account.balance == Decimal("100.00")