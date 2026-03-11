"""Views for bank account management."""
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .filters import BankAccountFilter
from .models import BankAccount
from .permissions import IsAdmin, IsAdminOrAccountOwner
from .serializers import BankAccountCreateSerializer, BankAccountSerializer, BankAccountUpdateSerializer


class BankAccountListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/accounts/  — List accounts (customers see own, admins see all).
    POST /api/accounts/  — Create a new bank account for the authenticated customer.
    """

    permission_classes = [permissions.IsAuthenticated]
    filterset_class = BankAccountFilter
    ordering_fields = ["created_at", "balance", "account_type"]
    ordering = ["-created_at"]

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        qs = BankAccount.objects.select_related("customer", "branch")
        if user.is_admin:
            return qs
        return qs.filter(customer=user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BankAccountCreateSerializer
        return BankAccountSerializer
        
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    @extend_schema(summary="List bank accounts", responses={200: BankAccountSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Create a bank account", request=BankAccountCreateSerializer, responses={201: BankAccountSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class BankAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/accounts/{id}/  — Retrieve account details.
    PUT    /api/accounts/{id}/  — Update account_type or status.
    DELETE /api/accounts/{id}/  — Soft-delete by setting status=inactive (admins only).
    """

    permission_classes = [IsAdminOrAccountOwner]
    queryset = BankAccount.objects.select_related("customer", "branch")

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return BankAccountUpdateSerializer
        return BankAccountSerializer

    @extend_schema(summary="Get bank account details")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Update bank account", request=BankAccountUpdateSerializer)
    def put(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Deactivate (soft-delete) a bank account")
    def delete(self, request, *args, **kwargs):
        """Soft-delete: sets status to inactive instead of removing the row."""
        if not request.user.is_admin:
            return Response({"detail": "Only admins may delete accounts."}, status=status.HTTP_403_FORBIDDEN)
        account = self.get_object()
        if account.balance < 0:
            return Response(
                {"detail": "Cannot deactivate an account with a negative balance."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        account.status = BankAccount.Status.INACTIVE
        account.save(update_fields=["status", "updated_at"])
        return Response({"detail": "Account deactivated."}, status=status.HTTP_200_OK)


class AdminDashboardStatsView(generics.GenericAPIView):
    """
    GET /api/admin/dashboard/stats/
    Aggregate stats across all accounts and transactions.
    """

    permission_classes = [IsAdmin]

    @extend_schema(summary="Admin dashboard statistics")
    def get(self, request, *args, **kwargs):
        from django.db.models import Count, Sum
        from transactions.models import Transaction
        from users.models import User

        account_stats = BankAccount.objects.aggregate(
            total_accounts=Count("id"),
            total_balance=Sum("balance"),
        )
        transaction_stats = Transaction.objects.aggregate(
            total_transactions=Count("id"),
        )
        user_stats = User.objects.aggregate(
            total_users=Count("id"),
            total_customers=Count("id", filter=__import__("django.db.models", fromlist=["Q"]).Q(role="customer")),
        )

        return Response(
            {
                "accounts": account_stats,
                "transactions": transaction_stats,
                "users": user_stats,
                "accounts_by_status": list(
                    BankAccount.objects.values("status").annotate(count=Count("id"))
                ),
            }
        )
