from domain.user import User

class UserRepository:
    def __init__(self):
        self.storage = storage
    def get_all(self) -> list[User]:
        return self.storage.load_users()
    def get_by_id(self, user_id: str) -> User | None:
        for user in self.get_all():
            if user.id == user_id:
                return user
        return None

    def save(self, user: User) -> None:
        users = self.get_all()
        
        for index, existing_user in enumerate(users):
            if existing_user.id == user.id:
                users[index] = user
                self.storage.save_users(users)
                return
        
        users.append(user)
        
        self.storage.save_users(users)
