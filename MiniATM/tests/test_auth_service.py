import pytest

from application.auth_service import AuthService


class FakeUser:
    def __init__(self, user_id: str, pin: str):
        self.user_id = user_id
        self.pin = pin

    def verify_pin(self, pin: str) -> bool:
        return self.pin == pin


class FakeUserRepository:
    def __init__(self, users):
        self.users = users

    def get_by_id(self, user_id: str):
        for user in self.users:
            if user.user_id == user_id:
                return user

        return None


def test_login_with_correct_pin():
    user = FakeUser("user001", "1234")
    repository = FakeUserRepository([user])

    auth_service = AuthService(repository)

    result = auth_service.login("user001", "1234")

    assert result == user


def test_login_with_wrong_pin():
    user = FakeUser("user001", "1234")
    repository = FakeUserRepository([user])

    auth_service = AuthService(repository)

    with pytest.raises(ValueError, match="Maximum login attempts exceeded"):
        auth_service.login("user001", "9999")


def test_login_with_unknown_user():
    repository = FakeUserRepository([])

    auth_service = AuthService(repository)

    with pytest.raises(ValueError, match="User not found"):
        auth_service.login("unknown", "1234")