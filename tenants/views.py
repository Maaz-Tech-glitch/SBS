from django.db import transaction

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import TenantSerializer, TenantUpdateSerializer
from .services import TenantService
from .notification_handlers import ShopSettingsNotificationService


class TenantAPIView(APIView):
    """Logged-in user apni shop ki details dekh/update kar sake."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = request.user.tenant
        return Response(
            TenantSerializer(tenant).data
        )

    def patch(self, request):
        tenant = request.user.tenant

        serializer = TenantUpdateSerializer(
            data=request.data,
            partial=True,
        )

        # Simple request/serializer validation remains normal API validation.
        # It does not create notification spam.
        serializer.is_valid(
            raise_exception=True
        )

        changed_fields = [
            field
            for field, value
            in serializer.validated_data.items()
            if getattr(
                tenant,
                field,
                None,
            ) != value
        ]

        try:
            with transaction.atomic():
                updated_tenant = (
                    TenantService
                    .update_tenant(
                        tenant,
                        **serializer.validated_data,
                    )
                )

                ShopSettingsNotificationService.schedule_updated(
                    tenant=updated_tenant,
                    actor=request.user,
                    changed_fields=changed_fields,
                )

        except Exception as exc:
            ShopSettingsNotificationService.schedule_failure(
                tenant=tenant,
                actor=request.user,
                error=exc,
            )
            raise

        return Response(
            {
                "message":
                    "Shop details updated successfully",

                "data":
                    TenantSerializer(
                        updated_tenant
                    ).data,
            },
            status=status.HTTP_200_OK,
        )
