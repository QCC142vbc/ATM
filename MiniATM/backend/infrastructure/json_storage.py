import json
import os
from pathlib import Path
import tempfile

from backend.domain.exceptions import DataCorruptionError


class JSONStorage:
    def __init__(self, file_path: str | Path):
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

        if not isinstance(data, list) or any(not isinstance(user, dict) for user in data):
            raise DataCorruptionError(
                f"Invalid data structure in file: {self.file_path}."
            )

        return data

    def save_users(self, users: list[dict]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.file_path.parent,
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                json.dump(users, file, indent=4, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.file_path)
        except OSError:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise