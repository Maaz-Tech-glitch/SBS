from rest_framework.permissions import BasePermission
from .services import SubscriptionService


class IsSubscriptionActive(BasePermission):
    message = "No active subscription found for your account. Please subscribe to continue."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        tenant = getattr(user, "tenant", None)
        if not tenant:
            return False
        return SubscriptionService.is_active(tenant)