from infrastructure.json_storage import JSONStorage
from infrastructure.repositories import UserRepository

from application.auth_service import AuthService
from application.atm_service import ATMService
from application.transaction_service import TransactionService

from backend.infrastructure.paths import USERS_FILE
from presentation.cli import CLI


def main() -> None:
    storage = JSONStorage(USERS_FILE)
    user_repository = UserRepository(storage)

    auth_service = AuthService(user_repository)

    transaction_service = TransactionService(user_repository)

    atm_service = ATMService(
        user_repository,
        transaction_service,
    )

    cli = CLI(
        auth_service=auth_service,
        atm_service=atm_service,
        transaction_service=transaction_service,
    )

    cli.run()


if __name__ == "__main__":
    main()