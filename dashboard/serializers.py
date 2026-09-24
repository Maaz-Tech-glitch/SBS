# from rest_framework import serializers

# class DashboardSummarySerializer(serializers.Serializer):
#     total_products = serializers.IntegerField()
#     low_stock_products = serializers.IntegerField()
#     out_of_stock_products = serializers.IntegerField()
#     total_sales_today = serializers.IntegerField()
#     total_revenue_today = serializers.DecimalField(max_digits=10,decimal_places=2)
#     pending_invoices = serializers.IntegerField()

from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_products = serializers.IntegerField()

    low_stock_products = serializers.IntegerField()

    out_of_stock_products = serializers.IntegerField()

    total_sales_today = serializers.IntegerField()

    total_revenue_today = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    total_profit_today = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    pending_invoices = serializers.IntegerField()