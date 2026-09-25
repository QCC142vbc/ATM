import json
from pathlib import Path

from backend.domain.exceptions import DataCorruptionError


class JSONStorage:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load_users(self) -> list[dict]:
        if not self.file_path.exists():
            return []

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise DataCorruptionError(
                f"Corrupted data file: {self.file_path}. "
                f"Error: {error.msg}"
            )

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