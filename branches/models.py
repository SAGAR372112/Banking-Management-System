"""Branch model."""
from django.core.validators import RegexValidator
from django.db import models


class Branch(models.Model):
    """
    Represents a physical bank branch.

    branch_code is a unique alphanumeric identifier (e.g. "NYC001").
    """

    branch_code = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r"^[A-Z0-9]{3,20}$", "Branch code must be 3–20 uppercase alphanumeric characters.")],
    )
    name = models.CharField(max_length=255)
    address = models.TextField()
    manager_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.branch_code})"
