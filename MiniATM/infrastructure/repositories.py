from domain.user import User


class UserRepository:
    def __init__(self, storage):
        self.storage = storage

    def get_all(self) -> list[User]:
        data = self.storage.load_users()

        return [
            User.from_dict(user_data)
            for user_data in data
        ]

    def get_by_id(self, user_id: str) -> User | None:
        users = self.get_all()

        for user in users:
            if user.user_id == user_id:
                return user

        return None

    def save(self, user: User) -> None:
        users = self.get_all()

        for index, existing_user in enumerate(users):
            if existing_user.user_id == user.user_id:
                users[index] = user
                self._save_all(users)
                return

        users.append(user)
        self._save_all(users)

    def _save_all(self, users: list[User]) -> None:
        data = [
            user.to_dict()
            for user in users
        ]

        self.storage.save_users(data)