from decimal import Decimal, InvalidOperation
from threading import RLock
from uuid import uuid4

from backend.application.transaction_limits import TransactionLimits
from backend.domain.account import Account
from backend.domain.exceptions import (
    AccountUnavailableError,
    InvalidAmountError,
    InsufficientFundsError,
)
from backend.domain.transaction import Transaction


class TransferService:
    def __init__(self, user_repository, limits: TransactionLimits | None = None):
        self.user_repository = user_repository
        self.limits = limits or TransactionLimits()
        self._lock = getattr(user_repository, "transaction_lock", RLock())

    def transfer(
        self,
        sender_id: str,
        recipient_id: str,
        amount: Decimal,
        description: str | None = None,
    ) -> tuple[Decimal, Decimal, Transaction, Transaction]:
        with self._lock:
            return self._transfer(sender_id, recipient_id, amount, description)

    def _transfer(
        self,
        sender_id: str,
        recipient_id: str,
        amount: Decimal,
        description: str | None,
    ) -> tuple[Decimal, Decimal, Transaction, Transaction]:
        try:
            amount = Decimal(amount)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise InvalidAmountError("Enter a valid transfer amount.") from exc
        if not amount.is_finite() or amount <= 10:
            raise InvalidAmountError("Transfer amount must be greater than 10.")
        if sender_id == recipient_id:
            raise ValueError("You cannot transfer money to your own account.")

        sender = self.user_repository.get_by_id(sender_id)
        recipient = self.user_repository.get_by_id(recipient_id)
        if sender is None:
            raise ValueError("Sender account not found.")
        if recipient is None:
            raise ValueError("Recipient account not found.")
        if sender.account.status != Account.ACTIVE:
            raise AccountUnavailableError(f"Sender account is {sender.account.status.lower()}.")
        if recipient.account.status != Account.ACTIVE:
            raise AccountUnavailableError(f"Recipient account is {recipient.account.status.lower()}.")
        if amount > sender.account.balance:
            raise InsufficientFundsError("Insufficient funds.")
        self.limits.check_transfer(amount, sender.transactions)

        sender.account.withdraw(amount)
        recipient.account.deposit(amount)
        transfer_id = str(uuid4())
        sent = Transaction(
            "transfer_sent",
            amount,
            sender.account.balance,
            user_id=sender.user_id,
            counterparty_id=recipient.user_id,
            counterparty_name=recipient.name,
            description=description,
            transfer_id=transfer_id,
        )
        received = Transaction(
            "transfer_received",
            amount,
            recipient.account.balance,
            user_id=recipient.user_id,
            counterparty_id=sender.user_id,
            counterparty_name=sender.name,
            description=description,
            transfer_id=transfer_id,
        )
        sender.add_transaction(sent)
        recipient.add_transaction(received)

        save_many = getattr(self.user_repository, "save_many", None)
        if save_many is None:
            raise RuntimeError("User repository must support atomic multi-user persistence.")
        save_many([sender, recipient])
        return sender.account.balance, recipient.account.balance, sent, received
