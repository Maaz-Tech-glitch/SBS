from rest_framework.permissions import BasePermission


class IsNotificationAdmin(BasePermission):
    message = "Only an admin can access notifications."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(request.user, "role", None) == "admin"
            and getattr(request.user, "tenant_id", None) is not None
        )
