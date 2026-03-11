"""URL routes for branches."""
from django.urls import path
from .views import BranchListView

urlpatterns = [
    path("", BranchListView.as_view(), name="branch-list"),
]
