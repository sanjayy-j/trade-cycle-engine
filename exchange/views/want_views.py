from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..constants import UUID_REGEX
from ..permissions import OwnerOrAdminActionsMixin
from ..models import Item, Want
from ..serializers import WantSerializer


class WantViewSet(OwnerOrAdminActionsMixin, viewsets.ModelViewSet):
    """
    Standard CRUD for wants. Unlike items, wants are personal: list is
    scoped to the requesting user, and retrieve/update/destroy require
    being the owner or an admin (a non-owner gets 403, not a 404, to
    match the original behavior of confirming the want exists but
    denying access to it).
    """

    serializer_class = WantSerializer
    lookup_field = "public_id"
    lookup_value_regex = UUID_REGEX
    owner_protected_actions = ("retrieve", "update", "partial_update", "destroy")

    def get_queryset(self):
        """Scope list requests to the requesting user; other actions see all wants."""
        queryset = Want.objects.select_related("user", "item")

        if self.action == "list":
            return queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        """Assign the requesting user as the new want's owner."""
        serializer.save(user=self.request.user)


class MatchListView(APIView):
    """Lists the requesting user's items alongside who currently wants each one."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return each of the user's items with the usernames that want it."""
        results = []

        my_items = Item.active.filter(owner=request.user).prefetch_related(
            "wanted_by__user"
        )

        for item in my_items:
            interested_users = [want.user.username for want in item.wanted_by.all()]

            results.append(
                {
                    "item": item.name,
                    "interested_users": interested_users,
                }
            )

        return Response(results)
