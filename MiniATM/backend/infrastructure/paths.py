from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"
ATM_CASH_FILE = DATA_DIR / "atm_cash.json"
