from django.conf import settings
from django.db import models
from django.utils import timezone

from tenants.models import Tenant


class Notification(models.Model):
    class Level(models.TextChoices):
        INFO = "INFO", "Info"
        SUCCESS = "SUCCESS", "Success"
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"
        CRITICAL = "CRITICAL", "Critical"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="generated_notifications",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=200)
    message = models.TextField()

    event_type = models.CharField(
        max_length=100,
        db_index=True,
    )

    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.INFO,
        db_index=True,
    )

    entity_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    entity_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    action_url = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    # Optional key used by event integrations to avoid accidental duplicate
    # unread alerts such as repeated backend retries.
    dedupe_key = models.CharField(
        max_length=180,
        blank=True,
        default="",
        db_index=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
        db_index=True,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["tenant", "is_read", "-created_at"],
                name="notif_tenant_read_idx",
            ),
            models.Index(
                fields=["tenant", "event_type", "-created_at"],
                name="notif_tenant_event_idx",
            ),
        ]

    def mark_read(self):
        if self.is_read:
            return False

        self.is_read = True
        self.read_at = timezone.now()
        self.save(
            update_fields=[
                "is_read",
                "read_at",
            ]
        )
        return True

    def __str__(self):
        return f"{self.tenant_id} - {self.event_type} - {self.title}"
