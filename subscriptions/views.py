from rest_framework import status

from rest_framework.generics import (
    ListAPIView,
)

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.response import (
    Response,
)

from rest_framework.views import (
    APIView,
)

from users.permissions import IsAdmin

from .serializers import (
    PlanSerializer,
    SubscriptionSerializer,
    SubscribeSerializer,
)

from .services import (
    PlanService,
    SubscriptionService,
)


# =========================================================
# PLANS
# =========================================================

class PlanListAPIView(
    ListAPIView
):
    serializer_class = (
        PlanSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            PlanService
            .list_plans()
        )


# =========================================================
# SUBSCRIBE
# =========================================================

class SubscribeAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def get(self, request):

        subscriptions = (
            SubscriptionService
            .list_history(
                request.user.tenant
            )
        )

        serializer = (
            SubscriptionSerializer(
                subscriptions,
                many=True
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    def post(self, request):

        serializer = (
            SubscribeSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = (
            serializer.validated_data
        )

        subscription = (
            SubscriptionService
            .subscribe(
                tenant=
                    request.user.tenant,

                plan_id=
                    data["plan_id"],

                payment_method=
                    data.get(
                        "payment_method"
                    ),

                use_trial=
                    data.get(
                        "use_trial",
                        False
                    ),
            )
        )

        return Response(
            {
                "message":
                    "Subscription activated successfully",

                "data":
                    SubscriptionSerializer(
                        subscription
                    ).data,
            },

            status=
                status.HTTP_201_CREATED
        )


# =========================================================
# ACTIVE
# =========================================================

class CurrentSubscriptionAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        subscription = (
            SubscriptionService
            .get_active_subscription(
                request.user.tenant
            )
        )

        return Response(
            SubscriptionSerializer(
                subscription
            ).data
        )


# =========================================================
# HISTORY
# =========================================================

class SubscriptionHistoryAPIView(
    ListAPIView
):
    serializer_class = (
        SubscriptionSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return (
            SubscriptionService
            .list_history(
                self.request
                .user
                .tenant
            )
        )
        
        
class CancelSubscriptionAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def post(self, request):

        subscription = (
            SubscriptionService
            .cancel_subscription(
                request.user.tenant
            )
        )

        return Response(
            {
                "message":
                    "Subscription cancelled successfully",

                "data":
                    SubscriptionSerializer(
                        subscription
                    ).data,
            },
            status=status.HTTP_200_OK,
        )