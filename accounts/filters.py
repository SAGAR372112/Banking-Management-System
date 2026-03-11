"""Django-filter FilterSets for the accounts app."""
import django_filters

from .models import BankAccount


class BankAccountFilter(django_filters.FilterSet):
    """Filter bank accounts by type, status, and customer."""

    account_type = django_filters.ChoiceFilter(choices=BankAccount.AccountType.choices)
    status = django_filters.ChoiceFilter(choices=BankAccount.Status.choices)
    customer_username = django_filters.CharFilter(field_name="customer__username", lookup_expr="icontains")
    branch_code = django_filters.CharFilter(field_name="branch__branch_code", lookup_expr="iexact")
    min_balance = django_filters.NumberFilter(field_name="balance", lookup_expr="gte")
    max_balance = django_filters.NumberFilter(field_name="balance", lookup_expr="lte")

    class Meta:
        model = BankAccount
        fields = ["account_type", "status", "customer_username", "branch_code", "min_balance", "max_balance"]
