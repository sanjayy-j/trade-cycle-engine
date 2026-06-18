from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    def has_permission(
        self,
        request,
        view,
    ):
        return (
            request.user.is_authenticated
            and request.user.role
            == request.user.Role.ADMIN
        )


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        if not request.user.is_authenticated:
            return False

        if (
            request.user.role
            == request.user.Role.ADMIN
        ):
            return True

        owner = getattr(
            obj,
            "owner",
            None,
        )

        if owner is not None:
            return owner == request.user

        owner = getattr(
            obj,
            "user",
            None,
        )

        if owner is not None:
            return owner == request.user

        return False