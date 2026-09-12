from rest_framework import serializers


class InvoiceSummarySerializer(serializers.Serializer):
    invoice_number = serializers.CharField()
    final_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class DailySalesReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    invoices = InvoiceSummarySerializer(many=True)


class MonthlySalesReportSerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    invoices = InvoiceSummarySerializer(many=True)


class YearlySalesReportSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    invoices = InvoiceSummarySerializer(many=True)
    
    
class RevenueTrendSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    revenue = serializers.ListField(child=serializers.DecimalField(max_digits=12, decimal_places=2))
    sales_count = serializers.ListField(child=serializers.IntegerField())


class CategorySalesSerializer(serializers.Serializer):
    category = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantity = serializers.IntegerField()


class PaymentMethodSplitSerializer(serializers.Serializer):
    payment_method = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()


class TopProductSerializer(serializers.Serializer):
    product = serializers.CharField()
    quantity_sold = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)