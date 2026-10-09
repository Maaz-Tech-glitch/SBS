from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "event_type",
        "level",
        "title",
        "is_read",
        "created_at",
    )
    list_filter = (
        "level",
        "event_type",
        "is_read",
        "created_at",
    )
    search_fields = (
        "title",
        "message",
        "entity_id",
        "dedupe_key",
    )
    readonly_fields = (
        "created_at",
        "read_at",
    )
