# MiniATM

A modular terminal-based ATM simulation written in Python.

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

The project follows a layered architecture:

```
Presentation (CLI, menus)
    ↓
Application (Services)
    ↓
Domain (Models)
    ↓
Infrastructure (Storage)
```

### Directory Structure

```
MiniATM/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore patterns
├── README.md              # This file
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

2. Install dependencies:
```bash
python -m pip install -r requirements.txt
```

## Usage

### Running the Application

Start the ATM application:
```bash
python main.py
```

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
- No network security
- No audit logging beyond transaction history
- No rate limiting on authentication (beyond the 3-attempt CLI retry)

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

The project currently has **66 passing tests** covering:

- Domain models (Account, Transaction, User)
- Application services (AuthService, ATMService, TransactionService)
- Infrastructure (JSONStorage, UserRepository)
- Input validation (validators)
- Custom exceptions

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
