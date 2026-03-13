"""Views for transaction operations: deposit, withdraw, transfer, list."""
from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import BankAccount
from accounts.permissions import IsAdminOrAccountOwner
from .models import Transaction
from .serializers import (
    DepositSerializer,
    TransactionSerializer,
    TransferSerializer,
    WithdrawSerializer,
)
from .services import (
    AccountNotOperableError,
    DailyLimitExceededError,
    InsufficientFundsError,
    InvalidTransactionError,
    process_deposit,
    process_transfer,
    process_withdrawal,
)


def _get_owned_account(account_id: int, user) -> BankAccount:
    """Retrieve an account the user owns (or any account if admin)."""
    account = get_object_or_404(BankAccount, pk=account_id)
    if not user.is_admin and account.customer != user:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("You do not own this account.")
    return account


class DepositView(APIView):
    """
    POST /api/accounts/{account_id}/deposit/
    Deposit funds into the specified account.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Deposit funds",
        request=DepositSerializer,
        responses={200: TransactionSerializer},
    )
    def post(self, request, account_id: int):
        _get_owned_account(account_id, request.user)
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            txn = process_deposit(
                account_id, 
                data["amount"], 
                data.get("reference", "")
            )
        except AccountNotOperableError as exc:
            return Response(
                {"detail": str(exc)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            TransactionSerializer(txn).data, 
            status=status.HTTP_200_OK
        )


class WithdrawView(APIView):
    """
    POST /api/accounts/{account_id}/withdraw/
    Withdraw funds from the specified account.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Withdraw funds",
        request=WithdrawSerializer,
        responses={200: TransactionSerializer},
    )
    def post(self, request, account_id: int):
        _get_owned_account(account_id, request.user)
        serializer = WithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            txn = process_withdrawal(
                account_id, 
                data["amount"], 
                data.get("reference", "")
            )
        except (
            InsufficientFundsError, 
            AccountNotOperableError, 
            DailyLimitExceededError
        ) as exc:
            return Response(
                {"detail": str(exc)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            TransactionSerializer(txn).data, 
            status=status.HTTP_200_OK
        )


class TransferView(APIView):
    """
    POST /api/transfer/
    Transfer funds between two accounts.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Transfer funds between accounts",
        request=TransferSerializer,
        responses={200: TransactionSerializer},
    )
    def post(self, request):
        print('start')
        serializer = TransferSerializer(data=request.data)
        print('1')
        serializer.is_valid(raise_exception=True)
        print('2')
        data = serializer.validated_data
        print('3')

        from_account: BankAccount = data["from_account"]
        # Customers may only transfer from their own accounts
        if not request.user.is_admin and from_account.customer != request.user:
            return Response(
                {"detail": "You do not own the source account."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            txn = process_transfer(
                from_account.pk,
                data["to_account"].pk,
                data["amount"],
                data.get("reference", ""),
            )
        except (
            InsufficientFundsError, 
            AccountNotOperableError, 
            DailyLimitExceededError, 
            InvalidTransactionError
        ) as exc:
            return Response(
                {"detail": str(exc)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            TransactionSerializer(txn).data, 
            status=status.HTTP_200_OK
        )


class AccountTransactionListView(generics.ListAPIView):
    """
    GET /api/accounts/{account_id}/transactions/?limit=20&offset=0
    List all transactions for a given account (paginated).
    """

    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["type", "status"]
    ordering_fields = ["timestamp", "amount"]
    ordering = ["-timestamp"]

    def get_queryset(self) -> QuerySet:
        account_id = self.kwargs["account_id"]
        account = _get_owned_account(account_id, self.request.user)
        return Transaction.objects.filter(
            Q(from_account=account) | Q(to_account=account)
        ).select_related("from_account", "to_account")

    @extend_schema(summary="List transactions for an account")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
