"""Tests for the branches app."""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from conftest import BranchFactory, UserFactory
from branches.models import Branch


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestBranchModel:
    """Test Branch model."""

    def test_branch_str(self):
        branch = BranchFactory(name="Main Branch", branch_code="MAIN01")
        assert "Main Branch" in str(branch)
        assert "MAIN01" in str(branch)

    def test_branch_code_unique(self):
        BranchFactory(branch_code="UNIQ01")
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Branch.objects.create(
                branch_code="UNIQ01",
                name="Duplicate",
                address="123 St",
                manager_name="Manager",
            )


@pytest.mark.django_db
class TestBranchListView:
    """Test GET /api/branches/."""

    def test_authenticated_user_can_list_branches(self, api_client):
        user = UserFactory()
        BranchFactory.create_batch(3)
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/branches/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 3

    def test_unauthenticated_cannot_list_branches(self, api_client):
        response = api_client.get("/api/branches/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
