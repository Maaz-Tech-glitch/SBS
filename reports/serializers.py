# from rest_framework import serializers


# class InvoiceSummarySerializer(serializers.Serializer):
#     invoice_number = serializers.CharField()
#     final_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


# class DailySalesReportSerializer(serializers.Serializer):
#     date = serializers.DateField()
#     total_sales = serializers.IntegerField()
#     total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
#     invoices = InvoiceSummarySerializer(many=True)


# class MonthlySalesReportSerializer(serializers.Serializer):
#     month = serializers.CharField()
#     year = serializers.IntegerField()
#     total_sales = serializers.IntegerField()
#     total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
#     invoices = InvoiceSummarySerializer(many=True)


# class YearlySalesReportSerializer(serializers.Serializer):
#     year = serializers.IntegerField()
#     total_sales = serializers.IntegerField()
#     total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
#     invoices = InvoiceSummarySerializer(many=True)
    
    
# class RevenueTrendSerializer(serializers.Serializer):
#     labels = serializers.ListField(child=serializers.CharField())
#     revenue = serializers.ListField(child=serializers.DecimalField(max_digits=12, decimal_places=2))
#     sales_count = serializers.ListField(child=serializers.IntegerField())


# class CategorySalesSerializer(serializers.Serializer):
#     category = serializers.CharField()
#     revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
#     quantity = serializers.IntegerField()


# class PaymentMethodSplitSerializer(serializers.Serializer):
#     payment_method = serializers.CharField()
#     revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
#     count = serializers.IntegerField()


# class TopProductSerializer(serializers.Serializer):
#     product = serializers.CharField()
#     quantity_sold = serializers.IntegerField()
#     revenue = serializers.DecimalField(max_digits=12, decimal_places=2)

from rest_framework import serializers


class InvoiceSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    invoice_number = serializers.CharField()
    customer_name = serializers.CharField(
        allow_blank=True
    )
    final_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    payment_method = serializers.CharField(
        allow_blank=True
    )
    created_at = serializers.DateTimeField()


class DailySalesReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    invoices = InvoiceSummarySerializer(
        many=True
    )


class MonthlySalesReportSerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    invoices = InvoiceSummarySerializer(
        many=True
    )


class YearlySalesReportSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    invoices = InvoiceSummarySerializer(
        many=True
    )


class RevenueTrendSerializer(serializers.Serializer):
    labels = serializers.ListField(
        child=serializers.CharField()
    )
    revenue = serializers.ListField(
        child=serializers.DecimalField(
            max_digits=15,
            decimal_places=2,
        )
    )
    sales_count = serializers.ListField(
        child=serializers.IntegerField()
    )


class CategorySalesSerializer(serializers.Serializer):
    category = serializers.CharField()
    revenue = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    quantity = serializers.IntegerField()


class PaymentMethodSplitSerializer(serializers.Serializer):
    payment_method = serializers.CharField()
    revenue = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    count = serializers.IntegerField()


class TopProductSerializer(serializers.Serializer):
    product = serializers.CharField()
    quantity_sold = serializers.IntegerField()
    revenue = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )


class ReportRangeQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    top_limit = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=20,
        default=5,
    )

    def validate(self, attrs):
        start_date = attrs["start_date"]
        end_date = attrs["end_date"]

        if start_date > end_date:
            raise serializers.ValidationError(
                {
                    "end_date":
                        "End date must be on or after start date."
                }
            )

        days = (
            end_date - start_date
        ).days + 1

        if days > 366:
            raise serializers.ValidationError(
                "Report date range cannot exceed 366 days."
            )

        return attrs


class ReportInvoiceQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    search = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    payment_method = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=[
            "CASH",
            "CARD",
            "ONLINE",
        ],
        default="",
    )

    def validate(self, attrs):
        start_date = attrs["start_date"]
        end_date = attrs["end_date"]

        if start_date > end_date:
            raise serializers.ValidationError(
                {
                    "end_date":
                        "End date must be on or after start date."
                }
            )

        if (
            end_date - start_date
        ).days + 1 > 366:
            raise serializers.ValidationError(
                "Report date range cannot exceed 366 days."
            )

        return attrs


class ReportSummarySerializer(serializers.Serializer):
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    average_sale = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    items_sold = serializers.IntegerField()


class ReportComparisonSerializer(serializers.Serializer):
    previous_start_date = serializers.DateField()
    previous_end_date = serializers.DateField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    sales_change_percent = serializers.FloatField(
        allow_null=True
    )
    revenue_change_percent = serializers.FloatField(
        allow_null=True
    )


class DailyBreakdownSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    average_sale = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )


class EnhancedReportSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    days = serializers.IntegerField()

    summary = ReportSummarySerializer()
    comparison = ReportComparisonSerializer()
    daily_breakdown = DailyBreakdownSerializer(
        many=True
    )
    category_sales = CategorySalesSerializer(
        many=True
    )
    payment_methods = PaymentMethodSplitSerializer(
        many=True
    )
    top_products = TopProductSerializer(
        many=True
    )
