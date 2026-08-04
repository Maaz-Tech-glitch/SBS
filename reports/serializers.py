from rest_framework import serializers

class DailySalesReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10,decimal_places=2)
    invoices = serializers.ListField()


class MonthlySalesReportSerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15,decimal_places=2)
    invoices = serializers.ListField()


class YearlySalesReportSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15,decimal_places=2)
    invoices = serializers.ListField()