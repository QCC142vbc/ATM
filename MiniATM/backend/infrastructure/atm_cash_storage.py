import json
import os
from pathlib import Path
import tempfile

from backend.domain.exceptions import DataCorruptionError


class ATMCashStorage:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load_inventory(self) -> dict[int, int] | None:
        if not self.file_path.exists():
            return None
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
            if not isinstance(raw, dict):
                raise ValueError("Inventory must be an object.")
            inventory = {int(denomination): count for denomination, count in raw.items()}
            if any(
                not isinstance(count, int) or isinstance(count, bool) or count < 0
                for count in inventory.values()
            ):
                raise ValueError("Banknote counts must be non-negative integers.")
            return inventory
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise DataCorruptionError("ATM cash inventory is invalid.") from exc

    def save_inventory(self, inventory: dict[int, int]) -> None:
        if any(
            not isinstance(count, int) or isinstance(count, bool) or count < 0
            for count in inventory.values()
        ):
            raise ValueError("Banknote counts must be non-negative integers.")
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
                json.dump(
                    {str(denomination): count for denomination, count in inventory.items()},
                    file,
                    indent=2,
                )
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.file_path)
        except OSError:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
