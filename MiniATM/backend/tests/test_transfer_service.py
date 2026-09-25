from decimal import Decimal

import pytest

from backend.application.transaction_limits import TransactionLimits
from backend.application.transfer_service import TransferService
from backend.domain.account import Account
from backend.domain.exceptions import (
    AccountUnavailableError,
    InsufficientFundsError,
    InvalidAmountError,
    TransactionLimitError,
)
from backend.domain.user import User
from backend.infrastructure.json_storage import JSONStorage
from backend.infrastructure.repositories import UserRepository


def create_repository(tmp_path):
    repository = UserRepository(JSONStorage(str(tmp_path / "users.json")))
    sender = User("user001", "Sender", "1234")
    receiver = User("user002", "Receiver", "5678")
    sender.account.deposit(Decimal("500"))
    repository.save_many([sender, receiver])
    return repository


def test_successful_transfer_creates_both_records_and_persists(tmp_path):
    repository = create_repository(tmp_path)
    service = TransferService(repository)

    sender_balance, receiver_balance, sent, received = service.transfer(
        "user001", "user002", Decimal("150"), "Rent"
    )

    assert sender_balance == Decimal("350")
    assert receiver_balance == Decimal("150")
    assert sent.transaction_type == "transfer_sent"
    assert received.transaction_type == "transfer_received"
    assert sent.transaction_id != received.transaction_id
    assert sent.transfer_id
    assert sent.transfer_id == received.transfer_id
    assert sent.counterparty_id == "user002"
    assert received.counterparty_id == "user001"
    assert sent.description == received.description == "Rent"

    persisted_sender = repository.get_by_id("user001")
    persisted_receiver = repository.get_by_id("user002")
    assert persisted_sender.account.balance == Decimal("350")
    assert persisted_receiver.account.balance == Decimal("150")
    assert persisted_sender.transactions[0].transaction_id == sent.transaction_id
    assert persisted_receiver.transactions[0].transaction_id == received.transaction_id
    assert persisted_sender.transactions[0].transfer_id == persisted_receiver.transactions[0].transfer_id


@pytest.mark.parametrize("amount", ["0", "-1", "10", "NaN", "Infinity"])
def test_invalid_amount_does_not_change_accounts(tmp_path, amount):
    repository = create_repository(tmp_path)
    service = TransferService(repository)

    with pytest.raises(InvalidAmountError):
        service.transfer("user001", "user002", Decimal(amount))

    assert repository.get_by_id("user001").account.balance == Decimal("500")
    assert repository.get_by_id("user002").account.balance == Decimal("0")


def test_transfer_to_missing_user_fails_without_saving(tmp_path):
    repository = create_repository(tmp_path)

    with pytest.raises(ValueError, match="Recipient account not found"):
        TransferService(repository).transfer("user001", "missing", Decimal("100"))

    assert repository.get_by_id("user001").account.balance == Decimal("500")


def test_self_transfer_fails(tmp_path):
    repository = create_repository(tmp_path)

    with pytest.raises(ValueError, match="own account"):
        TransferService(repository).transfer("user001", "user001", Decimal("100"))


def test_insufficient_funds_fails_without_saving(tmp_path):
    repository = create_repository(tmp_path)

    with pytest.raises(InsufficientFundsError):
        TransferService(repository).transfer("user001", "user002", Decimal("600"))

    assert repository.get_by_id("user001").account.balance == Decimal("500")
    assert repository.get_by_id("user002").account.balance == Decimal("0")


def test_transfer_limit_boundary(tmp_path):
    repository = create_repository(tmp_path)
    limits = TransactionLimits(max_transfer=Decimal("200"), daily_transfer=Decimal("200"))

    TransferService(repository, limits).transfer("user001", "user002", Decimal("200"))
    assert repository.get_by_id("user001").account.balance == Decimal("300")

    with pytest.raises(TransactionLimitError):
        TransferService(repository, limits).transfer("user001", "user002", Decimal("11"))


def test_transfer_single_limit_exact_boundary_and_overage(tmp_path):
    repository = create_repository(tmp_path)
    limits = TransactionLimits(max_transfer=Decimal("100"), daily_transfer=Decimal("300"))
    service = TransferService(repository, limits)

    service.transfer("user001", "user002", Decimal("100"))
    service.transfer("user001", "user002", Decimal("100"))
    with pytest.raises(TransactionLimitError, match="per transaction"):
        service.transfer("user001", "user002", Decimal("101"))


def test_transfer_rejects_locked_recipient(tmp_path):
    repository = create_repository(tmp_path)
    recipient = repository.get_by_id("user002")
    recipient.account.status = Account.LOCKED
    repository.save(recipient)

    with pytest.raises(AccountUnavailableError):
        TransferService(repository).transfer("user001", "user002", Decimal("100"))


def test_failed_atomic_write_keeps_both_balances_unchanged(tmp_path, monkeypatch):
    repository = create_repository(tmp_path)
    original_save = repository.storage.save_users

    def fail_save(_users):
        raise OSError("disk write failed")

    monkeypatch.setattr(repository.storage, "save_users", fail_save)
    with pytest.raises(OSError, match="disk write failed"):
        TransferService(repository).transfer("user001", "user002", Decimal("100"))

    monkeypatch.setattr(repository.storage, "save_users", original_save)
    assert repository.get_by_id("user001").account.balance == Decimal("500")
    assert repository.get_by_id("user002").account.balance == Decimal("0")
