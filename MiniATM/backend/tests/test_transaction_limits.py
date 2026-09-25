from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from backend.application.transaction_limits import TransactionLimits
from backend.domain.exceptions import TransactionLimitError
from backend.domain.transaction import Transaction


def test_withdrawal_exact_daily_limit_is_allowed():
    limits = TransactionLimits(
        max_withdrawal=Decimal("500"),
        daily_withdrawal=Decimal("300"),
    )
    limits.check_withdrawal(Decimal("300"), [])


def test_withdrawal_above_single_or_daily_limit_is_rejected():
    limits = TransactionLimits(
        max_withdrawal=Decimal("500"),
        daily_withdrawal=Decimal("300"),
    )
    with pytest.raises(TransactionLimitError, match="per transaction"):
        limits.check_withdrawal(Decimal("501"), [])

    earlier = Transaction("withdrawal", Decimal("200"), Decimal("800"))
    with pytest.raises(TransactionLimitError, match="Daily withdrawal"):
        limits.check_withdrawal(Decimal("101"), [earlier])


def test_only_today_completed_withdrawals_count():
    limits = TransactionLimits(daily_withdrawal=Decimal("300"))
    yesterday = Transaction(
        "withdrawal",
        Decimal("300"),
        Decimal("700"),
        timestamp=datetime.combine(datetime.now().date() - timedelta(days=1), datetime.min.time()),
    )
    limits.check_withdrawal(Decimal("300"), [yesterday])


def test_invalid_configured_limits_are_rejected():
    with pytest.raises(ValueError, match="finite positive"):
        TransactionLimits(max_transfer=Decimal("0"))


def test_deposit_single_limit_exact_boundary_is_allowed():
    limits = TransactionLimits(max_deposit=Decimal("500"))
    limits.check_deposit(Decimal("500"))
    with pytest.raises(TransactionLimitError, match="per transaction"):
        limits.check_deposit(Decimal("500.01"))
