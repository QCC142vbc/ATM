from backend.domain.user import User
from backend.domain.account import Account
from backend.domain.exceptions import AccountUnavailableError
from threading import RLock


class AuthService:
    def __init__(self, user_repository):
        self.user_repository = user_repository
        self._lock = getattr(user_repository, "transaction_lock", RLock())

    def login(self, user_id: str, pin: str) -> User:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found")

        if getattr(getattr(user, "account", None), "status", Account.ACTIVE) != Account.ACTIVE:
            raise AccountUnavailableError(
                f"Account is {user.account.status.lower()}."
            )

        if user.verify_pin(pin):
            return user

        raise ValueError("Invalid PIN")

    def change_pin(self, user_id: str, current_pin: str, new_pin: str) -> None:
        with self._lock:
            user = self.user_repository.get_by_id(user_id)
            if user is None:
                raise ValueError("User not found.")
            if user.account.status != Account.ACTIVE:
                raise AccountUnavailableError(
                    f"Account is {user.account.status.lower()}."
                )
            user.change_pin(current_pin, new_pin)
            self.user_repository.save(user)
