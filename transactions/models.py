"""Transaction model."""
import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Transaction(models.Model):
    """
    Immutable record of every financial operation.

    from_account / to_account are nullable to support:
      - deposit: to_account only
      - withdrawal: from_account only
      - transfer: both populated
    """

    class TransactionType(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        WITHDRAWAL = "withdrawal", "Withdrawal"
        TRANSFER = "transfer", "Transfer"

    class TransactionStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True, 
        editable=False, 
        db_index=True
    )
    type = models.CharField(
        max_length=20, 
        choices=TransactionType.choices, 
        db_index=True
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    from_account = models.ForeignKey(
        "accounts.BankAccount",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="outgoing_transactions",
    )
    to_account = models.ForeignKey(
        "accounts.BankAccount",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="incoming_transactions",
    )
    reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=TransactionStatus.choices, 
        default=TransactionStatus.PENDING, 
        db_index=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["from_account", "timestamp"]),
            models.Index(fields=["to_account", "timestamp"]),
            models.Index(fields=["status", "type"]),
        ]

    def __str__(self) -> str:
        return f"{self.type.upper()} {self.transaction_id} — {self.amount}"
