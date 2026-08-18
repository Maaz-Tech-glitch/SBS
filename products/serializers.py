from rest_framework import serializers
from .models import Category, Product


# Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]


# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "category", "category_name", "name", "barcode",
            "price", "stock", "description", "is_active",
            "sku", "created_at", "updated_at",
        ]
        read_only_fields = ["sku", "barcode"]


class RestockProductSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)