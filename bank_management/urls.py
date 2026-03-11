"""URL configuration for bank_management project."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def health_check(request):
    """Health check endpoint for deployment platforms."""
    return JsonResponse({"status": "healthy", "service": "bank-management-api"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    # API
    path("api/users/", include("users.urls")),
    path("api/accounts/", include("accounts.urls")),
    path("api/", include("transactions.urls")),
    path("api/branches/", include("branches.urls")),
    # OpenAPI Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
