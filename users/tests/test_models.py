"""Tests for the User model."""
import pytest
from django.core.exceptions import ValidationError

from conftest import UserFactory, AdminUserFactory
from users.models import User


@pytest.mark.django_db
class TestUserModel:
    """Test suite for the custom User model."""

    def test_create_customer_user(self):
        """A newly created user defaults to the customer role."""
        user = UserFactory()
        assert user.role == User.Role.CUSTOMER
        assert user.is_customer is True
        assert user.is_admin is False

    def test_create_admin_user(self):
        """Admin factory creates users with admin role."""
        admin = AdminUserFactory()
        assert admin.role == User.Role.ADMIN
        assert admin.is_admin is True
        assert admin.is_customer is False

    def test_account_number_auto_generated(self):
        """Account number is auto-generated on save and is 10 digits."""
        user = UserFactory()
        assert user.account_number is not None
        assert len(user.account_number) == 10
        assert user.account_number.isdigit()

    def test_account_number_is_unique(self):
        """Two different users get different account numbers."""
        user1 = UserFactory()
        user2 = UserFactory()
        assert user1.account_number != user2.account_number

    def test_account_number_not_changed_on_update(self):
        """Resaving a user does not regenerate the account number."""
        user = UserFactory()
        original_number = user.account_number
        user.first_name = "Updated"
        user.save()
        user.refresh_from_db()
        assert user.account_number == original_number

    def test_str_representation(self):
        """__str__ returns username and role."""
        user = UserFactory(username="john", role=User.Role.CUSTOMER)
        assert "john" in str(user)
        assert "customer" in str(user)

    def test_password_is_hashed(self):
        """Password is stored hashed, not in plaintext."""
        user = UserFactory()
        assert not user.password.startswith("TestPass123!")
        assert user.check_password("TestPass123!")
