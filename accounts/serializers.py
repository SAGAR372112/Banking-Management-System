"""Serializers for the accounts app."""
from decimal import Decimal
from typing import Any

from rest_framework import serializers

from users.serializers import UserMinimalSerializer
from branches.serializers import BranchSerializer
from .models import BankAccount


class BankAccountSerializer(serializers.ModelSerializer):
    """Full bank account serializer — used for GET responses."""

    customer = UserMinimalSerializer(read_only=True)
    branch_detail = BranchSerializer(source="branch", read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            "id", "account_number", "account_type", "balance",
            "status", "customer", "branch", "branch_detail",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "account_number", "balance", "created_at", "updated_at"]


class BankAccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new bank account."""

    class Meta:
        model = BankAccount
        fields = ["id", "account_number", "account_type", "branch", 'balance', 'customer']
        read_only_fields = ["id", "account_number", 'customer']


class BankAccountUpdateSerializer(serializers.ModelSerializer):
    """Allow updating only account_type and status (admins only for status)."""

    class Meta:
        model = BankAccount
        fields = ["account_type", "status", 'balance', 'branch']
        read_only_fields = ["id", "account_number"]


class AccountBalanceSerializer(serializers.Serializer):
    """Simple serializer to return current balance."""

    account_number = serializers.CharField()
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    status = serializers.CharField()
