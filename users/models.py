"""Custom User model with role-based access control."""
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

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
            models.Index(fields=["role"])
        ]

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"

    @property
    def is_admin(self) -> bool:
        """Return True if user has admin role."""
        return self.role == self.Role.ADMIN

    @property
    def is_customer(self) -> bool:
        """Return True if user has customer role."""
        return self.role == self.Role.CUSTOMER