from decimal import Decimal, InvalidOperation


def validate_user_id(user_id: str) -> str:
    """Validate user ID is a non-empty string."""
    if not user_id or not user_id.strip():
        raise ValueError("User ID cannot be empty")
    return user_id.strip()


def validate_pin(pin: str) -> str:
    """Validate PIN is a 4-digit string."""
    if not pin or not pin.strip():
        raise ValueError("PIN cannot be empty")
    
    pin = pin.strip()
    
    if not pin.isdigit():
        raise ValueError("PIN must contain only digits")
    
    if len(pin) != 4:
        raise ValueError("PIN must be exactly 4 digits")
    
    return pin


def validate_amount(amount: str) -> Decimal:
    """Validate amount string and convert to Decimal."""
    if not amount or not amount.strip():
        raise ValueError("Amount cannot be empty")
    
    try:
        decimal_amount = Decimal(amount.strip())
    except InvalidOperation:
        raise ValueError("Invalid amount format")
    
    if decimal_amount <= 0:
        raise ValueError("Amount must be greater than zero")
    
    return decimal_amount


def validate_non_empty_string(value: str, field_name: str) -> str:
    """Validate a string is non-empty."""
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    return value.strip()
