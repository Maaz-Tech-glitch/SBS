from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services import get_dashboard_summary
from .serializers import DashboardSummarySerializer
from subscriptions.repositories import SubscriptionRepository
from subscriptions.permissions import IsSubscriptionActive
from users.permissions import HasModuleAccess


class DashboardSummaryAPIView(APIView):
    """
    Real-world SaaS Dashboard: Store Info, User Profile, Subscription Status,
    aur Inventory/Sales Metrics ko ek saath return karta hai.
    """
    required_module = "dashboard"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]

    def get(self, request):
        user = request.user
        tenant = user.tenant

        # Current active subscription fetch karen (exception nahi phenkta - None milega agar na ho)
        subscription = SubscriptionRepository.get_active_for_tenant(tenant) if tenant else None
        is_active = subscription is not None and subscription.status == "ACTIVE"

        # Basic Store & User Object
        store_info = {
            "id": tenant.id if tenant else None,
            "name": getattr(tenant, 'name', 'My Store'),
        }

        user_info = {
            "id": user.id,
            "username": user.username,
            "email": getattr(user, 'email', ''),
            "role": getattr(user, 'role', 'ADMIN'),
        }

        # Agar Subscription Active hai to Full Dashboard Data bhejen
        if is_active:
            raw_metrics = get_dashboard_summary(user)
            metrics_data = DashboardSummarySerializer(raw_metrics).data

            return Response({
                "status": "success",
                "store": store_info,
                "user": user_info,
                "subscription": {
                    "is_active": True,
                    "plan_name": subscription.plan.name if subscription.plan else "N/A",
                    "end_date": subscription.end_date,
                },
                "metrics": metrics_data
            })

        # Subscription Active na hone par Limited Info
        return Response({
            "status": "subscription_required",
            "store": store_info,
            "user": user_info,
            "subscription": {
                "is_active": False,
                "plan_name": None,
                "end_date": None,
            },
            "metrics": None,
            "message": "Please subscribe to a plan to unlock full dashboard features."
        })