from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import  TenantSerializer, TenantUpdateSerializer
from .services import TenantService


class TenantAPIView(APIView):
    """Logged-in user apni shop ki details dekh/update kar sake."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = request.user.tenant
        return Response(TenantSerializer(tenant).data)

    def patch(self, request):
        tenant = request.user.tenant
        serializer = TenantUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_tenant = TenantService.update_tenant(tenant, **serializer.validated_data)
        return Response(
            {"message": "Shop details updated successfully", "data": TenantSerializer(updated_tenant).data},
            status=status.HTTP_200_OK,
        )