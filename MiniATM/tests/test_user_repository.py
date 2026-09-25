from decimal import Decimal

import pytest

from domain.user import User
from infrastructure.json_storage import JSONStorage
from infrastructure.repositories import UserRepository


def test_get_all_users(tmp_path):
    file_path = tmp_path / "users.json"
    storage = JSONStorage(str(file_path))
    repository = UserRepository(storage)
    
    user1 = User("user001", "User One", "1234")
    user2 = User("user002", "User Two", "5678")
    
    repository.save(user1)
    repository.save(user2)
    
    users = repository.get_all()
    
    assert len(users) == 2
    assert users[0].user_id == "user001"
    assert users[1].user_id == "user002"


def test_get_all_empty_repository(tmp_path):
    file_path = tmp_path / "users.json"
    storage = JSONStorage(str(file_path))
    repository = UserRepository(storage)
    
    users = repository.get_all()
    
    assert users == []


def test_get_by_id_existing_user(tmp_path):
    file_path = tmp_path / "users.json"
    storage = JSONStorage(str(file_path))
    repository = UserRepository(storage)
    
    user = User("user001", "Test User", "1234")
    repository.save(user)
    
    found_user = repository.get_by_id("user001")
    
    assert found_user is not None
    assert found_user.user_id == "user001"
    assert found_user.name == "Test User"


def test_get_by_id_unknown_user(tmp_path):
    file_path = tmp_path / "users.json"
    storage = JSONStorage(str(file_path))
    repository = UserRepository(storage)
    
    user = User("user001", "Test User", "1234")
    repository.save(user)
    
    found_user = repository.get_by_id("unknown")
    
    assert found_user is None


def test_save_new_user(tmp_path):
    file_path = tmp_path / "users.json"
    storage = JSONStorage(str(file_path))
    repository = UserRepository(storage)
    
    user = User("user001", "Test User", "1234")
    repository.save(user)
    
    found_user = repository.get_by_id("user001")
    
    assert found_user is not None
    assert found_user.user_id == "user001"


def test_update_existing_user(tmp_path):
    file_path = tmp_path / "users.json"
    storage = JSONStorage(str(file_path))
    repository = UserRepository(storage)
    
    user = User("user001", "Test User", "1234")
    repository.save(user)
    
    updated_user = User("user001", "Updated Name", "1234")
    updated_user.account.deposit(Decimal("500"))
    repository.save(updated_user)
    
    found_user = repository.get_by_id("user001")
    
    assert found_user.name == "Updated Name"
    assert found_user.account.balance == Decimal("500")


def test_save_updates_account_balance(tmp_path):
    file_path = tmp_path / "users.json"
    storage = JSONStorage(str(file_path))
    repository = UserRepository(storage)
    
    user = User("user001", "Test User", "1234")
    repository.save(user)
    
    user.account.deposit(Decimal("1000"))
    repository.save(user)
    
    found_user = repository.get_by_id("user001")
    
    assert found_user.account.balance == Decimal("1000")


def test_save_persists_transactions(tmp_path):
    file_path = tmp_path / "users.json"
    storage = JSONStorage(str(file_path))
    repository = UserRepository(storage)
    
    from domain.transaction import Transaction
    
    user = User("user001", "Test User", "1234")
    transaction = Transaction("deposit", Decimal("500"), Decimal("500"))
    user.add_transaction(transaction)
    repository.save(user)
    
    found_user = repository.get_by_id("user001")
    
    assert len(found_user.transactions) == 1
    assert found_user.transactions[0].transaction_type == "deposit"


def test_persistence_between_repository_instances(tmp_path):
    file_path = tmp_path / "users.json"
    
    repository1 = UserRepository(JSONStorage(str(file_path)))
    user = User("user001", "Test User", "1234")
    user.account.deposit(Decimal("1000"))
    repository1.save(user)
    
    repository2 = UserRepository(JSONStorage(str(file_path)))
    found_user = repository2.get_by_id("user001")
    
    assert found_user is not None
    assert found_user.account.balance == Decimal("1000")


def test_multiple_users_with_different_ids(tmp_path):
    file_path = tmp_path / "users.json"
    storage = JSONStorage(str(file_path))
    repository = UserRepository(storage)
    
    user1 = User("user001", "User One", "1234")
    user2 = User("user002", "User Two", "5678")
    user3 = User("user003", "User Three", "9012")
    
    repository.save(user1)
    repository.save(user2)
    repository.save(user3)
    
    assert repository.get_by_id("user001") is not None
    assert repository.get_by_id("user002") is not None
    assert repository.get_by_id("user003") is not None
    
    assert len(repository.get_all()) == 3
