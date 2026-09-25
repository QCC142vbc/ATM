from decimal import Decimal

import pytest

from backend.domain.validators import (
    validate_amount,
    validate_non_empty_string,
    validate_pin,
    validate_user_id,
)


def test_validate_user_id_valid():
    assert validate_user_id("user001") == "user001"
    assert validate_user_id("  user001  ") == "user001"


def test_validate_user_id_empty():
    with pytest.raises(ValueError, match="User ID cannot be empty"):
        validate_user_id("")
    
    with pytest.raises(ValueError, match="User ID cannot be empty"):
        validate_user_id("   ")


def test_validate_pin_valid():
    assert validate_pin("1234") == "1234"
    assert validate_pin("  1234  ") == "1234"


def test_validate_pin_empty():
    with pytest.raises(ValueError, match="PIN cannot be empty"):
        validate_pin("")
    
    with pytest.raises(ValueError, match="PIN cannot be empty"):
        validate_pin("   ")


def test_validate_pin_non_digit():
    with pytest.raises(ValueError, match="PIN must contain only digits"):
        validate_pin("12a4")
    
    with pytest.raises(ValueError, match="PIN must contain only digits"):
        validate_pin("abcd")


def test_validate_pin_wrong_length():
    with pytest.raises(ValueError, match="PIN must be exactly 4 digits"):
        validate_pin("123")
    
    with pytest.raises(ValueError, match="PIN must be exactly 4 digits"):
        validate_pin("12345")


def test_validate_amount_valid():
    assert validate_amount("100") == Decimal("100")
    assert validate_amount("  100  ") == Decimal("100")
    assert validate_amount("50.50") == Decimal("50.50")
    assert validate_amount("10.01") == Decimal("10.01")
    assert validate_amount("11") == Decimal("11")


def test_validate_amount_empty():
    with pytest.raises(ValueError, match="Amount cannot be empty"):
        validate_amount("")
    
    with pytest.raises(ValueError, match="Amount cannot be empty"):
        validate_amount("   ")


def test_validate_amount_invalid_format():
    with pytest.raises(ValueError, match="Invalid amount format"):
        validate_amount("abc")
    
    with pytest.raises(ValueError, match="Invalid amount format"):
        validate_amount("12.34.56")


def test_validate_amount_zero_or_negative():
    with pytest.raises(ValueError, match="Amount must be greater than 10"):
        validate_amount("0")
    
    with pytest.raises(ValueError, match="Amount must be greater than 10"):
        validate_amount("-10")
    
    with pytest.raises(ValueError, match="Amount must be greater than 10"):
        validate_amount("-5.50")


def test_validate_amount_boundary_cases():
    with pytest.raises(ValueError, match="Amount must be greater than 10"):
        validate_amount("5")
    
    with pytest.raises(ValueError, match="Amount must be greater than 10"):
        validate_amount("10")
    
    # 10.01 should be valid
    assert validate_amount("10.01") == Decimal("10.01")


def test_validate_non_empty_string_valid():
    assert validate_non_empty_string("Test", "Name") == "Test"
    assert validate_non_empty_string("  Test  ", "Name") == "Test"


def test_validate_non_empty_string_empty():
    with pytest.raises(ValueError, match="Name cannot be empty"):
        validate_non_empty_string("", "Name")
    
    with pytest.raises(ValueError, match="Name cannot be empty"):
        validate_non_empty_string("   ", "Name")
