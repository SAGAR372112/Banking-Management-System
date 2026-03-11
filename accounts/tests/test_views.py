"""Tests for account API views."""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from conftest import AdminUserFactory, BankAccountFactory, BranchFactory, UserFactory
from accounts.models import BankAccount


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer_client(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture
def admin_client(api_client):
    admin = AdminUserFactory()
    api_client.force_authenticate(user=admin)
    return api_client, admin


@pytest.mark.django_db
class TestBankAccountListCreate:
    """Test GET/POST /api/accounts/."""

    def test_customer_sees_only_own_accounts(self, customer_client):
        client, user = customer_client
        own = BankAccountFactory(customer=user)
        other = BankAccountFactory()  # belongs to someone else

        response = client.get("/api/accounts/")
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert own.pk in ids
        assert other.pk not in ids

    def test_admin_sees_all_accounts(self, admin_client):
        client, _ = admin_client
        BankAccountFactory.create_batch(3)

        response = client.get("/api/accounts/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 3

    def test_create_account(self, customer_client):
        client, user = customer_client
        branch = BranchFactory()

        response = client.post("/api/accounts/", {"account_type": "savings", "branch": branch.pk})
        assert response.status_code == status.HTTP_201_CREATED
        assert BankAccount.objects.filter(customer=user).exists()

    def test_unauthenticated_request_denied(self):
        client = APIClient()
        response = client.get("/api/accounts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestBankAccountDetail:
    """Test GET/PUT/DELETE /api/accounts/{id}/."""

    def test_customer_can_get_own_account(self, customer_client):
        client, user = customer_client
        account = BankAccountFactory(customer=user)
        response = client.get(f"/api/accounts/{account.pk}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["account_number"] == account.account_number

    def test_customer_cannot_get_other_account(self, customer_client):
        client, _ = customer_client
        other_account = BankAccountFactory()
        response = client.get(f"/api/accounts/{other_account.pk}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_soft_delete_with_zero_balance(self, admin_client):
        client, _ = admin_client
        account = BankAccountFactory(balance=Decimal("0.00"))
        response = client.delete(f"/api/accounts/{account.pk}/")
        assert response.status_code == status.HTTP_200_OK
        account.refresh_from_db()
        assert account.status == BankAccount.Status.INACTIVE

    def test_admin_cannot_delete_account_with_balance(self, admin_client):
        client, _ = admin_client
        account = BankAccountFactory(balance=Decimal("100.00"))
        response = client.delete(f"/api/accounts/{account.pk}/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
