"""URL routes for the accounts app."""
from django.urls import path
from .views import AdminDashboardStatsView, BankAccountDetailView, BankAccountListCreateView
from transactions.views import DepositView, WithdrawView, AccountTransactionListView

urlpatterns = [
    path("", BankAccountListCreateView.as_view(), name="account-list-create"),
    path("<int:pk>/", BankAccountDetailView.as_view(), name="account-detail"),
    path("<int:account_id>/deposit/", DepositView.as_view(), name="account-deposit"),
    path("<int:account_id>/withdraw/", WithdrawView.as_view(), name="account-withdraw"),
    path("<int:account_id>/transactions/", AccountTransactionListView.as_view(), name="account-transactions"),
]

admin_urlpatterns = [
    path("admin/dashboard/stats/", AdminDashboardStatsView.as_view(), name="admin-dashboard"),
]
