from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Notification


class NotificationService:
    @staticmethod
    def _safe_action_url(action_url):
        value = (action_url or "").strip()

        # Notifications should navigate only inside this SaaS.
        if value and not value.startswith("/"):
            return ""

        return value

    @staticmethod
    def create(
        *,
        tenant,
        title,
        message,
        event_type,
        level=Notification.Level.INFO,
        actor=None,
        entity_type="",
        entity_id="",
        action_url="",
        metadata=None,
        dedupe_key="",
        dedupe_unread=False,
    ):
        if tenant is None:
            raise ValueError("tenant is required for a notification.")

        clean_dedupe_key = (dedupe_key or "").strip()

        if dedupe_unread and clean_dedupe_key:
            existing = (
                Notification.objects
                .filter(
                    tenant=tenant,
                    dedupe_key=clean_dedupe_key,
                    is_read=False,
                )
                .order_by("-id")
                .first()
            )

            if existing:
                return existing, False

        notification = Notification.objects.create(
            tenant=tenant,
            actor=actor,
            title=str(title).strip(),
            message=str(message).strip(),
            event_type=str(event_type).strip().upper(),
            level=level,
            entity_type=str(entity_type or "").strip().upper(),
            entity_id=str(entity_id or "").strip(),
            action_url=NotificationService._safe_action_url(
                action_url
            ),
            metadata=metadata or {},
            dedupe_key=clean_dedupe_key,
        )

        return notification, True

    @staticmethod
    def mark_read(*, notification, tenant):
        if notification.tenant_id != tenant.id:
            return False

        return notification.mark_read()

    @staticmethod
    @transaction.atomic
    def mark_all_read(*, tenant):
        now = timezone.now()

        return (
            Notification.objects
            .filter(
                tenant=tenant,
                is_read=False,
            )
            .update(
                is_read=True,
                read_at=now,
            )
        )

    @staticmethod
    def cleanup_read_notifications(days=7):
        cutoff = timezone.now() - timedelta(days=days)

        deleted_count, _ = (
            Notification.objects
            .filter(
                is_read=True,
                read_at__lt=cutoff,
            )
            .delete()
        )

        return deleted_count
