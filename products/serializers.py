from rest_framework import serializers
from .models import Category, Product
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "tenant", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["tenant"]

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    class Meta:
        model = Product
        fields = [
            "id", "tenant", "category", "category_name", "name", "barcode",
            "price", "stock", "description", "is_active",
            "sku", "created_at", "updated_at",
        ]
        read_only_fields = ["sku", "barcode", "tenant"]
    def validate_name(self, value):
        request = self.context.get("request")
        tenant = request.user.tenant if request else None
        queryset = Product.objects.filter(tenant=tenant, name=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A product with this name already exists in your store.")
        return value

class RestockProductSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)