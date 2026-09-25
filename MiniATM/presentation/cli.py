from decimal import Decimal, InvalidOperation

from application.atm_service import ATMService
from application.auth_service import AuthService
from application.transaction_service import TransactionService

from presentation.menus import show_login_menu, show_main_menu


class CLI:
    def __init__(
        self,
        auth_service: AuthService,
        atm_service: ATMService,
        transaction_service: TransactionService,
    ):
        self.auth_service = auth_service
        self.atm_service = atm_service
        self.transaction_service = transaction_service
        self.current_user = None

    def run(self) -> None:
        print("Welcome to MiniATM!")

        if not self._login():
            return

        self._main_loop()

    def _login(self) -> bool:
        user_id, pin = show_login_menu()

        try:
            self.current_user = self.auth_service.login(user_id, pin)
            print("Login successful.")
            return True

        except ValueError as error:
            print(f"Login failed: {error}")
            return False

    def _main_loop(self) -> None:
        while self.current_user is not None:
            choice = show_main_menu()

            if choice == "1":
                self._show_balance()

            elif choice == "2":
                self._deposit()

            elif choice == "3":
                self._withdraw()

            elif choice == "4":
                self._show_transactions()

            elif choice == "5":
                self._logout()

            else:
                print("Invalid option.")

    def _show_balance(self) -> None:
        try:
            balance = self.atm_service.get_balance(
                self.current_user.user_id
            )

            print(f"Current balance: {balance}")

        except ValueError as error:
            print(f"Error: {error}")

    def _deposit(self) -> None:
        amount = self._read_amount("Deposit amount: ")

        if amount is None:
            return

        try:
            balance = self.atm_service.deposit(
                self.current_user.user_id,
                amount,
            )

            print(f"Deposit successful.")
            print(f"New balance: {balance}")

        except ValueError as error:
            print(f"Error: {error}")

    def _withdraw(self) -> None:
        amount = self._read_amount("Withdrawal amount: ")

        if amount is None:
            return

        try:
            balance = self.atm_service.withdraw(
                self.current_user.user_id,
                amount,
            )

            print("Withdrawal successful.")
            print(f"New balance: {balance}")

        except ValueError as error:
            print(f"Error: {error}")

    def _show_transactions(self) -> None:
        try:
            transactions = self.transaction_service.get_transactions(
                self.current_user.user_id
            )

            if not transactions:
                print("No transactions found.")
                return

            print("\n=== Transaction History ===")

            for transaction in transactions:
                print(
                    f"{transaction.timestamp} | "
                    f"{transaction.transaction_type} | "
                    f"{transaction.amount} | "
                    f"Balance: {transaction.balance_after}"
                )

        except ValueError as error:
            print(f"Error: {error}")

    def _read_amount(self, prompt: str) -> Decimal | None:
        value = input(prompt).strip()

        try:
            amount = Decimal(value)

        except InvalidOperation:
            print("Invalid amount.")
            return None

        return amount

    def _logout(self) -> None:
        self.current_user = None
        print("Logged out.")