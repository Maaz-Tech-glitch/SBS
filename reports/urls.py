from django.urls import path
from .views import DailySalesReportAPIView , MonthlySalesReportAPIView , YearlySalesReportAPIView

urlpatterns = [
    path("daily-sales/",DailySalesReportAPIView.as_view(),name="daily-sales",),
    path("monthly-sales/",MonthlySalesReportAPIView.as_view(),name="monthly-sales",),
    path("yearly-sales/",YearlySalesReportAPIView.as_view(),name="yearly-sales",),
    ]





