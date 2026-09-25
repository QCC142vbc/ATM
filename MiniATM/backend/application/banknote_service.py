from decimal import Decimal
from threading import RLock

from backend.domain.exceptions import ATMError


class InvalidBanknoteWithdrawalError(ATMError):
    """Raised when the ATM cannot dispense an exact valid banknote combination."""


class BanknoteService:
    DENOMINATIONS = (100, 50, 20, 10)

    @classmethod
    def calculate_dispense(
        cls,
        amount: Decimal,
        inventory: dict[int, int],
    ) -> dict[int, int]:
        amount = Decimal(amount)
        if not amount.is_finite() or amount != amount.to_integral_value():
            raise InvalidBanknoteWithdrawalError(
                "ATM withdrawals must be a whole-euro amount."
            )
        remaining = int(amount)
        if remaining <= 0:
            raise InvalidBanknoteWithdrawalError("Withdrawal amount must be positive.")
        denominations = cls.DENOMINATIONS

        def search(index: int, left: int) -> dict[int, int] | None:
            if left == 0:
                return {}
            if index == len(denominations):
                return None
            denomination = denominations[index]
            maximum_count = min(inventory.get(denomination, 0), left // denomination)
            for count in range(maximum_count, -1, -1):
                result = search(index + 1, left - count * denomination)
                if result is not None:
                    if count:
                        result[denomination] = count
                    return result
            return None

        notes = search(0, remaining)
        if notes is None:
            raise InvalidBanknoteWithdrawalError(
                "The ATM cannot dispense that exact amount with its current cash."
            )
        return notes


class ATMWithdrawalService:
    def __init__(self, atm_service, cash_storage, initial_inventory: dict[int, int] | None = None):
        self.atm_service = atm_service
        self.cash_storage = cash_storage
        self._lock = RLock()
        self.initial_inventory = initial_inventory or {
            100: 12,
            50: 18,
            20: 31,
            10: 24,
        }

    def get_inventory(self) -> dict[int, int]:
        inventory = self.cash_storage.load_inventory()
        return self.initial_inventory.copy() if inventory is None else inventory

    def total_cash(self) -> int:
        return sum(denomination * count for denomination, count in self.get_inventory().items())

    def withdraw(self, user_id: str, amount: Decimal) -> tuple[Decimal, dict[int, int]]:
        with self._lock:
            inventory = self.get_inventory()
            notes = BanknoteService.calculate_dispense(amount, inventory)
            updated = inventory.copy()
            for denomination, count in notes.items():
                updated[denomination] -= count

            self.cash_storage.save_inventory(updated)
            try:
                balance = self.atm_service.withdraw(
                    user_id,
                    amount,
                    description="ATM cash withdrawal",
                )
            except Exception:
                try:
                    self.cash_storage.save_inventory(inventory)
                except OSError as rollback_error:
                    raise RuntimeError(
                        "Unable to restore ATM cash inventory after a failed withdrawal."
                    ) from rollback_error
                raise
            return balance, notes
