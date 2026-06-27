"""Custom DRF permission classes for role- and ownership-based access control."""

from rest_framework.permissions import BasePermission, IsAuthenticated


class IsOwnerOrAdmin(BasePermission):
    """Grants object access to the object's owner/user or to admins."""

    def has_object_permission(self, request, view, obj):
        """Return True for admins, or for the user referenced by obj.owner/obj.user."""
        if not request.user.is_authenticated:
            return False

        if request.user.role == request.user.Role.ADMIN:
            return True

        owner = getattr(obj, "owner", None)

        if owner is not None:
            return owner == request.user

        owner = getattr(obj, "user", None)

        if owner is not None:
            return owner == request.user

        return False


class OwnerOrAdminActionsMixin:
    """
    ViewSet mixin that resolves get_permissions() from a declared set of
    owner-protected actions.

    Subclasses set ``owner_protected_actions`` to the action names that
    should require ``IsOwnerOrAdmin`` in addition to authentication; every
    other action only requires authentication. Used by ItemViewSet and
    WantViewSet, whose protected action sets differ but whose permission
    resolution logic is otherwise identical.
    """

    owner_protected_actions = ()

    def get_permissions(self):
        """Require ownership or admin role for the declared protected actions."""
        if self.action in self.owner_protected_actions:
            return [IsAuthenticated(), IsOwnerOrAdmin()]

        return [IsAuthenticated()]
