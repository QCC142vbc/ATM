from decimal import Decimal

from domain.account import Account
from domain.transaction import Transaction
from domain.user import User


def test_user_creation():
    user = User("user001", "Test User", "1234")
    
    assert user.user_id == "user001"
    assert user.name == "Test User"
    assert user.verify_pin("1234") is True
    assert user.account.balance == Decimal("0.00")
    assert user.transactions == []


def test_user_with_account():
    account = Account(Decimal("1000.00"))
    user = User("user001", "Test User", "1234", account)
    
    assert user.account.balance == Decimal("1000.00")


def test_user_with_transactions():
    user = User("user001", "Test User", "1234")
    transaction = Transaction("deposit", Decimal("500"), Decimal("500"))
    
    user.add_transaction(transaction)
    
    assert len(user.transactions) == 1
    assert user.transactions[0] == transaction


def test_pin_verification_correct():
    user = User("user001", "Test User", "1234")
    
    assert user.verify_pin("1234") is True


def test_pin_verification_incorrect():
    user = User("user001", "Test User", "1234")
    
    assert user.verify_pin("9999") is False


def test_user_to_dict():
    user = User("user001", "Test User", "1234")
    user.account.deposit(Decimal("500"))
    transaction = Transaction("deposit", Decimal("500"), Decimal("500"))
    user.add_transaction(transaction)
    
    data = user.to_dict()
    
    assert data["user_id"] == "user001"
    assert data["name"] == "Test User"
    assert data["pin"] == "1234"
    assert data["account"]["balance"] == "500.00"
    assert len(data["transactions"]) == 1
    assert data["transactions"][0]["transaction_type"] == "deposit"


def test_user_from_dict():
    data = {
        "user_id": "user001",
        "name": "Test User",
        "pin": "1234",
        "account": {
            "balance": "1000.00"
        },
        "transactions": [
            {
                "transaction_type": "deposit",
                "amount": "500",
                "balance_after": "1500.00",
                "timestamp": "2026-09-25T21:17:10.814902"
            }
        ]
    }
    
    user = User.from_dict(data)
    
    assert user.user_id == "user001"
    assert user.name == "Test User"
    assert user.verify_pin("1234") is True
    assert user.account.balance == Decimal("1000.00")
    assert len(user.transactions) == 1
    assert user.transactions[0].transaction_type == "deposit"


def test_user_from_dict_without_account():
    data = {
        "user_id": "user001",
        "name": "Test User",
        "pin": "1234"
    }
    
    user = User.from_dict(data)
    
    assert user.account.balance == Decimal("0.00")


def test_user_from_dict_without_transactions():
    data = {
        "user_id": "user001",
        "name": "Test User",
        "pin": "1234",
        "account": {
            "balance": "1000.00"
        }
    }
    
    user = User.from_dict(data)
    
    assert len(user.transactions) == 0


def test_user_serialization_roundtrip():
    original = User("user001", "Test User", "1234")
    original.account.deposit(Decimal("500"))
    transaction = Transaction("deposit", Decimal("500"), Decimal("500"))
    original.add_transaction(transaction)
    
    data = original.to_dict()
    restored = User.from_dict(data)
    
    assert restored.user_id == original.user_id
    assert restored.name == original.name
    assert restored.verify_pin("1234") is True
    assert restored.account.balance == original.account.balance
    assert len(restored.transactions) == len(original.transactions)
