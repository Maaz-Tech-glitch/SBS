from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ShopSetupSerializer, TenantSerializer
from .services import TenantService


class ShopSetupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ShopSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tenant = TenantService.setup_shop(
            user=request.user,
            name=data["shop_name"],
            address=data.get("shop_address", ""),
            business_type=data.get("business_type", ""),
        )
        return Response(
            {"message": "Shop setup completed successfully", "tenant": TenantSerializer(tenant).data},
            status=status.HTTP_201_CREATED,
        )