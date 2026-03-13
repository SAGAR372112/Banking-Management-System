"""Serializers for the transactions app."""
from decimal import Decimal

from rest_framework import serializers

from accounts.models import BankAccount
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """Read-only serializer for returning transaction data."""

    from_account_number = serializers.CharField(
        source="from_account.account_number", 
        read_only=True, 
        default=None
    )
    to_account_number = serializers.CharField(
        source="to_account.account_number", 
        read_only=True, 
        default=None
    )

    class Meta:
        model = Transaction
        fields = [
            "id", "transaction_id", "type", "amount",
            "from_account", "from_account_number",
            "to_account", "to_account_number",
            "reference", "status", "timestamp",
        ]
        read_only_fields = fields


class DepositSerializer(serializers.Serializer):
    """Input serializer for deposit operations."""

    amount = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        min_value=Decimal("0.01")
    )
    reference = serializers.CharField(
        max_length=255,
        required=False, 
        default="", 
        allow_blank=True
    )

    def validate_amount(self, amount: Decimal) -> Decimal:
        if amount <= 0:
            raise serializers.ValidationError("Deposit amount must be positive.")
        return amount


class WithdrawSerializer(serializers.Serializer):
    """Input serializer for withdrawal operations."""

    amount = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        min_value=Decimal("0.01")
    )
    reference = serializers.CharField(
        max_length=255, 
        required=False, 
        default="", 
        allow_blank=True
    )

    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Withdrawal amount must be positive.")
        return value


class TransferSerializer(serializers.Serializer):
    """Input serializer for account-to-account transfers."""

    from_account = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all()
    )
    to_account = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all()
    )
    amount = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        min_value=Decimal("0.01")
    )
    reference = serializers.CharField(
        max_length=255, 
        required=False, 
        default="", 
        allow_blank=True
    )

    def validate(self, attrs):
        if attrs["from_account"] == attrs["to_account"]:
            raise serializers.ValidationError(
            {"to_account": "Source and destination accounts must differ."}
            )
        return attrs
