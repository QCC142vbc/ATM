# MiniATM

A modular ATM and banking simulation with a Python/FastAPI backend and React/Vite
frontend. The original CLI remains available for local terminal use.

## Features

- User authentication with PIN login
- Account balance checking
- Money deposits
- Money withdrawals
- Transaction history
- Multiple user support
- JSON data persistence
- Decimal-based monetary calculations
- Automated testing with pytest

## Architecture

The project has two entrypoints over layered implementations:

- `backend/` powers the web application. FastAPI routes call application
  services, which use domain models and infrastructure repositories.
- The root `application/`, `domain/`, `infrastructure/`, and `presentation/`
  packages power the preserved CLI entrypoint in `main.py`.

The implementations are intentionally separate so the web API can evolve
without breaking the existing terminal application.

### Directory Structure

```
MiniATM/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore patterns
├── README.md              # This file
│
├── backend/                # FastAPI web application and backend tests
│   ├── api/                # HTTP routes and sessions
│   ├── application/        # Web application services
│   ├── domain/             # Web domain models and rules
│   ├── infrastructure/     # JSON repositories and ATM cash storage
│   └── tests/               # Web/API test suite
│
├── frontend/               # React/Vite dashboard and ATM mode
│
├── application/           # Application layer
│   ├── __init__.py
│   ├── atm_service.py     # ATM operations (deposit, withdraw, balance)
│   ├── auth_service.py    # User authentication
│   └── transaction_service.py  # Transaction management
│
├── data/                  # Data storage
│   └── users.json         # User data (persisted)
│
├── domain/                # Domain layer
│   ├── __init__.py
│   ├── account.py         # Account model and business logic
│   ├── exceptions.py      # Custom domain exceptions
│   ├── transaction.py     # Transaction model
│   ├── user.py            # User model
│   └── validators.py      # Input validation functions
│
├── infrastructure/        # Infrastructure layer
│   ├── __init__.py
│   ├── json_storage.py    # JSON file storage
│   └── repositories.py    # Data repositories
│
├── presentation/          # Presentation layer
│   ├── __init__.py
│   ├── cli.py            # Command-line interface
│   └── menus.py          # Menu display functions
│
└── tests/                # Test suite
    ├── __init__.py
    ├── test_account.py
    ├── test_atm_service.py
    ├── test_auth_service.py
    ├── test_json_storage.py
    ├── test_transaction.py
    ├── test_user.py
    ├── test_user_repository.py
    └── test_validators.py
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/QCC142vbc/MiniATM.git
cd MiniATM
```

2. Install CLI dependencies:
```bash
python -m pip install -r requirements.txt
```

3. Install backend dependencies:
```bash
python -m pip install -r backend/requirements.txt
```

4. Install frontend dependencies:
```powershell
Set-Location frontend
npm install
```

## Usage

### Running the CLI Application

Start the ATM application:
```bash
python main.py
```

### Running MiniATM v2 (Web Application)

Start the API from the `MiniATM` project directory in one terminal:

```powershell
python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000
```

Start the React development server from `MiniATM\frontend` in another terminal:

```powershell
npm install
npm run dev
```

The browser uses same-origin `/api` URLs. Vite forwards those requests to the local
FastAPI server, so the API address is not exposed in the frontend bundle. For a
Cloudflare Quick Tunnel demo, keep both servers running and start:

```powershell
cloudflared tunnel --url http://localhost:5173
```

Open the generated `trycloudflare.com` URL. Vite is configured to accept Quick
Tunnel hostnames and bind to all interfaces for that development server.

MiniATM v2 includes transfers, searchable transaction details, profile/PIN
settings, account statuses, server-enforced limits, activity analytics, an ATM
mode, and a persisted banknote inventory. The backend remains authoritative for
all account operations. User/account data is stored in `backend/data/users.json`;
the simulated cash inventory is stored in `backend/data/atm_cash.json`.

Transaction limits are configurable through these environment variables:

| Variable | Default |
| --- | ---: |
| `MINIATM_MAX_WITHDRAWAL` | `1000` |
| `MINIATM_DAILY_WITHDRAWAL` | `1000` |
| `MINIATM_MAX_TRANSFER` | `1000` |
| `MINIATM_DAILY_TRANSFER` | `3000` |
| `MINIATM_MAX_DEPOSIT` | `5000` |

### Example Session

```
Welcome to MiniATM!
=== Login ===
User ID: user001
PIN: 1234
Login successful.
=== MiniATM ===
1. Check balance
2. Deposit
3. Withdraw
4. Transaction history
5. Logout
Choose an option: 1
Current balance: 1057.00
Choose an option: 2
Deposit amount: 100
Deposit successful.
New balance: 1157.00
Choose an option: 5
Logged out.
```

### Running Tests

Run the complete test suite:
```bash
python -m pytest -q
```

Run tests with verbose output:
```bash
python -m pytest -v
```

Run specific test files:
```bash
python -m pytest tests/test_account.py
python -m pytest tests/test_atm_service.py
```

## Test Data

The application includes a test user for demonstration purposes:

- **User ID**: `user001`
- **PIN**: `1234`
- **Name**: Test User

**Note**: This is educational/demo data. In a production environment, PINs should never be stored in plaintext.

## Limitations & Security Notes

This is an educational ATM simulation project. It is **not suitable for real financial use**.

### Known Limitations

- PINs are stored in plaintext in JSON files
- No encryption for sensitive data
- No real banking integration
- No card processing
- The web application and Quick Tunnel are for local demos only, not production banking
- No audit logging beyond transaction history
- Login attempts and sessions are held in process memory and are not shared across workers
- Transfer persistence is atomic for a single process/JSON file; this is not a multi-process banking ledger
- Simulated ATM cash and account balances are stored in separate JSON files, so a machine crash between writes is not a transactional database commit

### Transaction Rules

- **Minimum transaction amount**: 10.00 (deposits and withdrawals must be greater than 10)
- Transactions with amounts ≤ 10 will be rejected
- Withdrawals cannot exceed available balance
- All monetary calculations use Decimal for precision

### Security Recommendations for Future Development

- Implement PIN hashing (e.g., bcrypt, Argon2)
- Add encryption for data at rest
- Implement proper session management
- Add audit logging for security events
- Implement rate limiting
- Add input sanitization
- Use environment variables for configuration

## Technology Stack

- **Python**: 3.11+
- **Testing**: pytest
- **Data Persistence**: JSON
- **Monetary Calculations**: Decimal (for precision)

## Development

### Code Quality

The project follows these principles:

- Object-oriented programming
- Separation of concerns
- Domain-driven design elements
- Type hints
- Clean code practices
- Comprehensive test coverage

### Testing

Tests cover:

- Domain models (Account, Transaction, User)
- Application services (AuthService, ATMService, TransactionService)
- Infrastructure (JSONStorage, UserRepository)
- Input validation (validators)
- Transfers, transaction limits, PIN changes, account status, ATM banknote selection, and authenticated API flows

## Contributing

This is an educational project. Feel free to use it as a learning resource or extend it for educational purposes.

## License

This project is provided as-is for educational purposes.

## Acknowledgments

Designed as a learning project to demonstrate:
- Python OOP
- Modular architecture
- Separation of concerns
- Persistence strategies
- Exception handling
- Testing practices
- Clean code principles
