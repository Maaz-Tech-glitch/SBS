from rest_framework import serializers
from .models import Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "name", "price", "max_users",  "features", "is_active"]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    max_users = serializers.IntegerField(source="plan.max_users", read_only=True)
    class Meta:
        model = Subscription
        fields = [
            "id", "tenant", "plan", "plan_name","max_users",  "start_date", "end_date",
            "status", "payment_method", "transaction_id", "created_at",
            
        ]
        read_only_fields = ["transaction_id", "status", "start_date", "end_date"]


class SubscribeSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=["CASH", "CARD", "ONLINE"])