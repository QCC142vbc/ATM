from backend.domain.user import User
from backend.domain.exceptions import DataCorruptionError
from threading import RLock


class UserRepository:
    transaction_lock = RLock()

    def __init__(self, storage):
        self.storage = storage

    def get_all(self) -> list[User]:
        with self.transaction_lock:
            data = self.storage.load_users()
            try:
                users = [User.from_dict(user_data) for user_data in data]
            except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
                raise DataCorruptionError(
                    f"Invalid user record in file: {self.storage.file_path}."
                ) from exc
            user_ids = [user.user_id for user in users]
            if len(user_ids) != len(set(user_ids)):
                raise DataCorruptionError(
                    f"Duplicate user IDs in file: {self.storage.file_path}."
                )
            has_legacy_transactions = any(
                not transaction_data.get("transaction_id")
                for user_data in data
                for transaction_data in user_data.get("transactions", [])
            )
            if has_legacy_transactions:
                self._save_all(users)
            return users

    def get_by_id(self, user_id: str) -> User | None:
        users = self.get_all()

        for user in users:
            if user.user_id == user_id:
                return user

        return None

    def save(self, user: User) -> None:
        self.save_many([user])

    def save_many(self, changed_users: list[User]) -> None:
        with self.transaction_lock:
            users = self.get_all()
            changed_by_id = {user.user_id: user for user in changed_users}
            persisted_ids = set()

            for index, existing_user in enumerate(users):
                if existing_user.user_id in changed_by_id:
                    users[index] = changed_by_id[existing_user.user_id]
                    persisted_ids.add(existing_user.user_id)

            users.extend(
                user
                for user in changed_users
                if user.user_id not in persisted_ids
            )
            self._save_all(users)

    def _save_all(self, users: list[User]) -> None:
        data = [
            user.to_dict()
            for user in users
        ]

        self.storage.save_users(data)