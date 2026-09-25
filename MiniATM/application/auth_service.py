from domain.user import User


class AuthService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def login(self, user_id: str, pin: str) -> User:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found")

        if user.verify_pin(pin):
            return user

        raise ValueError("Invalid PIN")
