from rest_framework import viewsets

from ..constants import UUID_REGEX
from ..permissions import OwnerOrAdminActionsMixin
from ..models import Want
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
    # Want has a single writable field (item), so PUT and PATCH would be
    # behaviorally identical - PATCH alone is kept as the one update path.
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """Scope list requests to the requesting user; other actions see all wants."""
        queryset = Want.objects.select_related("user", "item")

        if self.action == "list":
            return queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        """Assign the requesting user as the new want's owner."""
        serializer.save(user=self.request.user)
