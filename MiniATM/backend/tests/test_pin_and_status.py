import pytest

from backend.application.auth_service import AuthService
from backend.domain.account import Account
from backend.domain.exceptions import AccountUnavailableError
from backend.domain.user import User


class Repository:
    def __init__(self, user):
        self.user = user

    def get_by_id(self, user_id):
        return self.user if self.user.user_id == user_id else None

    def save(self, user):
        self.user = user


def test_change_pin_requires_old_pin_and_persists():
    user = User("user001", "Test User", "1234")
    repository = Repository(user)
    AuthService(repository).change_pin("user001", "1234", "9876")
    assert repository.user.verify_pin("9876")
    assert not repository.user.verify_pin("1234")


@pytest.mark.parametrize("pin", ["123", "abcd", "12 4"])
def test_change_pin_rejects_invalid_new_pin(pin):
    with pytest.raises(ValueError, match="4 to 12 digits"):
        User("user001", "Test User", "1234").change_pin("1234", pin)


def test_change_pin_rejects_wrong_current_pin():
    with pytest.raises(ValueError, match="Current PIN"):
        User("user001", "Test User", "1234").change_pin("0000", "9876")


def test_login_rejects_locked_or_suspended_accounts():
    for status in (Account.LOCKED, Account.SUSPENDED):
        user = User("user001", "Test User", "1234")
        user.account.status = status
        with pytest.raises(AccountUnavailableError):
            AuthService(Repository(user)).login("user001", "1234")
