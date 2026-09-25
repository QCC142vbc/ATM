def show_main_menu() -> str:
    print("\n=== MiniATM ===")
    print("1. Check balance")
    print("2. Deposit")
    print("3. Withdraw")
    print("4. Transaction history")
    print("5. Logout")

    return input("Choose an option: ").strip()


def show_login_menu() -> tuple[str, str]:
    print("\n=== Login ===")

    user_id = input("User ID: ").strip()
    pin = input("PIN: ").strip()

    return user_id, pin