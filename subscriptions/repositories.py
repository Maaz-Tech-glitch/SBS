from django.utils import timezone
from .models import Plan, Subscription
from .exceptions import PlanNotFoundException, SubscriptionNotFoundException


class PlanRepository:
    @staticmethod
    def get_by_id(plan_id):
        try:
            return Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            raise PlanNotFoundException()

    @staticmethod
    def list_active():
        return Plan.objects.filter(is_active=True)


class SubscriptionRepository:
    @staticmethod
    def create(tenant, plan, payment_method):
        return Subscription.objects.create(tenant=tenant, plan=plan, payment_method=payment_method)

    @staticmethod
    def get_by_id(subscription_id):
        try:
            return Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            raise SubscriptionNotFoundException()

    @staticmethod
    def get_active_for_tenant(tenant):
        return (
            Subscription.objects
            .filter(tenant=tenant, status="ACTIVE", end_date__gte=timezone.now())
            .order_by("-end_date")
            .first()
        )

    @staticmethod
    def list_for_tenant(tenant):
        return Subscription.objects.filter(tenant=tenant).order_by("-created_at")