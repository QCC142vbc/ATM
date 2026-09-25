import json
from datetime import datetime
from decimal import Decimal
from shutil import copyfile

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.application.atm_service import ATMService
from backend.application.transaction_service import TransactionService
from backend.application.transfer_service import TransferService
from backend.infrastructure.json_storage import JSONStorage
from backend.infrastructure.paths import USERS_FILE
from backend.infrastructure.repositories import UserRepository
from domain.account import Account as CLIAccount
from domain.transaction import Transaction as CLITransaction
from domain.user import User as CLIUser
from infrastructure.json_storage import JSONStorage as CLIJSONStorage
from infrastructure.repositories import UserRepository as CLIUserRepository
from backend.domain.account import Account
from backend.domain.transaction import Transaction
from backend.domain.user import User
import main as cli_main


def test_cli_compatibility_modules_share_backend_implementations():
    assert CLIAccount is Account
    assert CLITransaction is Transaction
    assert CLIUser is User
    assert CLIJSONStorage is JSONStorage
    assert CLIUserRepository is UserRepository


def test_cli_uses_the_canonical_dataset(monkeypatch):
    captured = {}

    class CapturingCLI:
        def __init__(self, auth_service, atm_service, transaction_service):
            captured["services"] = (auth_service, atm_service, transaction_service)

        def run(self):
            captured["ran"] = True

    monkeypatch.setattr(cli_main, "CLI", CapturingCLI)

    cli_main.main()

    auth_service, atm_service, transaction_service = captured["services"]
    repository = auth_service.user_repository
    assert captured["ran"]
    assert repository.storage.file_path == USERS_FILE
    assert len(repository.get_all()) >= 500
    assert atm_service.user_repository is repository
    assert transaction_service.user_repository is repository


def test_canonical_dataset_has_unique_users_and_current_schema(tmp_path):
    raw_users = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    copied_file = tmp_path / "users.json"
    copyfile(USERS_FILE, copied_file)
    repository = UserRepository(JSONStorage(copied_file))
    users = repository.get_all()

    assert len(raw_users) >= 500
    assert len(users) == len(raw_users)
    assert len({user.user_id for user in users}) == len(users)
    assert len({user.user_id for user in users}) == len(
        {raw_user["user_id"] for raw_user in raw_users}
    )
    assert {user.account.status for user in users} <= {
        Account.ACTIVE,
        Account.LOCKED,
        Account.SUSPENDED,
    }
    assert all(
        transaction.transaction_id
        for user in users
        for transaction in user.transactions
    )
    assert repository.get_by_id(users[-1].user_id) is not None


def test_transaction_write_preserves_all_records_in_canonical_format(tmp_path):
    raw_users = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    copied_file = tmp_path / "users.json"
    copyfile(USERS_FILE, copied_file)
    repository = UserRepository(JSONStorage(copied_file))
    before_ids = {user["user_id"] for user in raw_users}
    active_record = next(
        user for user in raw_users
        if user.get("account", {}).get("status") == Account.ACTIVE
    )
    before_count = len(active_record["transactions"])
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)

    atm_service.deposit(active_record["user_id"], Decimal("25"))

    saved_users = json.loads(copied_file.read_text(encoding="utf-8"))
    saved_record = next(user for user in saved_users if user["user_id"] == active_record["user_id"])
    saved_repository = UserRepository(JSONStorage(copied_file))
    saved_user = saved_repository.get_by_id(active_record["user_id"])
    assert saved_user is not None
    assert len(saved_users) == len(raw_users)
    assert {user["user_id"] for user in saved_users} == before_ids
    assert len(saved_record["transactions"]) == before_count + 1
    assert saved_record["transactions"][-1]["transaction_id"]
    assert saved_user.account.balance == Decimal(active_record["account"]["balance"]) + Decimal("25")
    assert saved_record["account"]["status"] == Account.ACTIVE


def test_banking_operations_and_statistics_use_full_dataset_schema(tmp_path):
    raw_users = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    active_users = [
        user for user in raw_users
        if user.get("account", {}).get("status") == Account.ACTIVE
    ]
    sender_record = next(
        user for user in active_users
        if Decimal(user["account"]["balance"]) >= Decimal("100")
        and sum(
            (
                Decimal(transaction["amount"])
                for transaction in user.get("transactions", [])
                if transaction["transaction_type"] == "withdrawal"
                and datetime.fromisoformat(transaction["timestamp"]).date()
                == datetime.now().date()
            ),
            Decimal("0"),
        ) <= Decimal("980")
        and sum(
            (
                Decimal(transaction["amount"])
                for transaction in user.get("transactions", [])
                if transaction["transaction_type"] == "transfer_sent"
                and datetime.fromisoformat(transaction["timestamp"]).date()
                == datetime.now().date()
            ),
            Decimal("0"),
        ) <= Decimal("2970")
    )
    recipient_record = next(
        user for user in active_users
        if user["user_id"] != sender_record["user_id"]
    )
    copied_file = tmp_path / "users.json"
    copyfile(USERS_FILE, copied_file)
    repository = UserRepository(JSONStorage(copied_file))
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service)
    transfer_service = TransferService(repository)
    sender_before = Decimal(sender_record["account"]["balance"])
    recipient_before = Decimal(recipient_record["account"]["balance"])

    atm_service.deposit(sender_record["user_id"], Decimal("25"))
    atm_service.withdraw(sender_record["user_id"], Decimal("20"))
    transfer_service.transfer(
        sender_record["user_id"],
        recipient_record["user_id"],
        Decimal("30"),
        "Dataset integration",
    )

    sender = repository.get_by_id(sender_record["user_id"])
    recipient = repository.get_by_id(recipient_record["user_id"])
    assert sender is not None
    assert recipient is not None
    assert sender.account.balance == sender_before - Decimal("25")
    assert recipient.account.balance == recipient_before + Decimal("30")
    assert [item.transaction_type for item in sender.transactions[-3:]] == [
        "deposit",
        "withdrawal",
        "transfer_sent",
    ]
    assert recipient.transactions[-1].transaction_type == "transfer_received"
    assert sender.transactions[-1].transfer_id == recipient.transactions[-1].transfer_id
    assert [
        transaction.transaction_id
        for transaction in transaction_service.get_transactions(sender_record["user_id"])
    ] == [transaction.transaction_id for transaction in sender.transactions]
    assert len(repository.get_all()) == len(raw_users)


def test_canonical_dataset_supports_authenticated_profile_and_history():
    repository = UserRepository(JSONStorage(USERS_FILE))
    raw_users = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    active = next(
        user for user in raw_users
        if user.get("account", {}).get("status") == Account.ACTIVE
    )
    client = TestClient(app)

    login = client.post(
        "/api/auth/login",
        json={"user_id": active["user_id"], "pin": active["pin"]},
    )
    assert login.status_code == 200

    profile = client.get("/api/account")
    history = client.get("/api/transactions")

    assert profile.status_code == 200
    assert profile.json()["user_id"] == active["user_id"]
    assert profile.json()["name"] == active["name"]
    loaded_user = repository.get_by_id(active["user_id"])
    assert loaded_user is not None
    assert profile.json()["balance"] == str(loaded_user.account.balance)
    assert profile.json()["transaction_count"] == len(active["transactions"])
    assert "pin" not in profile.text.lower()
    assert history.status_code == 200
    assert len(history.json()) == len(active["transactions"])
    client.post("/api/auth/logout")
