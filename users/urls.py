"""URL routes for the users app."""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

from .views import UserProfileView, UserRegistrationView

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="user-register"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/blacklist/", TokenBlacklistView.as_view(), name="token-blacklist"),
]
