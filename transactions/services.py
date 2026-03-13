"""
Service layer for financial operations.

All balance mutations go through here to ensure:
  - Atomicity (django.db.transaction.atomic)
  - Concurrency safety (select_for_update)
  - Consistent validation
"""
import logging
from functools import partial
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .notifications import (
    notify_deposit,
    notify_transfer_receiver,
    notify_transfer_sender,
    notify_withdrawal,
)



from accounts.models import BankAccount
from .models import Transaction

logger = logging.getLogger("bank")

# Maximum single-transaction amount
MAX_TRANSACTION_AMOUNT = Decimal("1_000_000.00")


class InsufficientFundsError(Exception):
    """Raised when an account has insufficient balance."""

    def __init__(self, message: str, balance: Decimal):
        super().__init__(f"{message} Balance: {balance:.2f}")
        self._balance = balance

    @property
    def balance(self) -> str:
        return f"{self._balance:.2f}"


class AccountNotOperableError(Exception):
    """Raised when an account is frozen or inactive."""
    def __init__(self, message: str, status: str):
        super().__init__(f"{message} Status: {status}")
        self._status = status

    @property
    def status(self) -> str:
        return self._status


class DailyLimitExceededError(Exception):
    """Raised when the daily transfer limit would be exceeded."""
    def __init__(self, message: str, limit: Decimal):
        super().__init__(f"{message} Limit: {limit:.2f}")
        self._limit = limit

    @property
    def limit(self) -> str:
        return f"{self._limit:.2f}"


class InvalidTransactionError(Exception):
    """Raised for business-rule violations (e.g. same account transfer)."""
    def __init__(self, message: str):
        super().__init__(f"Invalid transaction: {message}")


def _validate_account_operable(account: BankAccount, role: str = "source") -> None:
    """Raise AccountNotOperableError if account is not active."""
    if not account.is_operable():
        raise AccountNotOperableError(
            f"The {role} account ({account.account_number}) is {account.status} and cannot process transactions."
        )


def _check_daily_limit(account: BankAccount, amount: Decimal) -> None:
    """
    Ensure the account has not exceeded the daily transfer/withdrawal limit.
    Uses today's completed outgoing transaction sum.
    """
    limit = Decimal(str(getattr(settings, "DAILY_TRANSFER_LIMIT", 50_000)))
    today = timezone.now().date()
    daily_total = (
        Transaction.objects.filter(
            Q(from_account=account),
            status=Transaction.TransactionStatus.COMPLETED,
            timestamp__date=today,
            type__in=[Transaction.TransactionType.WITHDRAWAL, Transaction.TransactionType.TRANSFER],
        ).aggregate(total=__import__("django.db.models", fromlist=["Sum"]).Sum("amount"))["total"]
        or Decimal("0.00")
    )
    if daily_total + amount > limit:
        raise DailyLimitExceededError(
            f"Daily limit of {limit} exceeded. Used: {daily_total}, Requested: {amount}."
        )


@transaction.atomic
def process_deposit(account_id: int, amount: Decimal, reference: str = "") -> Transaction:
    """
    Deposit funds into an account.

    Locks the account row with select_for_update() to prevent race conditions.
    """
    account = BankAccount.objects.select_for_update().get(pk=account_id)
    _validate_account_operable(account, "destination")

    if amount > MAX_TRANSACTION_AMOUNT:
        raise InvalidTransactionError(f"Amount exceeds maximum transaction limit of {MAX_TRANSACTION_AMOUNT}.")

    txn = Transaction.objects.create(
        type=Transaction.TransactionType.DEPOSIT,
        amount=amount,
        to_account=account,
        reference=reference,
        status=Transaction.TransactionStatus.PENDING,
    )

    try:
        account.balance += amount
        account.save(update_fields=["balance", "updated_at"])
        txn.status = Transaction.TransactionStatus.COMPLETED
        txn.save(update_fields=["status"])
        logger.info("Deposit completed: txn=%s account=%s amount=%s", 
            txn.transaction_id, 
            account.account_number, 
            amount
        )

        # Schedule email AFTER the DB transaction commits — never fires on rollback
        customer = account.customer
        if customer.email:
            transaction.on_commit(partial(
                notify_deposit,
                recipient_email=customer.email,
                recipient_name=customer.get_full_name() or customer.username,
                account_number=account.account_number,
                amount=amount,
                new_balance=account.balance,
                transaction_id=str(txn.transaction_id),
                reference=reference,
                timestamp=txn.timestamp,
            ))
    except Exception as exc:
        txn.status = Transaction.TransactionStatus.FAILED
        txn.metadata["error"] = str(exc)
        txn.save(update_fields=["status", "metadata"])
        logger.exception("Deposit failed: txn=%s", txn.transaction_id)
        raise

    return txn


