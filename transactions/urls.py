"""URL routes for the transactions app."""
from django.urls import include, path
from .views import TransferView
from accounts.urls import urlpatterns as account_urls, admin_urlpatterns

urlpatterns = [
    path("transfer/", TransferView.as_view(), name="transfer"),
    path("accounts/", include(account_urls)),
    path("", include(admin_urlpatterns)),
]
