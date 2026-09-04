from rest_framework import serializers
from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "address", "business_type", "email", "phone", "is_active", "created_at", "updated_at"]


class ShopSetupSerializer(serializers.Serializer):
    shop_name = serializers.CharField(max_length=200)
    shop_address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    business_type = serializers.CharField(required=False, allow_blank=True, max_length=100)
    
class TenantUpdateSerializer(serializers.Serializer):
    address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    business_type = serializers.CharField(required=False, allow_blank=True, max_length=100)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=15)
    


