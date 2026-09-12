# from django.urls import path
# from .views import DailySalesReportAPIView , MonthlySalesReportAPIView , YearlySalesReportAPIView

# urlpatterns = [
#     path("daily-sales/",DailySalesReportAPIView.as_view(),name="daily-sales",),
#     path("monthly-sales/",MonthlySalesReportAPIView.as_view(),name="monthly-sales",),
#     path("yearly-sales/",YearlySalesReportAPIView.as_view(),name="yearly-sales",),
#     ]

from django.urls import path
from .views import (
    DailySalesReportAPIView, MonthlySalesReportAPIView, YearlySalesReportAPIView,
    RevenueTrendChartAPIView, CategorySalesChartAPIView,
    PaymentMethodChartAPIView, TopProductsChartAPIView,
)

urlpatterns = [
    path("daily-sales/", DailySalesReportAPIView.as_view(), name="daily-sales"),
    path("monthly-sales/", MonthlySalesReportAPIView.as_view(), name="monthly-sales"),
    path("yearly-sales/", YearlySalesReportAPIView.as_view(), name="yearly-sales"),

    path("charts/revenue-trend/", RevenueTrendChartAPIView.as_view(), name="chart-revenue-trend"),
    path("charts/category-sales/", CategorySalesChartAPIView.as_view(), name="chart-category-sales"),
    path("charts/payment-methods/", PaymentMethodChartAPIView.as_view(), name="chart-payment-methods"),
    path("charts/top-products/", TopProductsChartAPIView.as_view(), name="chart-top-products"),
]