from rest_framework import serializers
from .models import Category, Product
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "tenant", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["tenant"]

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    payment_method = serializers.ChoiceField(
        choices=["CASH", "CARD", "ONLINE"], required=False, write_only=True, default="CASH"
    )
    is_opening_stock = serializers.BooleanField(required=False, write_only=True, default=False)
    supplier_name = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=150)
    paid_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, write_only=True, min_value=0
    )

    class Meta:
        model = Product
        fields = [
            "id", "tenant", "category", "category_name", "name", "barcode",
            "price", "cost_price", "stock", "description", "is_active",
            "sku", "created_at", "updated_at", "payment_method", "is_opening_stock",
            "supplier_name", "paid_amount",
        ]
        read_only_fields = ["sku", "barcode", "tenant"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request.user, "tenant") and "category" in self.fields:
            self.fields["category"].queryset = Category.objects.filter(tenant=request.user.tenant)

    def validate_category(self, value):
        request = self.context.get("request")
        tenant = getattr(request.user, "tenant", None) if request else None
        if tenant and value.tenant != tenant:
            raise serializers.ValidationError("Yeh category aapke store ki nahi hai.")
        return value

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
    unit_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    payment_method = serializers.ChoiceField(
        choices=["CASH", "CARD", "ONLINE"], required=False, default="CASH"
    )
    supplier_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    paid_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True, min_value=0
    )