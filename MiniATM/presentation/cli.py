from application.atm_service import ATMService
from application.auth_service import AuthService

from presentation.menus import show_login_menu, show_main_menu


class CLI:
    def __init__(
        self,
        auth_service: AuthService,
        atm_service: ATMService,
    ):
        self.auth_service = auth_service
        self.atm_service = atm_service
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
        balance = self.atm_service.get_balance(
            self.current_user.user_id
        )

        print(f"Current balance: {balance}")

    def _deposit(self) -> None:
        print("Deposit functionality will be connected here.")

    def _withdraw(self) -> None:
        print("Withdrawal functionality will be connected here.")

    def _show_transactions(self) -> None:
        print("Transaction history will be connected here.")

    def _logout(self) -> None:
        self.current_user = None
        print("Logged out.")