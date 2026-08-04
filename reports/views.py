from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import DailySalesReportSerializer , MonthlySalesReportSerializer , YearlySalesReportSerializer
from .services import daily_sales_report , monthly_sales_report , yearly_sales_report


class DailySalesReportAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data = daily_sales_report(request.user)
        invoices = []
        for invoice in data["invoices"]:
            invoices.append({
                "invoice_number":invoice.invoice_number,
                "final_amount":invoice.final_amount
            })
        response = {
            "date": data["date"],
            "total_sales":data["total_sales"],
            "total_revenue":data["total_revenue"],
            "invoices":invoices,
        }
        serializer = (DailySalesReportSerializer(response))
        return Response(serializer.data)
    
    
class MonthlySalesReportAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data = monthly_sales_report(request.user)
        invoices = []
        for invoice in data["invoices"]:
            invoices.append({
                "invoice_number":invoice.invoice_number,
                "final_amount":invoice.final_amount
                    })
        response = {
            "month": data["month"],
            "year": data["year"],
            "total_sales":data["total_sales"],
            "total_revenue":data["total_revenue"],
            "invoices":invoices,
        }
        serializer = (MonthlySalesReportSerializer(response))
        return Response(serializer.data)


class YearlySalesReportAPIView(APIView):
    permission_classes =[IsAuthenticated]
    def get(self, request):
        data = yearly_sales_report(request.user)
        invoices = []
        for invoice in data["invoices"]:
            invoices.append({
                "invoice_number":invoice.invoice_number,
                "final_amount":invoice.final_amount
            })
        response = {
            "year": data["year"],
            "total_sales":data["total_sales"],
            "total_revenue":data["total_revenue"],
            "invoices":invoices,
        }
        serializer = (YearlySalesReportSerializer(response))
        return Response(serializer.data)