from domain.user import User

class AuthService:
    MAX_ATTEMPTS = 3

    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def login(self, user_id: str, pin: str) -> User:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found")

        for _ in range(self.MAX_ATTEMPTS):
            if user.verify_pin(pin):
                return user

            # The CLI will handle asking for another PIN later.

        raise ValueError("Maximum login attempts exceeded")
