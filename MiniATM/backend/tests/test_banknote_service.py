from decimal import Decimal

import pytest

from backend.application.banknote_service import (
    ATMWithdrawalService,
    BanknoteService,
    InvalidBanknoteWithdrawalError,
)
from backend.domain.exceptions import InsufficientFundsError
from backend.infrastructure.atm_cash_storage import ATMCashStorage


def test_calculate_dispense_prefers_larger_notes():
    notes = BanknoteService.calculate_dispense(
        Decimal("270"),
        {100: 2, 50: 2, 20: 2, 10: 2},
    )
    assert notes == {100: 2, 50: 1, 20: 1}


def test_calculate_dispense_finds_combination_when_greedy_would_fail():
    notes = BanknoteService.calculate_dispense(
        Decimal("60"),
        {100: 0, 50: 1, 20: 3, 10: 0},
    )
    assert notes == {20: 3}


@pytest.mark.parametrize("amount", ["0", "15", "10.50", "NaN"])
def test_calculate_dispense_rejects_invalid_or_impossible_amounts(amount):
    with pytest.raises(InvalidBanknoteWithdrawalError):
        BanknoteService.calculate_dispense(
            Decimal(amount),
            {100: 1, 50: 1, 20: 1, 10: 1},
        )


def test_atm_withdrawal_updates_and_persists_inventory(tmp_path):
    class ATM:
        def withdraw(self, user_id, amount, description=None):
            assert user_id == "user001"
            assert description == "ATM cash withdrawal"
            return Decimal("230")

    storage = ATMCashStorage(str(tmp_path / "cash.json"))
    service = ATMWithdrawalService(ATM(), storage, {100: 2, 50: 1, 20: 1, 10: 1})

    balance, notes = service.withdraw("user001", Decimal("270"))

    assert balance == Decimal("230")
    assert notes == {100: 2, 50: 1, 20: 1}
    assert storage.load_inventory() == {100: 0, 50: 0, 20: 0, 10: 1}


def test_failed_account_withdrawal_restores_inventory(tmp_path):
    class ATM:
        def withdraw(self, user_id, amount, description=None):
            raise InsufficientFundsError("Insufficient funds")

    storage = ATMCashStorage(str(tmp_path / "cash.json"))
    original = {100: 1, 50: 1, 20: 1, 10: 1}
    service = ATMWithdrawalService(ATM(), storage, original)

    with pytest.raises(InsufficientFundsError):
        service.withdraw("user001", Decimal("100"))

    assert storage.load_inventory() == original
