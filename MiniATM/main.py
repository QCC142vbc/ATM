from infrastructure.json_storage import JSONStorage
from infrastructure.repositories import UserRepository

from application.auth_service import AuthService
from application.atm_service import ATMService

from presentation.cli import CLI


def main() -> None:
    storage = JSONStorage("data/users.json")
    user_repository = UserRepository(storage)

    auth_service = AuthService(user_repository)
    atm_service = ATMService(user_repository)

    cli = CLI(
        auth_service=auth_service,
        atm_service=atm_service,
    )

    cli.run()


if __name__ == "__main__":
    main()