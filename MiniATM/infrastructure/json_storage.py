import json
from pathlib import Path


class JSONStorage:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load_users(self) -> list[dict]:
        if not self.file_path.exists():
            return []

        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return data

    def save_users(self, users: list[dict]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(
                users,
                file,
                indent=4,
                ensure_ascii=False,
            )