from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "event_type",
            "level",
            "actor_name",
            "entity_type",
            "entity_id",
            "action_url",
            "metadata",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj):
        if not obj.actor:
            return ""

        full_name = obj.actor.get_full_name().strip()

        return full_name or obj.actor.username
