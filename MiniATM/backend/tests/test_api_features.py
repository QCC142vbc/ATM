from decimal import Decimal

from fastapi.testclient import TestClient

from backend.api import account_routes, atm_routes, auth_routes, transaction_routes, transfer_routes
from backend.api.app import create_app
from backend.application.atm_service import ATMService
from backend.application.auth_service import AuthService
from backend.application.banknote_service import ATMWithdrawalService
from backend.application.transaction_limits import TransactionLimits
from backend.application.transaction_service import TransactionService
from backend.application.transfer_service import TransferService
from backend.domain.account import Account
from backend.domain.user import User
from backend.infrastructure.atm_cash_storage import ATMCashStorage
from backend.infrastructure.json_storage import JSONStorage
from backend.infrastructure.repositories import UserRepository


def make_client(tmp_path, monkeypatch):
    repository = UserRepository(JSONStorage(str(tmp_path / "users.json")))
    sender = User("user001", "Sender", "1234")
    sender.account.deposit(Decimal("500"))
    receiver = User("user002", "Receiver", "5678")
    repository.save_many([sender, receiver])
    limits = TransactionLimits()
    transaction_service = TransactionService(repository)
    atm_service = ATMService(repository, transaction_service, limits)

    monkeypatch.setattr(auth_routes, "user_repository", repository)
    monkeypatch.setattr(auth_routes, "auth_service", AuthService(repository))
    monkeypatch.setattr(account_routes, "user_repository", repository)
    monkeypatch.setattr(account_routes, "transaction_service", transaction_service)
    monkeypatch.setattr(account_routes, "atm_service", atm_service)
    monkeypatch.setattr(transaction_routes, "transaction_service", transaction_service)
    monkeypatch.setattr(transfer_routes, "user_repository", repository)
    monkeypatch.setattr(transfer_routes, "transfer_service", TransferService(repository, limits))
    monkeypatch.setattr(
        atm_routes,
        "atm_withdrawal_service",
        ATMWithdrawalService(
            atm_service,
            ATMCashStorage(str(tmp_path / "atm_cash.json")),
            {100: 2, 50: 2, 20: 2, 10: 2},
        ),
    )

    return TestClient(create_app()), repository


def login(client):
    response = client.post("/api/auth/login", json={"user_id": "user001", "pin": "1234"})
    assert response.status_code == 200


def test_api_requires_session_and_returns_non_sensitive_account_data(tmp_path, monkeypatch):
    client, _ = make_client(tmp_path, monkeypatch)

    assert client.get("/api/account").status_code == 401
    login(client)
    response = client.get("/api/account")

    assert response.status_code == 200
    assert response.json()["user_id"] == "user001"
    assert response.json()["status"] == Account.ACTIVE
    assert response.json()["transaction_count"] == 0
    assert response.json()["limits"]["max_withdrawal"] == "1000"
    assert "pin" not in response.text.lower()


def test_transfer_api_creates_sender_and_receiver_history(tmp_path, monkeypatch):
    client, repository = make_client(tmp_path, monkeypatch)
    login(client)

    response = client.post(
        "/api/transfers",
        json={"recipient_id": "user002", "amount": "120", "description": "Utilities"},
    )

    assert response.status_code == 200
    assert response.json()["balance"] == "380.00"
    assert repository.get_by_id("user001").transactions[0].transaction_type == "transfer_sent"
    assert repository.get_by_id("user002").transactions[0].transaction_type == "transfer_received"
    history = client.get("/api/transactions").json()
    assert history[0]["transaction_id"]
    assert history[0]["counterparty_id"] == "user002"
    assert history[0]["description"] == "Utilities"
    assert history[0]["transfer_id"]
    recipient = repository.get_by_id("user002")
    assert recipient is not None
    recipient_history = recipient.transactions
    assert recipient_history[0].transfer_id == history[0]["transfer_id"]


def test_transfer_api_reports_validation_errors_without_changing_balances(tmp_path, monkeypatch):
    client, repository = make_client(tmp_path, monkeypatch)
    login(client)

    invalid_amount = client.post("/api/transfers", json={"recipient_id": "user002", "amount": "0"})
    self_transfer = client.post("/api/transfers", json={"recipient_id": "user001", "amount": "100"})
    missing_user = client.post("/api/transfers", json={"recipient_id": "missing", "amount": "100"})
    insufficient = client.post("/api/transfers", json={"recipient_id": "user002", "amount": "501"})

    assert invalid_amount.status_code == 400
    assert invalid_amount.json()["detail"]["error"]["code"] == "INVALID_AMOUNT"
    assert self_transfer.status_code == 400
    assert self_transfer.json()["detail"]["error"]["code"] == "SELF_TRANSFER"
    assert missing_user.status_code == 404
    assert missing_user.json()["detail"]["error"]["code"] == "USER_NOT_FOUND"
    assert insufficient.status_code == 400
    assert insufficient.json()["detail"]["error"]["code"] == "INSUFFICIENT_FUNDS"
    assert repository.get_by_id("user001").account.balance == Decimal("500.00")
    assert repository.get_by_id("user002").account.balance == Decimal("0.00")


