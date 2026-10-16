from rest_framework import serializers
from .models import Invoice, InvoiceItem, SaleReturn, SaleReturnItem


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
    payment_method = serializers.ChoiceField(choices=["CASH", "CARD", "ONLINE"])

class SaleReturnItemInputSerializer(serializers.Serializer):
    invoice_item_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class CreateSaleReturnSerializer(serializers.Serializer):
    # The frontend must generate one UUID for a confirmation attempt and reuse
    # it if the same request is retried/double-clicked.
    request_id = serializers.UUIDField()
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        default="",
    )
    items = SaleReturnItemInputSerializer(
        many=True,
        allow_empty=False,
    )

    def validate_items(self, value):
        item_ids = [item["invoice_item_id"] for item in value]

        if len(item_ids) != len(set(item_ids)):
            raise serializers.ValidationError(
                "The same invoice item cannot appear more than once in one return."
            )

        return value


class SaleReturnItemSerializer(serializers.ModelSerializer):
    invoice_item_id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField(
        source="invoice_item.product_id",
        read_only=True,
    )
    product_name = serializers.CharField(
        source="invoice_item.product.name",
        read_only=True,
    )
    original_unit_price = serializers.DecimalField(
        source="invoice_item.unit_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = SaleReturnItem
        fields = [
            "id",
            "invoice_item_id",
            "product_id",
            "product_name",
            "quantity",
            "original_unit_price",
            "refund_unit_price",
            "refund_amount",
        ]


class SaleReturnSerializer(serializers.ModelSerializer):
    items = SaleReturnItemSerializer(many=True, read_only=True)
    invoice_number = serializers.CharField(
        source="invoice.invoice_number",
        read_only=True,
    )
    created_by_name = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:
        model = SaleReturn
        fields = [
            "id",
            "return_number",
            "request_id",
            "invoice",
            "invoice_number",
            "refund_method",
            "reason",
            "total_refund",
            "created_by_name",
            "items",
            "created_at",
        ]
        read_only_fields = fields