@transaction.atomic
def process_withdrawal(account_id: int, amount: Decimal, reference: str = "") -> Transaction:
    """
    Withdraw funds from an account.

    Validates sufficient balance and daily limits before deducting.
    """
    account = BankAccount.objects.select_for_update().get(pk=account_id)
    _validate_account_operable(account, "source")

    if amount > MAX_TRANSACTION_AMOUNT:
        raise InvalidTransactionError(f"Amount exceeds maximum transaction limit of {MAX_TRANSACTION_AMOUNT}.")

    if account.balance < amount:
        raise InsufficientFundsError(
        "Insufficient balance for withdrawal.",
        account.balance
    )

    _check_daily_limit(account, amount)

    txn = Transaction.objects.create(
        type=Transaction.TransactionType.WITHDRAWAL,
        amount=amount,
        from_account=account,
        reference=reference,
        status=Transaction.TransactionStatus.PENDING,
    )

    try:
        account.balance -= amount
        account.save(update_fields=["balance", "updated_at"])
        txn.status = Transaction.TransactionStatus.COMPLETED
        txn.save(update_fields=["status"])
        logger.info("Withdrawal completed: txn=%s account=%s amount=%s", 
            txn.transaction_id, 
            account.account_number, 
            amount
        )

        customer = account.customer
        if customer.email:
            transaction.on_commit(partial(
                notify_withdrawal,
                recipient_email=customer.email,
                recipient_name=customer.get_full_name() or customer.username,
                account_number=account.account_number,
                amount=amount,
                new_balance=account.balance,
                transaction_id=str(txn.transaction_id),
                reference=reference,
                timestamp=txn.timestamp,
            ))
    except Exception as exc:
        txn.status = Transaction.TransactionStatus.FAILED
        txn.metadata["error"] = str(exc)
        txn.save(update_fields=["status", "metadata"])
        logger.exception("Withdrawal failed: txn=%s", txn.transaction_id)
        raise

    return txn


@transaction.atomic
def process_transfer(from_account_id: int, to_account_id: int, amount: Decimal, reference: str = "") -> Transaction:
    """
    Transfer funds between two accounts atomically.

    Locks both accounts using ordered IDs to prevent deadlocks.
    """
    if from_account_id == to_account_id:
        raise InvalidTransactionError("Source and destination accounts must be different.")

    if amount > MAX_TRANSACTION_AMOUNT:
        raise InvalidTransactionError(f"Amount exceeds maximum transaction limit of {MAX_TRANSACTION_AMOUNT}.")

    # Lock accounts in consistent order (lower PK first) to avoid deadlocks
    low_id, high_id = sorted([from_account_id, to_account_id])
    locked = {
        acc.pk: acc
        for acc in BankAccount.objects.select_for_update().filter(pk__in=[low_id, high_id])
    }

    if len(locked) < 2:
        raise InvalidTransactionError("One or both accounts not found.")

    from_account = locked[from_account_id]
    to_account = locked[to_account_id]

    _validate_account_operable(from_account, "source")
    _validate_account_operable(to_account, "destination")

    if from_account.balance < amount:
        raise InsufficientFundsError(
            f"Insufficient balance. Available: {from_account.balance}, Requested: {amount}."
        )

    _check_daily_limit(from_account, amount)

    txn = Transaction.objects.create(
        type=Transaction.TransactionType.TRANSFER,
        amount=amount,
        from_account=from_account,
        to_account=to_account,
        reference=reference,
        status=Transaction.TransactionStatus.PENDING,
    )

    try:
        from_account.balance -= amount
        to_account.balance += amount
        BankAccount.objects.bulk_update([from_account, to_account], ["balance", "updated_at"])
        txn.status = Transaction.TransactionStatus.COMPLETED
        txn.save(update_fields=["status"])
        logger.info(
            "Transfer completed: txn=%s from=%s to=%s amount=%s",
            txn.transaction_id, from_account.account_number, to_account.account_number, amount,
        )
        sender = from_account.customer
        if sender.email:
            transaction.on_commit(partial(
                notify_transfer_sender,
                recipient_email=sender.email,
                recipient_name=sender.get_full_name() or sender.username,
                from_account_number=from_account.account_number,
                to_account_number=to_account.account_number,
                amount=amount,
                new_balance=from_account.balance,
                transaction_id=str(txn.transaction_id),
                reference=reference,
                timestamp=txn.timestamp,
            ))

        # Notify receiver (only if different person from sender)
        receiver = to_account.customer
        if receiver.email and receiver.pk != sender.pk:
            transaction.on_commit(partial(
                notify_transfer_receiver,
                recipient_email=receiver.email,
                recipient_name=receiver.get_full_name() or receiver.username,
                from_account_number=from_account.account_number,
                to_account_number=to_account.account_number,
                amount=amount,
                new_balance=to_account.balance,
                transaction_id=str(txn.transaction_id),
                reference=reference,
                timestamp=txn.timestamp,
            ))
    except Exception as exc:
        txn.status = Transaction.TransactionStatus.FAILED
        txn.metadata["error"] = str(exc)
        txn.save(update_fields=["status", "metadata"])
        logger.exception("Transfer failed: txn=%s", txn.transaction_id)
        raise

    return txn
