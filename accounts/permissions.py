"""Custom DRF permission classes for bank_management."""
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdmin(permissions.BasePermission):
    """Allow access only to users with the 'admin' role."""

    message = "Only administrators may perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsAccountOwner(permissions.BasePermission):
    """
    Object-level permission: allow access only if the authenticated user
    owns the BankAccount (or is an admin).
    """

    message = "You do not own this account."

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if request.user.is_admin:
            return True
        # obj can be a BankAccount or a Transaction — normalise access
        account = getattr(obj, "customer", None) or getattr(obj, "from_account", None)
        if account is None:
            return False
        owner = getattr(account, "customer", account)
        return owner == request.user


class IsAdminOrAccountOwner(permissions.BasePermission):
    """
    View-level: allow authenticated users.
    Object-level: allow admins or the account owner.
    """

    message = "You do not have permission to access this resource."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if request.user.is_admin:
            return True
        customer = getattr(obj, "customer", None)
        return customer == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """Read-only for authenticated users; write access for admins only."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)
