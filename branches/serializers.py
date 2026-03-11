"""Serializers for the branches app."""
from rest_framework import serializers

from .models import Branch


class BranchSerializer(serializers.ModelSerializer):
    """Full branch serializer."""

    class Meta:
        model = Branch
        fields = ["id", "branch_code", "name", "address", "manager_name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class BranchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new branch."""

    class Meta:
        model = Branch
        fields = ["id", "branch_code", "name", "address", "manager_name"]
        read_only_fields = ["id"]