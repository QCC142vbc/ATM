import json

import pytest

from backend.domain.exceptions import DataCorruptionError
from backend.infrastructure.json_storage import JSONStorage


def test_load_existing_file(tmp_path):
    file_path = tmp_path / "users.json"
    test_data = [{"user_id": "user001", "name": "Test"}]
    
    file_path.write_text(json.dumps(test_data), encoding="utf-8")
    
    storage = JSONStorage(str(file_path))
    result = storage.load_users()
    
    assert result == test_data


def test_load_nonexistent_file(tmp_path):
    file_path = tmp_path / "nonexistent.json"
    
    storage = JSONStorage(str(file_path))
    result = storage.load_users()
    
    assert result == []


def test_save_users(tmp_path):
    file_path = tmp_path / "users.json"
    test_data = [{"user_id": "user001", "name": "Test"}]
    
    storage = JSONStorage(str(file_path))
    storage.save_users(test_data)
    
    assert file_path.exists()
    
    with file_path.open("r", encoding="utf-8") as f:
        result = json.load(f)
    
    assert result == test_data


def test_save_creates_parent_directories(tmp_path):
    file_path = tmp_path / "subdir" / "nested" / "users.json"
    test_data = [{"user_id": "user001"}]
    
    storage = JSONStorage(str(file_path))
    storage.save_users(test_data)
    
    assert file_path.exists()
    
    with file_path.open("r", encoding="utf-8") as f:
        result = json.load(f)
    
    assert result == test_data


def test_save_unicode_content(tmp_path):
    file_path = tmp_path / "users.json"
    test_data = [{"user_id": "user001", "name": "Tëst Üsér"}]
    
    storage = JSONStorage(str(file_path))
    storage.save_users(test_data)
    
    with file_path.open("r", encoding="utf-8") as f:
        result = json.load(f)
    
    assert result == test_data


def test_save_overwrites_existing_file(tmp_path):
    file_path = tmp_path / "users.json"
    initial_data = [{"user_id": "old"}]
    new_data = [{"user_id": "new"}]
    
    storage = JSONStorage(str(file_path))
    storage.save_users(initial_data)
    storage.save_users(new_data)
    
    with file_path.open("r", encoding="utf-8") as f:
        result = json.load(f)
    
    assert result == new_data


def test_load_save_roundtrip(tmp_path):
    file_path = tmp_path / "users.json"
    original_data = [
        {
            "user_id": "user001",
            "name": "Test User",
            "pin": "1234",
            "account": {"balance": "1000.00"},
            "transactions": []
        }
    ]
    
    storage = JSONStorage(str(file_path))
    storage.save_users(original_data)
    loaded_data = storage.load_users()
    
    assert loaded_data == original_data


def test_load_malformed_json(tmp_path):
    file_path = tmp_path / "users.json"
    
    # Write corrupted JSON
    file_path.write_text("{invalid json content", encoding="utf-8")
    
    storage = JSONStorage(str(file_path))
    
    with pytest.raises(DataCorruptionError, match="Corrupted data file"):
        storage.load_users()
