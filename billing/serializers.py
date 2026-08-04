from rest_framework import serializers
from .models import Invoice, InvoiceItem


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"


def _format_discount(discount, discount_type):
    """Turns (10, 'PERCENTAGE') -> '10%' and (50, 'FIXED') -> 'Rs. 50'."""
    if discount_type == "PERCENTAGE":
        return f"{discount}%"
    return f"Rs. {discount}"


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    total_stock = serializers.IntegerField(source="product.stock", read_only=True)
    discount_display = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceItem
        fields = [
            "id", "product", "product_name", "quantity",
            "unit_price", "discount", "discount_type", "discount_display",
            "total_price", "total_stock",
        ]

    def get_discount_display(self, obj):
        return _format_discount(obj.discount, obj.discount_type)


class AddItemSerializer(serializers.Serializer):

    invoice_id = serializers.IntegerField(required=False, allow_null=True)
    customer_name = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=150
    )

    product_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(required=False, default=1, min_value=0)

    discount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True, min_value=0
    )
    discount_type = serializers.ChoiceField(
        choices=["FIXED", "PERCENTAGE"], required=False, allow_null=True
    )

    invoice_discount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True, min_value=0
    )
    invoice_discount_type = serializers.ChoiceField(
        choices=["FIXED", "PERCENTAGE"], required=False, allow_null=True
    )


class InvoiceDetailSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    discount_display = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "customer_name",
            "items",
            "total_amount",
            "discount",
            "discount_type",
            "discount_display",
            "final_amount",
            "status",
            "payment_method",
            "created_at",
        ]

    def get_discount_display(self, obj):
        return _format_discount(obj.discount, obj.discount_type)


class InvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight view for showing all open drafts (multiple customers)."""
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "customer_name",
            "status",
            "total_amount",
            "final_amount",
            "item_count",
            "created_at",
            "updated_at",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


class CompleteSaleSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=["CASH", "CARD", "ONLINE"])


class CancelInvoiceSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()