class User:
    def __init__(self, user_id: str, pin: str):
        self.user_id = user_id
        self.pin = pin

    def verify_pin(self, pin: str) -> bool:
        return self.pin == pin