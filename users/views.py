"""Views for user registration and profile management."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import User
from .serializers import UserProfileSerializer, UserRegistrationSerializer


class UserRegistrationView(generics.CreateAPIView):
    """
    POST /api/users/register/
    Register a new customer account. No authentication required.
    """

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register a new user",
        responses={201: UserRegistrationSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": "Registration successful.", 
            "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/users/profile/  — Retrieve own profile.
    PUT  /api/users/profile/  — Update own profile (partial updates supported).
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> User:
        """Always operate on the authenticated user's own profile."""
        return self.request.user

    @extend_schema(summary="Get current user profile")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Update current user profile")
    def put(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