def test_transfer_api_requires_authentication(tmp_path, monkeypatch):
    client, _ = make_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/transfers",
        json={"recipient_id": "user002", "amount": "120"},
    )

    assert response.status_code == 401


def test_authenticated_basic_banking_flow_updates_profile_and_history(tmp_path, monkeypatch):
    client, repository = make_client(tmp_path, monkeypatch)
    login(client)

    deposit = client.post("/api/account/deposit", json={"amount": "50"})
    withdrawal = client.post("/api/account/withdraw", json={"amount": "20"})
    transfer = client.post(
        "/api/transfers",
        json={"recipient_id": "user002", "amount": "100", "description": "Shared costs"},
    )

    assert deposit.status_code == 200
    assert withdrawal.status_code == 200
    assert transfer.status_code == 200
    assert transfer.json()["balance"] == "430.00"

    profile = client.get("/api/account").json()
    history = client.get("/api/transactions").json()
    assert len(history) == 3
    receiver = repository.get_by_id("user002")
    assert receiver is not None

    assert profile["balance"] == "430.00"
    assert profile["transaction_count"] == 3
    assert [transaction["transaction_type"] for transaction in history] == [
        "deposit",
        "withdrawal",
        "transfer_sent",
    ]
    assert history[-1]["transfer_id"] == receiver.transactions[0].transfer_id
    assert receiver.account.balance == Decimal("100.00")


def test_account_endpoints_do_not_allow_user_id_impersonation(tmp_path, monkeypatch):
    client, _ = make_client(tmp_path, monkeypatch)
    login(client)

    response = client.get("/api/account")
    assert response.json()["user_id"] == "user001"
    assert client.get("/api/account/user002").status_code == 404


def test_locked_account_cannot_use_existing_session(tmp_path, monkeypatch):
    client, repository = make_client(tmp_path, monkeypatch)
    login(client)
    user = repository.get_by_id("user001")
    user.account.status = Account.LOCKED
    repository.save(user)

    response = client.get("/api/account")
    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "ACCOUNT_UNAVAILABLE"


def test_pin_change_validates_and_does_not_return_pin(tmp_path, monkeypatch):
    client, repository = make_client(tmp_path, monkeypatch)
    login(client)

    mismatch = client.post(
        "/api/auth/change-pin",
        json={"current_pin": "1234", "new_pin": "9876", "confirm_pin": "0000"},
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["detail"]["error"]["code"] == "PIN_CONFIRMATION_MISMATCH"

    wrong = client.post(
        "/api/auth/change-pin",
        json={"current_pin": "0000", "new_pin": "9876", "confirm_pin": "9876"},
    )
    assert wrong.status_code == 400
    assert wrong.json()["detail"]["error"]["code"] == "INVALID_CURRENT_PIN"

    success = client.post(
        "/api/auth/change-pin",
        json={"current_pin": "1234", "new_pin": "9876", "confirm_pin": "9876"},
    )
    assert success.status_code == 200
    assert "9876" not in success.text
    assert repository.get_by_id("user001").verify_pin("9876")

    old_login = TestClient(create_app()).post(
        "/api/auth/login", json={"user_id": "user001", "pin": "1234"}
    )
    assert old_login.status_code == 401


def test_atm_withdrawal_api_dispenses_notes_and_updates_inventory(tmp_path, monkeypatch):
    client, repository = make_client(tmp_path, monkeypatch)
    login(client)

    response = client.post("/api/atm/withdraw", json={"amount": "270"})

    assert response.status_code == 200
    assert response.json()["balance"] == "230.00"
    assert response.json()["banknotes"] == {"100": 2, "50": 1, "20": 1}
    assert repository.get_by_id("user001").transactions[0].description == "ATM cash withdrawal"
    assert client.get("/api/atm/cash").json()["total_cash"] == "90"


def test_locked_account_login_is_rejected(tmp_path, monkeypatch):
    client, repository = make_client(tmp_path, monkeypatch)
    user = repository.get_by_id("user001")
    user.account.status = Account.LOCKED
    repository.save(user)

    response = client.post("/api/auth/login", json={"user_id": "user001", "pin": "1234"})

    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "ACCOUNT_UNAVAILABLE"
