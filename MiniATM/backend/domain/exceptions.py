class ATMError(Exception):
    """Base exception for Mini ATM errors."""


class InvalidAmountError(ATMError):
    """Raised when a transaction amount is invalid."""


class InsufficientFundsError(ATMError):
    """Raised when an account does not have enough money."""


class DataCorruptionError(ATMError):
    """Raised when stored data is corrupted or unreadable."""


class AccountUnavailableError(ATMError):
    """Raised when an account is not active."""


class TransactionLimitError(ATMError):
    """Raised when an operation exceeds configured transaction limits."""