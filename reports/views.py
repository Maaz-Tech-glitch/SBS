from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import DailySalesReportSerializer, MonthlySalesReportSerializer, YearlySalesReportSerializer
from .services import SalesReportService


class DailySalesReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = SalesReportService.daily(request.user)
        return Response(DailySalesReportSerializer(data).data)


class MonthlySalesReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = SalesReportService.monthly(request.user)
        return Response(MonthlySalesReportSerializer(data).data)


class YearlySalesReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = SalesReportService.yearly(request.user)
        return Response(YearlySalesReportSerializer(data).data)