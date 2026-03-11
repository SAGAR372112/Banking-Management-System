"""Tests for user registration and profile views."""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from conftest import UserFactory, AdminUserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestUserRegistration:
    """Test POST /api/users/register/."""

    def test_successful_registration(self, api_client):
        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "SecurePass99!",
            "password_confirm": "SecurePass99!",
        }
        response = api_client.post("/api/users/register/", payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert "account_number" in response.data

    def test_mismatched_passwords_rejected(self, api_client):
        payload = {
            "username": "user2",
            "email": "user2@example.com",
            "first_name": "A",
            "last_name": "B",
            "password": "SecurePass99!",
            "password_confirm": "DifferentPass99!",
        }
        response = api_client.post("/api/users/register/", payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_username_rejected(self, api_client):
        existing = UserFactory(username="taken")
        payload = {
            "username": "taken",
            "email": "other@example.com",
            "first_name": "A",
            "last_name": "B",
            "password": "SecurePass99!",
            "password_confirm": "SecurePass99!",
        }
        response = api_client.post("/api/users/register/", payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_password_rejected(self, api_client):
        payload = {
            "username": "weakuser",
            "email": "weak@example.com",
            "first_name": "A",
            "last_name": "B",
            "password": "123",
            "password_confirm": "123",
        }
        response = api_client.post("/api/users/register/", payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserProfile:
    """Test GET/PUT /api/users/profile/."""

    def test_get_own_profile(self, api_client):
        user = UserFactory(first_name="Alice")
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/users/profile/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Alice"

    def test_unauthenticated_cannot_get_profile(self, api_client):
        response = api_client.get("/api/users/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.put("/api/users/profile/", {"address": "123 New Street"})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.address == "123 New Street"

    def test_cannot_change_role_via_profile(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        api_client.put("/api/users/profile/", {"role": "admin"})
        user.refresh_from_db()
        assert user.role == "customer"
