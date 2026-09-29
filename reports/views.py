from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .services import  SalesReportService, ChartDataService
from subscriptions.permissions import IsSubscriptionActive
from users.permissions import HasModuleAccess
from .serializers import (
    DailySalesReportSerializer, MonthlySalesReportSerializer, YearlySalesReportSerializer,
    RevenueTrendSerializer, CategorySalesSerializer, PaymentMethodSplitSerializer, TopProductSerializer,
)



class DailySalesReportAPIView(APIView):
    required_module = "reports"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def get(self, request):
        data = SalesReportService.daily(request.user)
        return Response(DailySalesReportSerializer(data).data)


class MonthlySalesReportAPIView(APIView):
    required_module = "reports"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def get(self, request):
        data = SalesReportService.monthly(request.user)
        return Response(MonthlySalesReportSerializer(data).data)


class YearlySalesReportAPIView(APIView):
    required_module = "reports"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def get(self, request):
        data = SalesReportService.yearly(request.user)
        return Response(YearlySalesReportSerializer(data).data)
    
    


class RevenueTrendChartAPIView(APIView):
    required_module = "reports"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        group_by = request.query_params.get("group_by", "day")  # "day" | "month"
        data = ChartDataService.revenue_trend(request.user, days=days, group_by=group_by)
        return Response(RevenueTrendSerializer(data).data)


class CategorySalesChartAPIView(APIView):
    required_module = "reports"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        data = ChartDataService.category_sales(request.user, days=days)
        return Response(CategorySalesSerializer(data, many=True).data)


class PaymentMethodChartAPIView(APIView):
    required_module = "reports"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        data = ChartDataService.payment_method_split(request.user, days=days)
        return Response(PaymentMethodSplitSerializer(data, many=True).data)


class TopProductsChartAPIView(APIView):
    required_module = "reports"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        limit = int(request.query_params.get("limit", 10))
        data = ChartDataService.top_products(request.user, days=days, limit=limit)
        return Response(TopProductSerializer(data, many=True).data)