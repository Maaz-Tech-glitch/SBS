from rest_framework import serializers

from .models import (
    Plan,
    Subscription,
)

from .repositories import (
    SubscriptionRepository,
)


# =========================================================
# PLAN
# =========================================================

class PlanSerializer(
    serializers.ModelSerializer
):

    trial_available = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = Plan

        fields = [
            "id",
            "name",
            "price",
            "max_users",
            "features",
            "trial_days",
            "trial_available",
            "is_active",
        ]

    def get_trial_available(
        self,
        plan
    ):
        if plan.trial_days <= 0:
            return False

        request = (
            self.context.get(
                "request"
            )
        )

        if (
            not request
            or not request.user
            or not request.user.is_authenticated
        ):
            return False

        tenant = getattr(
            request.user,
            "tenant",
            None
        )

        if not tenant:
            return False

        return not (
            SubscriptionRepository
            .has_used_trial(
                tenant,
                plan
            )
        )


# =========================================================
# SUBSCRIPTION
# =========================================================

class SubscriptionSerializer(
    serializers.ModelSerializer
):

    plan_name = serializers.CharField(
        source="plan.name",
        read_only=True
    )

    max_users = serializers.IntegerField(
        source="plan.max_users",
        read_only=True
    )

    class Meta:
        model = Subscription

        fields = [
            "id",
            "tenant",
            "plan",
            "plan_name",
            "max_users",
            "start_date",
            "end_date",
            "status",
            "payment_method",
            "transaction_id",
            "created_at",
        ]

        read_only_fields = [
            "transaction_id",
            "status",
            "start_date",
            "end_date",
        ]


# =========================================================
# SUBSCRIBE
# =========================================================

class SubscribeSerializer(
    serializers.Serializer
):

    plan_id = serializers.IntegerField()

    payment_method = (
        serializers.ChoiceField(
            choices=[
                "CASH",
                "CARD",
                "ONLINE",
            ],
            required=False
        )
    )

    use_trial = serializers.BooleanField(
        required=False,
        default=False
    )

    def validate(self, data):

        use_trial = data.get(
            "use_trial",
            False
        )

        payment_method = data.get(
            "payment_method"
        )

        # Paid subscription needs payment method
        if (
            not use_trial
            and not payment_method
        ):
            raise serializers.ValidationError({
                "payment_method":
                    "Payment method is required for paid plans."
            })

        return data