"""Custom User model with role-based access control."""
import random
import string
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


def generate_account_number() -> str:
    """Generate a unique 10-digit account number."""
    return "".join(random.choices(string.digits, k=10))


class User(AbstractUser):
    """
    Extended Django User with banking-specific fields.

    Roles:
        - admin: Full access to all resources and branch management.
        - customer: Access limited to their own accounts.
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        CUSTOMER = "customer", "Customer"

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.CUSTOMER, 
        db_index=True
        )
    account_number = models.CharField(
        max_length=10, 
        unique=True, 
        blank=True, 
        editable=False
        )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r"^\+?[\d\s\-().]{7,20}$", "Enter a valid phone number.")],
    )
    address = models.TextField(blank=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["account_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs) -> None:
        """Auto-generate account number on first save."""
        if not self.account_number:
            self.account_number = self._generate_unique_account_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_unique_account_number() -> str:
        """Generate a unique account number, retrying on collision."""
        for _ in range(10):
            number = generate_account_number()
            if not User.objects.filter(account_number=number).exists():
                return number
        raise ValueError("Could not generate a unique account number after 10 attempts.")

    @property
    def is_admin(self) -> bool:
        """Return True if user has admin role."""
        return self.role == self.Role.ADMIN

    @property
    def is_customer(self) -> bool:
        """Return True if user has customer role."""
        return self.role == self.Role.CUSTOMER