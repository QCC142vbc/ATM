from datetime import datetime
from decimal import Decimal
import json

from backend.domain.transaction import Transaction
from backend.domain.user import User


def test_transaction_ids_are_unique():
    first = Transaction("deposit", Decimal("20"), Decimal("20"))
    second = Transaction("deposit", Decimal("20"), Decimal("40"))

    assert first.transaction_id
    assert first.transaction_id != second.transaction_id


def test_transaction_serialization_roundtrip():
    timestamp = datetime(2026, 9, 25, 10, 30)
    transaction = Transaction(
        "transfer_sent",
        Decimal("150.25"),
        Decimal("849.75"),
        timestamp=timestamp,
        user_id="user001",
        counterparty_id="user002",
        counterparty_name="Recipient",
        description="Shared bill",
        transfer_id="transfer-123",
    )

    restored = Transaction.from_dict(transaction.to_dict())

    assert restored.transaction_id == transaction.transaction_id
    assert restored.transaction_type == "transfer_sent"
    assert restored.timestamp == timestamp
    assert restored.user_id == "user001"
    assert restored.counterparty_id == "user002"
    assert restored.counterparty_name == "Recipient"
    assert restored.description == "Shared bill"
    assert restored.transfer_id == "transfer-123"
    assert restored.status == "completed"


def test_legacy_transaction_record_loads_with_generated_id():
    legacy = {
        "transaction_type": "deposit",
        "amount": "100",
        "balance_after": "100",
        "timestamp": "2026-09-25T10:30:00",
    }

    transaction = Transaction.from_dict(legacy)

    assert transaction.transaction_id
    assert transaction.counterparty_id is None
    assert transaction.status == "completed"


def test_user_persists_transaction_metadata(tmp_path):
    user = User("user001", "Test User", "1234")
    transaction = Transaction("transfer_received", Decimal("150"), Decimal("150"), user_id="user001")
    user.add_transaction(transaction)
    path = tmp_path / "users.json"
    from backend.infrastructure.json_storage import JSONStorage
    from backend.infrastructure.repositories import UserRepository

    repository = UserRepository(JSONStorage(str(path)))
    repository.save(user)

    restored = repository.get_by_id("user001")
    assert restored.transactions[0].transaction_id == transaction.transaction_id
    assert restored.transactions[0].user_id == "user001"


def test_legacy_transaction_id_is_migrated_once_and_remains_stable(tmp_path):
    path = tmp_path / "legacy-users.json"
    path.write_text(
        json.dumps([{
            "user_id": "user001",
            "name": "Legacy User",
            "pin": "1234",
            "transactions": [{
                "transaction_type": "deposit",
                "amount": "50",
                "balance_after": "50",
                "timestamp": "2026-09-25T10:30:00",
            }],
        }]),
        encoding="utf-8",
    )
    from backend.infrastructure.json_storage import JSONStorage
    from backend.infrastructure.repositories import UserRepository

    repository = UserRepository(JSONStorage(str(path)))
    first_id = repository.get_by_id("user001").transactions[0].transaction_id
    second_id = UserRepository(JSONStorage(str(path))).get_by_id("user001").transactions[0].transaction_id

    assert first_id == second_id
