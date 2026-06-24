from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response

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
    # No full-replace semantics needed - PATCH covers every legitimate edit,
    # so PUT is dropped to keep one way to update a resource.
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """Return non-deleted items, with owners preloaded, newest-created last."""
        return Item.active.select_related("owner").order_by("created_at")

    def perform_create(self, serializer):
        """Assign the requesting user as the new item's owner."""
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Block deletion of an item that is RESERVED by a pending proposal.

        A RESERVED item is already committed to an in-flight trade; letting
        it be deleted out from under that proposal would let the proposal
        execute against an item no longer considered tradable. Inlines
        DRF's default destroy() body (rather than delegating to super())
        so get_object() only runs once.
        """
        instance = self.get_object()

        if instance.status == Item.Status.RESERVED:
            return Response(
                {"detail": "Reserved items cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """
        Soft-delete the item instead of removing its row.

        TradeItem/TradeExecution rows reference items by foreign key, so a
        hard delete would either cascade and destroy historical trade
        records or be blocked by the database; soft delete keeps the row
        (and history) intact while removing it from every active queryset.
        """
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["is_deleted", "deleted_at"])
