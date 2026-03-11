"""Tests for the BankAccount model."""
import pytest
from decimal import Decimal

from conftest import BankAccountFactory, UserFactory, BranchFactory
from accounts.models import BankAccount


@pytest.mark.django_db
class TestBankAccountModel:
    """Test suite for BankAccount model."""

    def test_account_number_auto_generated(self):
        """Account number is auto-generated and starts with ACC."""
        account = BankAccountFactory()
        assert account.account_number.startswith("ACC")
        assert len(account.account_number) == 13  # ACC + 10 hex chars

    def test_account_number_unique(self):
        """Two accounts have different account numbers."""
        acc1 = BankAccountFactory()
        acc2 = BankAccountFactory()
        assert acc1.account_number != acc2.account_number

    def test_default_status_is_active(self):
        """New accounts default to active status."""
        account = BankAccountFactory()
        assert account.status == BankAccount.Status.ACTIVE

    def test_is_operable_when_active(self):
        """Active accounts are operable."""
        account = BankAccountFactory(status=BankAccount.Status.ACTIVE)
        assert account.is_operable() is True

    def test_not_operable_when_frozen(self):
        """Frozen accounts are not operable."""
        account = BankAccountFactory(status=BankAccount.Status.FROZEN)
        assert account.is_operable() is False

    def test_not_operable_when_inactive(self):
        """Inactive accounts are not operable."""
        account = BankAccountFactory(status=BankAccount.Status.INACTIVE)
        assert account.is_operable() is False

    def test_str_representation(self):
        """__str__ contains account number and type."""
        account = BankAccountFactory(account_type=BankAccount.AccountType.SAVINGS)
        assert account.account_number in str(account)
        assert "savings" in str(account)

    def test_balance_precision(self):
        """Balance stored with 2 decimal places."""
        account = BankAccountFactory(balance=Decimal("123.45"))
        account.refresh_from_db()
        assert account.balance == Decimal("123.45")
