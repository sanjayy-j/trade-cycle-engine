from rest_framework import viewsets

from ..constants import UUID_REGEX
from ..pagination import ItemPagination
from ..permissions import OwnerOrAdminActionsMixin
from ..models import Item
from ..serializers import ItemSerializer


class ItemViewSet(OwnerOrAdminActionsMixin, viewsets.ModelViewSet):
    """
    Standard CRUD for items: list/retrieve are open to any authenticated
    user (items are publicly browsable, like a marketplace listing);
    update/destroy are restricted to the owner or an admin.
    """

    serializer_class = ItemSerializer
    pagination_class = ItemPagination
    lookup_field = "public_id"
    lookup_value_regex = UUID_REGEX
    owner_protected_actions = ("update", "partial_update", "destroy")

    def get_queryset(self):
        """Return all items, with owners preloaded, ordered by creation time."""
        return Item.objects.select_related("owner").order_by("created_at")

    def perform_create(self, serializer):
        """Assign the requesting user as the new item's owner."""
        serializer.save(owner=self.request.user)
