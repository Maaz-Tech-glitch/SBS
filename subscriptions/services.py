from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from .repositories import PlanRepository, SubscriptionRepository
from .strategies import PaymentStrategyFactory
from .exceptions import NoActiveSubscriptionException, PaymentFailedException, NoTenantException


class PlanService:
    @staticmethod
    def list_plans():
        return PlanRepository.list_active()

    @staticmethod
    def get_plan(plan_id):
        return PlanRepository.get_by_id(plan_id)


class SubscriptionService:
    DEFAULT_DURATION_DAYS = 30

    @staticmethod
    def subscribe(tenant, plan_id, payment_method):
        from .exceptions import SubscriptionAlreadyActiveException

        if not tenant:
            raise NoTenantException()

        if SubscriptionRepository.get_active_for_tenant(tenant):
            raise SubscriptionAlreadyActiveException()

        plan = PlanRepository.get_by_id(plan_id)

        with transaction.atomic():
            subscription = SubscriptionRepository.create(tenant, plan, payment_method)
            strategy = PaymentStrategyFactory.get(payment_method)

            try:
                success = strategy.process(subscription)
            except Exception:
                subscription.status = "FAILED"
                subscription.save(update_fields=["status", "updated_at"])
                raise PaymentFailedException()

            if not success:
                subscription.status = "FAILED"
                subscription.save(update_fields=["status", "updated_at"])
                raise PaymentFailedException()

            subscription.status = "ACTIVE"
            subscription.start_date = timezone.now()
            subscription.end_date = timezone.now() + timedelta(days=SubscriptionService.DEFAULT_DURATION_DAYS)
            subscription.save(update_fields=["status", "start_date", "end_date", "updated_at"])
            return subscription

    @staticmethod
    def get_active_subscription(tenant):
        subscription = SubscriptionRepository.get_active_for_tenant(tenant)
        if not subscription:
            raise NoActiveSubscriptionException()
        return subscription

    @staticmethod
    def is_active(tenant):
        if not tenant:
            return False
        return SubscriptionRepository.get_active_for_tenant(tenant) is not None

    @staticmethod
    def get_max_users_for_tenant(tenant):
        if not tenant:
            return 1
        subscription = SubscriptionRepository.get_active_for_tenant(tenant)
        return subscription.plan.max_users if subscription else 1

    @staticmethod
    def list_history(tenant):
        return SubscriptionRepository.list_for_tenant(tenant)