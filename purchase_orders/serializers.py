from django.db import transaction
from rest_framework import serializers

from products.models import Product

from .models import PurchaseOrder, PurchaseOrderItem, Supplier


class PurchaseOrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "stock"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id", "name", "phone", "whatsapp_number", "email", "address",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    current_stock = serializers.IntegerField(source="product.stock", read_only=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.none())

    class Meta:
        model = PurchaseOrderItem
        fields = ["id", "product", "product_name", "current_stock", "quantity"]
        read_only_fields = ["id", "product_name", "current_stock"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and getattr(request.user, "tenant_id", None):
            self.fields["product"].queryset = Product.objects.filter(tenant=request.user.tenant)

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    supplier = serializers.CharField(source="supplier.name", read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "po_number", "supplier", "item_count", "status", "created_by",
            "created_at", "updated_at", "finalized_at",
        ]

    def get_created_by(self, obj):
        if not obj.created_by:
            return ""
        return obj.created_by.get_full_name() or obj.created_by.username


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        source="supplier", queryset=Supplier.objects.none(), write_only=True, required=False
    )
    items = PurchaseOrderItemSerializer(many=True, required=False)
    created_by = serializers.SerializerMethodField()
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "po_number", "status", "supplier", "supplier_id", "notes",
            "items", "item_count", "created_by", "created_at", "updated_at",
            "finalized_at",
        ]
        read_only_fields = [
            "id", "po_number", "status", "item_count", "created_at", "updated_at", "finalized_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        tenant_id = getattr(getattr(request, "user", None), "tenant_id", None)
        if tenant_id:
            self.fields["supplier_id"].queryset = Supplier.objects.filter(tenant_id=tenant_id, is_active=True)
            item_serializer = self.fields["items"].child
            item_serializer.fields["product"].queryset = Product.objects.filter(tenant_id=tenant_id)

    def get_created_by(self, obj):
        if not obj.created_by:
            return ""
        return obj.created_by.get_full_name() or obj.created_by.username

    def validate_items(self, items):
        if not items and self.instance is None:
            raise serializers.ValidationError("At least one product is required.")
        if not items and self.instance is not None:
            raise serializers.ValidationError("A purchase order must contain at least one product.")
        product_ids = [item["product"].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("A product can only appear once in a purchase order.")
        return items

    def validate(self, attrs):
        if self.instance is None:
            if "supplier" not in attrs:
                raise serializers.ValidationError({"supplier_id": "A supplier is required."})
            if not attrs.get("items"):
                raise serializers.ValidationError({"items": "At least one product is required."})
        elif "supplier" not in attrs and "items" not in attrs and "notes" not in attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items")
        request = self.context["request"]
        order = PurchaseOrder.objects.create(
            tenant=request.user.tenant,
            created_by=request.user,
            **validated_data,
        )
        PurchaseOrderItem.objects.bulk_create([
            PurchaseOrderItem(purchase_order=order, **item) for item in items
        ])
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context["request"]
        order = PurchaseOrder.objects.select_for_update().get(
            pk=instance.pk, tenant=request.user.tenant
        )
        if order.status != PurchaseOrder.Status.DRAFT:
            raise serializers.ValidationError("Only draft purchase orders can be edited.")

        items = validated_data.pop("items", None)
        for field, value in validated_data.items():
            setattr(order, field, value)
        order.save()

        if items is not None:
            order.items.all().delete()
            PurchaseOrderItem.objects.bulk_create([
                PurchaseOrderItem(purchase_order=order, **item) for item in items
            ])
        return order