"""Tests for transaction operations: deposit, withdraw, transfer, rollback."""
import pytest
from decimal import Decimal
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient

from conftest import AdminUserFactory, BankAccountFactory, UserFactory
from accounts.models import BankAccount
from transactions.models import Transaction
from transactions.services import (
    DailyLimitExceededError,
    InsufficientFundsError,
    InvalidTransactionError,
    process_deposit,
    process_transfer,
    process_withdrawal,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestDepositService:
    """Unit tests for process_deposit service."""

    def test_successful_deposit(self):
        account = BankAccountFactory(balance=Decimal("100.00"))
        txn = process_deposit(account.pk, Decimal("50.00"))
        account.refresh_from_db()
        assert account.balance == Decimal("150.00")
        assert txn.status == Transaction.TransactionStatus.COMPLETED

    def test_deposit_to_inactive_account_raises(self):
        account = BankAccountFactory(status=BankAccount.Status.INACTIVE)
        with pytest.raises(Exception):
            process_deposit(account.pk, Decimal("100.00"))

    def test_deposit_to_frozen_account_raises(self):
        account = BankAccountFactory(status=BankAccount.Status.FROZEN)
        with pytest.raises(Exception):
            process_deposit(account.pk, Decimal("100.00"))


@pytest.mark.django_db
class TestWithdrawService:
    """Unit tests for process_withdrawal service."""

    def test_successful_withdrawal(self):
        account = BankAccountFactory(balance=Decimal("200.00"))
        txn = process_withdrawal(account.pk, Decimal("75.00"))
        account.refresh_from_db()
        assert account.balance == Decimal("125.00")
        assert txn.status == Transaction.TransactionStatus.COMPLETED

    def test_insufficient_funds_raises(self):
        account = BankAccountFactory(balance=Decimal("10.00"))
        with pytest.raises(InsufficientFundsError):
            process_withdrawal(account.pk, Decimal("100.00"))

    def test_balance_unchanged_on_insufficient_funds(self):
        account = BankAccountFactory(balance=Decimal("10.00"))
        original_balance = account.balance
        with pytest.raises(InsufficientFundsError):
            process_withdrawal(account.pk, Decimal("100.00"))
        account.refresh_from_db()
        assert account.balance == original_balance


@pytest.mark.django_db
class TestTransferService:
    """Unit tests for process_transfer service."""

    def test_successful_transfer(self):
        sender = BankAccountFactory(balance=Decimal("500.00"))
        receiver = BankAccountFactory(balance=Decimal("100.00"))
        txn = process_transfer(sender.pk, receiver.pk, Decimal("200.00"))
        sender.refresh_from_db()
        receiver.refresh_from_db()
        assert sender.balance == Decimal("300.00")
        assert receiver.balance == Decimal("300.00")
        assert txn.status == Transaction.TransactionStatus.COMPLETED

    def test_same_account_transfer_raises(self):
        account = BankAccountFactory(balance=Decimal("500.00"))
        with pytest.raises(InvalidTransactionError):
            process_transfer(account.pk, account.pk, Decimal("100.00"))

    def test_insufficient_funds_rollback(self):
        """On failure, both account balances remain unchanged."""
        sender = BankAccountFactory(balance=Decimal("50.00"))
        receiver = BankAccountFactory(balance=Decimal("100.00"))
        sender_balance = sender.balance
        receiver_balance = receiver.balance

        with pytest.raises(InsufficientFundsError):
            process_transfer(sender.pk, receiver.pk, Decimal("200.00"))

        sender.refresh_from_db()
        receiver.refresh_from_db()
        assert sender.balance == sender_balance
        assert receiver.balance == receiver_balance

    def test_transfer_from_frozen_account_raises(self):
        sender = BankAccountFactory(balance=Decimal("500.00"), status=BankAccount.Status.FROZEN)
        receiver = BankAccountFactory()
        with pytest.raises(Exception):
            process_transfer(sender.pk, receiver.pk, Decimal("100.00"))


@pytest.mark.django_db
class TestTransactionViews:
    """Integration tests for deposit/withdraw/transfer API endpoints."""

    def test_deposit_endpoint(self, api_client):
        user = UserFactory()
        account = BankAccountFactory(customer=user, balance=Decimal("0.00"))
        api_client.force_authenticate(user=user)

        response = api_client.post(
            f"/api/accounts/{account.pk}/deposit/",
            {"amount": "250.00"},
        )
        assert response.status_code == status.HTTP_200_OK
        account.refresh_from_db()
        assert account.balance == Decimal("250.00")

    def test_withdraw_endpoint(self, api_client):
        user = UserFactory()
        account = BankAccountFactory(customer=user, balance=Decimal("500.00"))
        api_client.force_authenticate(user=user)

        response = api_client.post(
            f"/api/accounts/{account.pk}/withdraw/",
            {"amount": "100.00"},
        )
        assert response.status_code == status.HTTP_200_OK
        account.refresh_from_db()
        assert account.balance == Decimal("400.00")

    def test_withdraw_insufficient_funds(self, api_client):
        user = UserFactory()
        account = BankAccountFactory(customer=user, balance=Decimal("10.00"))
        api_client.force_authenticate(user=user)

        response = api_client.post(
            f"/api/accounts/{account.pk}/withdraw/",
            {"amount": "1000.00"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_transfer_endpoint(self, api_client):
        user = UserFactory()
        sender = BankAccountFactory(customer=user, balance=Decimal("500.00"))
        receiver = BankAccountFactory(balance=Decimal("0.00"))
        api_client.force_authenticate(user=user)

        response = api_client.post(
            "/api/transfer/",
            {"from_account": sender.pk, "to_account": receiver.pk, "amount": "150.00"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_cannot_deposit_to_other_user_account(self, api_client):
        user = UserFactory()
        other_account = BankAccountFactory()  # Different owner
        api_client.force_authenticate(user=user)

        response = api_client.post(
            f"/api/accounts/{other_account.pk}/deposit/",
            {"amount": "100.00"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_transaction_list_for_account(self, api_client):
        user = UserFactory()
        account = BankAccountFactory(customer=user)
        process_deposit(account.pk, Decimal("100.00"))
        api_client.force_authenticate(user=user)

        response = api_client.get(f"/api/accounts/{account.pk}/transactions/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1
