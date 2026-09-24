from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .repositories import (
    PlanRepository,
    SubscriptionRepository,
)

from .strategies import (
    PaymentStrategyFactory,
)

from .exceptions import (
    NoActiveSubscriptionException,
    PaymentFailedException,
    NoTenantException,
    SubscriptionAlreadyActiveException,
    TrialNotAvailableException,
    TrialAlreadyUsedException,
)


# =========================================================
# PLAN
# =========================================================

class PlanService:

    @staticmethod
    def list_plans():
        return (
            PlanRepository
            .list_active()
        )

    @staticmethod
    def get_plan(plan_id):
        return (
            PlanRepository
            .get_by_id(plan_id)
        )


# =========================================================
# SUBSCRIPTION
# =========================================================

class SubscriptionService:

    DEFAULT_DURATION_DAYS = 30

    # =====================================================
    # SUBSCRIBE
    # =====================================================

    @staticmethod
    def subscribe(
        tenant,
        plan_id,
        payment_method=None,
        use_trial=False,
    ):

        if not tenant:
            raise NoTenantException()

        # ---------------------------------------------
        # Only one active subscription at a time
        # ---------------------------------------------

        if (
            SubscriptionRepository
            .get_active_for_tenant(
                tenant
            )
        ):
            raise SubscriptionAlreadyActiveException()

        # ---------------------------------------------
        # Plan
        # ---------------------------------------------

        plan = (
            PlanRepository
            .get_by_id(
                plan_id
            )
        )

        # =================================================
        # FREE TRIAL
        # =================================================

        if use_trial:

            # Plan does not support trial
            if plan.trial_days <= 0:
                raise TrialNotAvailableException()

            # Trial can only ever be used once
            if (
                SubscriptionRepository
                .has_used_trial(
                    tenant,
                    plan
                )
            ):
                raise TrialAlreadyUsedException()

            payment_method = "TRIAL"

            duration_days = (
                plan.trial_days
            )

        # =================================================
        # PAID SUBSCRIPTION
        # =================================================

        else:

            if not payment_method:
                raise PaymentFailedException(
                    "Payment method is required."
                )

            duration_days = (
                SubscriptionService
                .DEFAULT_DURATION_DAYS
            )


        # =================================================
        # CREATE SUBSCRIPTION
        # =================================================

        with transaction.atomic():

            subscription = (
                SubscriptionRepository
                .create(
                    tenant,
                    plan,
                    payment_method
                )
            )

            # =============================================
            # TRIAL = NO PAYMENT PROCESSING
            # =============================================

            if use_trial:
                success = True

            # =============================================
            # PAID
            # =============================================

            else:

                strategy = (
                    PaymentStrategyFactory
                    .get(
                        payment_method
                    )
                )

                try:
                    success = (
                        strategy.process(
                            subscription
                        )
                    )

                except Exception:

                    subscription.status = (
                        "FAILED"
                    )

                    subscription.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )

                    raise PaymentFailedException()


            if not success:

                subscription.status = (
                    "FAILED"
                )

                subscription.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                raise PaymentFailedException()


            # =============================================
            # ACTIVATE
            # =============================================

            subscription.status = (
                "ACTIVE"
            )

            subscription.start_date = (
                timezone.now()
            )

            subscription.end_date = (
                timezone.now()
                + timedelta(
                    days=duration_days
                )
            )

            subscription.save(
                update_fields=[
                    "payment_method",
                    "status",
                    "start_date",
                    "end_date",
                    "updated_at",
                ]
            )

            return subscription


    # =====================================================
    # ACTIVE
    # =====================================================

    @staticmethod
    def get_active_subscription(
        tenant
    ):

        subscription = (
            SubscriptionRepository
            .get_active_for_tenant(
                tenant
            )
        )

        if not subscription:
            raise NoActiveSubscriptionException()

        return subscription


    # =====================================================
    # CHECK ACTIVE
    # =====================================================

    @staticmethod
    def is_active(tenant):

        if not tenant:
            return False

        return (
            SubscriptionRepository
            .get_active_for_tenant(
                tenant
            )
            is not None
        )


    # =====================================================
    # MAX USERS
    # =====================================================

    @staticmethod
    def get_max_users_for_tenant(
        tenant
    ):

        if not tenant:
            return 1

        subscription = (
            SubscriptionRepository
            .get_active_for_tenant(
                tenant
            )
        )

        if not subscription:
            return 1

        return (
            subscription
            .plan
            .max_users
        )


    # =====================================================
    # HISTORY
    # =====================================================

    @staticmethod
    def list_history(tenant):

        return (
            SubscriptionRepository
            .list_for_tenant(
                tenant
            )
        )
        
        
    # =========================================================
# CANCEL / UNSUBSCRIBE
# =========================================================

    @staticmethod
    def cancel_subscription(tenant):
        if not tenant:
            raise NoTenantException()

        subscription = (
            SubscriptionRepository
            .get_active_for_tenant(
                tenant
            )
        )

        if not subscription:
            raise NoActiveSubscriptionException()

        subscription.status = "CANCELLED"
        subscription.end_date = timezone.now()

        subscription.save(
            update_fields=[
                "status",
                "end_date",
                "updated_at",
            ]
        )

        return subscription