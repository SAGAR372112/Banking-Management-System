"""Serializers for the users app."""
import re
from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for new user registration."""

    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name",
            "last_name", "password", "password_confirm",
            "phone", "address", "role",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_password(self, value: str) -> str:
        """Run Django's built-in password validators."""
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate_phone(self, value: str) -> str:
        """Normalize phone number format."""
        cleaned = re.sub(r"[\s\-().]", "", value)
        if value and not re.match(r"^\+?\d{7,15}$", cleaned):
            raise serializers.ValidationError("Enter a valid phone number (7–15 digits, optional leading +).")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Ensure passwords match."""
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        """Create user with hashed password."""
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for reading/updating a user's own profile."""

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", 
            "last_name", "phone", "address", 
            "role", "date_joined"
        ]
        read_only_fields = ["id", "username", "role", "date_joined"]


class UserMinimalSerializer(serializers.ModelSerializer):
    """Lightweight serializer for embedding user data in other responses."""

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]
        read_only_fields = fields
