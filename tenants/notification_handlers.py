from django.db import transaction

from notifications.models import Notification
from notifications.services import NotificationService


class ShopSettingsNotificationService:
    ACTION_URL = "/shop"

    @staticmethod
    def _schedule(callback):
        transaction.on_commit(
            callback,
            robust=True,
        )

    @staticmethod
    def _safe_tenant_data(tenant):
        if tenant is None:
            return {}

        return {
            "tenant_id": getattr(tenant, "pk", None),
            "shop_name": getattr(tenant, "name", ""),
        }

    @classmethod
    def schedule_updated(
        cls,
        *,
        tenant,
        actor,
        changed_fields,
    ):
        fields = sorted(set(changed_fields or []))

        if not fields:
            return

        safe_data = cls._safe_tenant_data(tenant)
        actor_name = getattr(actor, "username", "User")

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Shop Settings Updated",
                message=(
                    f"Shop settings were updated by {actor_name}."
                ),
                event_type="SHOP_SETTINGS_UPDATED",
                level=Notification.Level.SUCCESS,
                entity_type="TENANT",
                entity_id=tenant.pk,
                action_url=cls.ACTION_URL,
                metadata={
                    **safe_data,
                    "changed_fields": fields,
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_failure(
        cls,
        *,
        tenant,
        actor,
        error,
    ):
        if tenant is None:
            return

        safe_data = cls._safe_tenant_data(tenant)
        safe_error = str(error)[:300]

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Shop Settings Update Failed",
                message="Shop settings could not be updated.",
                event_type="SHOP_SETTINGS_UPDATE_FAILED",
                level=Notification.Level.ERROR,
                entity_type="TENANT",
                entity_id=tenant.pk,
                action_url=cls.ACTION_URL,
                metadata={
                    **safe_data,
                    "error": safe_error,
                },
            )

        cls._schedule(create_notification)
