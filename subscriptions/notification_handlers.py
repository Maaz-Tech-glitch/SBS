from notifications.models import Notification
from notifications.services import NotificationService


class SubscriptionNotificationService:
    ACTION_URL = "/subscription"

    @staticmethod
    def _safe_subscription_data(subscription):
        if subscription is None:
            return {}

        plan = getattr(subscription, "plan", None)

        return {
            "subscription_id": getattr(subscription, "pk", None),
            "plan_id": getattr(subscription, "plan_id", None),
            "plan_name": getattr(plan, "name", ""),
            "status": getattr(subscription, "status", ""),
            "payment_method": getattr(subscription, "payment_method", ""),
            "start_date": (
                subscription.start_date.isoformat()
                if getattr(subscription, "start_date", None)
                else None
            ),
            "end_date": (
                subscription.end_date.isoformat()
                if getattr(subscription, "end_date", None)
                else None
            ),
        }

    @staticmethod
    def _already_exists(*, tenant, dedupe_key):
        return Notification.objects.filter(
            tenant=tenant,
            dedupe_key=dedupe_key,
        ).exists()

    @classmethod
    def subscription_activated(
        cls,
        *,
        subscription,
        actor,
    ):
        tenant = subscription.tenant
        data = cls._safe_subscription_data(subscription)

        NotificationService.create(
            tenant=tenant,
            actor=actor,
            title="Subscription Activated",
            message=(
                f"{data.get('plan_name') or 'Subscription'} "
                f"was activated successfully."
            ),
            event_type="SUBSCRIPTION_ACTIVATED",
            level=Notification.Level.SUCCESS,
            entity_type="SUBSCRIPTION",
            entity_id=subscription.pk,
            action_url=cls.ACTION_URL,
            metadata=data,
            dedupe_key=(
                f"subscription:{subscription.pk}:activated"
            ),
            dedupe_unread=True,
        )

    @classmethod
    def payment_failed(
        cls,
        *,
        tenant,
        actor,
        plan_id,
        payment_method,
        error,
    ):
        safe_error = str(error)[:300]

        NotificationService.create(
            tenant=tenant,
            actor=actor,
            title="Subscription Payment Failed",
            message="Subscription payment could not be completed.",
            event_type="SUBSCRIPTION_PAYMENT_FAILED",
            level=Notification.Level.ERROR,
            entity_type="SUBSCRIPTION",
            action_url=cls.ACTION_URL,
            metadata={
                "plan_id": plan_id,
                "payment_method": payment_method,
                "error": safe_error,
            },
        )

    @classmethod
    def expiry_near(
        cls,
        *,
        subscription,
        days_remaining,
    ):
        tenant = subscription.tenant
        dedupe_key = (
            f"subscription:{subscription.pk}:expiry-near"
        )

        # Exactly one expiry-near alert per subscription,
        # even if the admin reads the first one.
        if cls._already_exists(
            tenant=tenant,
            dedupe_key=dedupe_key,
        ):
            return False

        data = cls._safe_subscription_data(subscription)

        NotificationService.create(
            tenant=tenant,
            actor=None,
            title="Subscription Expiring Soon",
            message=(
                f"{data.get('plan_name') or 'Subscription'} "
                f"will expire in {days_remaining} day(s)."
            ),
            event_type="SUBSCRIPTION_EXPIRY_NEAR",
            level=Notification.Level.WARNING,
            entity_type="SUBSCRIPTION",
            entity_id=subscription.pk,
            action_url=cls.ACTION_URL,
            metadata={
                **data,
                "days_remaining": days_remaining,
            },
            dedupe_key=dedupe_key,
        )

        return True

    @classmethod
    def expired(
        cls,
        *,
        subscription,
    ):
        tenant = subscription.tenant
        dedupe_key = (
            f"subscription:{subscription.pk}:expired"
        )

        if cls._already_exists(
            tenant=tenant,
            dedupe_key=dedupe_key,
        ):
            return False

        data = cls._safe_subscription_data(subscription)

        NotificationService.create(
            tenant=tenant,
            actor=None,
            title="Subscription Expired",
            message=(
                f"{data.get('plan_name') or 'Subscription'} "
                f"has expired."
            ),
            event_type="SUBSCRIPTION_EXPIRED",
            level=Notification.Level.CRITICAL,
            entity_type="SUBSCRIPTION",
            entity_id=subscription.pk,
            action_url=cls.ACTION_URL,
            metadata=data,
            dedupe_key=dedupe_key,
        )

        return True

    @classmethod
    def subscription_cancelled(
        cls,
        *,
        subscription,
        actor,
    ):
        tenant = subscription.tenant
        data = cls._safe_subscription_data(
            subscription
        )

        NotificationService.create(
            tenant=tenant,
            actor=actor,
            title="Subscription Cancelled",
            message=(
                f"{data.get('plan_name') or 'Subscription'} "
                f"was cancelled."
            ),
            event_type="SUBSCRIPTION_CANCELLED",
            level=Notification.Level.WARNING,
            entity_type="SUBSCRIPTION",
            entity_id=subscription.pk,
            action_url=cls.ACTION_URL,
            metadata=data,
            dedupe_key=(
                f"subscription:{subscription.pk}:cancelled"
            ),
            dedupe_unread=True,
        )
