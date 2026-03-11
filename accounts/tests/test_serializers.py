"""Tests for account serializers."""
import pytest
from decimal import Decimal
from django.test import RequestFactory

from conftest import BankAccountFactory, BranchFactory, UserFactory
from accounts.serializers import BankAccountCreateSerializer, BankAccountUpdateSerializer


@pytest.mark.django_db
class TestBankAccountCreateSerializer:
    """Test BankAccountCreateSerializer validation."""

    def test_valid_data(self):
        """Valid data passes serializer validation."""
        branch = BranchFactory()
        user = UserFactory()
        factory = RequestFactory()
        request = factory.post("/")
        request.user = user

        data = {"account_type": "savings", "branch": branch.pk}
        serializer = BankAccountCreateSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors

    def test_invalid_account_type(self):
        """Invalid account_type is rejected."""
        branch = BranchFactory()
        user = UserFactory()
        factory = RequestFactory()
        request = factory.post("/")
        request.user = user

        data = {"account_type": "invalid", "branch": branch.pk}
        serializer = BankAccountCreateSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()
        assert "account_type" in serializer.errors

    def test_missing_branch(self):
        """Missing branch field is rejected."""
        user = UserFactory()
        factory = RequestFactory()
        request = factory.post("/")
        request.user = user

        data = {"account_type": "savings"}
        serializer = BankAccountCreateSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()
        assert "branch" in serializer.errors


@pytest.mark.django_db
class TestBankAccountUpdateSerializer:
    """Test update serializer restrictions."""

    def test_customer_cannot_freeze_account(self):
        """Non-admin cannot set status to frozen."""
        user = UserFactory()
        factory = RequestFactory()
        request = factory.put("/")
        request.user = user

        data = {"status": "frozen"}
        serializer = BankAccountUpdateSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()

    def test_admin_can_freeze_account(self):
        """Admin can set status to frozen."""
        from conftest import AdminUserFactory
        admin = AdminUserFactory()
        factory = RequestFactory()
        request = factory.put("/")
        request.user = admin

        data = {"status": "frozen"}
        serializer = BankAccountUpdateSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors
