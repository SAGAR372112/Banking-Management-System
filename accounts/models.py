"""BankAccount model."""
import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from branches.models import Branch
from users.models import User


class BankAccount(models.Model):
    """
    Represents a bank account owned by a customer.

    Account number is auto-generated via signal.
    balance uses Decimal for precision (never float for money).
    select_for_update() must be used before modifying balance.
    """

    class AccountType(models.TextChoices):
        SAVINGS = "savings", "Savings"
        CURRENT = "current", "Current"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        FROZEN = "frozen", "Frozen"

    account_number = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    account_type = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.SAVINGS)
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="bank_accounts", db_index=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="accounts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["account_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.account_number} ({self.account_type}) - {self.customer.username}"

    def is_operable(self) -> bool:
        """Return True if account can send/receive funds."""
        return self.status == self.Status.ACTIVE

    def generate_account_number(self) -> str:
        """Generate a unique account number using UUID-based approach."""
        return f"ACC{uuid.uuid4().hex[:10].upper()}"

    def save(self, *args, **kwargs) -> None:
        if not self.account_number:
            for _ in range(10):
                candidate = self.generate_account_number()
                if not BankAccount.objects.filter(account_number=candidate).exists():
                    self.account_number = candidate
                    break
            else:
                raise ValueError("Failed to generate unique account number.")
        super().save(*args, **kwargs)
