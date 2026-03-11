"""Views for branch listing."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from .models import Branch
from .serializers import BranchCreateSerializer, BranchSerializer


class BranchListView(generics.ListAPIView):
    """
    GET /api/branches/
    List all branches. Authenticated users only.
    """

    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["name", "branch_code"]
    search_fields = ["name", "branch_code", "manager_name"]
    ordering_fields = ["name", "branch_code", "created_at"]
    ordering = ["name"]

    @extend_schema(summary="List all bank branches")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Create a new bank branch", request=BranchCreateSerializer, responses={201: BranchSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Branch created successfully.", "branch_id": serializer.instance.id},
            status=status.HTTP_201_CREATED,
        )
