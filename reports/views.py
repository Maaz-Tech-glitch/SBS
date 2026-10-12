# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from .services import  SalesReportService, ChartDataService
# from subscriptions.permissions import IsSubscriptionActive
# from users.permissions import HasModuleAccess
# from .serializers import (
#     DailySalesReportSerializer, MonthlySalesReportSerializer, YearlySalesReportSerializer,
#     RevenueTrendSerializer, CategorySalesSerializer, PaymentMethodSplitSerializer, TopProductSerializer,
# )



# class DailySalesReportAPIView(APIView):
#     required_module = "reports"
#     permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
#     def get(self, request):
#         data = SalesReportService.daily(request.user)
#         return Response(DailySalesReportSerializer(data).data)


# class MonthlySalesReportAPIView(APIView):
#     required_module = "reports"
#     permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
#     def get(self, request):
#         data = SalesReportService.monthly(request.user)
#         return Response(MonthlySalesReportSerializer(data).data)


# class YearlySalesReportAPIView(APIView):
#     required_module = "reports"
#     permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
#     def get(self, request):
#         data = SalesReportService.yearly(request.user)
#         return Response(YearlySalesReportSerializer(data).data)
    
    


# class RevenueTrendChartAPIView(APIView):
#     required_module = "reports"
#     permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
#     def get(self, request):
#         days = int(request.query_params.get("days", 30))
#         group_by = request.query_params.get("group_by", "day")  # "day" | "month"
#         data = ChartDataService.revenue_trend(request.user, days=days, group_by=group_by)
#         return Response(RevenueTrendSerializer(data).data)


# class CategorySalesChartAPIView(APIView):
#     required_module = "reports"
#     permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
#     def get(self, request):
#         days = int(request.query_params.get("days", 30))
#         data = ChartDataService.category_sales(request.user, days=days)
#         return Response(CategorySalesSerializer(data, many=True).data)


# class PaymentMethodChartAPIView(APIView):
#     required_module = "reports"
#     permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]

#     def get(self, request):
#         days = int(request.query_params.get("days", 30))
#         data = ChartDataService.payment_method_split(request.user, days=days)
#         return Response(PaymentMethodSplitSerializer(data, many=True).data)


# class TopProductsChartAPIView(APIView):
#     required_module = "reports"
#     permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
#     def get(self, request):
#         days = int(request.query_params.get("days", 30))
#         limit = int(request.query_params.get("limit", 10))
#         data = ChartDataService.top_products(request.user, days=days, limit=limit)
#         return Response(TopProductSerializer(data, many=True).data)



from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from subscriptions.permissions import IsSubscriptionActive
from users.permissions import HasModuleAccess

from .serializers import (
    CategorySalesSerializer,
    DailySalesReportSerializer,
    EnhancedReportSerializer,
    InvoiceSummarySerializer,
    MonthlySalesReportSerializer,
    PaymentMethodSplitSerializer,
    ReportInvoiceQuerySerializer,
    ReportRangeQuerySerializer,
    RevenueTrendSerializer,
    TopProductSerializer,
    YearlySalesReportSerializer,
)
from .services import (
    ChartDataService,
    EnhancedReportService,
    SalesReportService,
)


class ReportsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class DailySalesReportAPIView(APIView):
    required_module = "reports"
    permission_classes = [
        IsAuthenticated,
        IsSubscriptionActive,
        HasModuleAccess,
    ]

    def get(self, request):
        data = SalesReportService.daily(
            request.user
        )
        return Response(
            DailySalesReportSerializer(
                data
            ).data
        )


class MonthlySalesReportAPIView(APIView):
    required_module = "reports"
    permission_classes = [
        IsAuthenticated,
        IsSubscriptionActive,
        HasModuleAccess,
    ]

    def get(self, request):
        data = SalesReportService.monthly(
            request.user
        )
        return Response(
            MonthlySalesReportSerializer(
                data
            ).data
        )


class YearlySalesReportAPIView(APIView):
    required_module = "reports"
    permission_classes = [
        IsAuthenticated,
        IsSubscriptionActive,
        HasModuleAccess,
    ]

    def get(self, request):
        data = SalesReportService.yearly(
            request.user
        )
        return Response(
            YearlySalesReportSerializer(
                data
            ).data
        )


class EnhancedSalesReportAPIView(APIView):
    required_module = "reports"
    permission_classes = [
        IsAuthenticated,
        IsSubscriptionActive,
        HasModuleAccess,
    ]

    def get(self, request):
        query = ReportRangeQuerySerializer(
            data=request.query_params
        )

        query.is_valid(
            raise_exception=True
        )

        data = (
            EnhancedReportService
            .analytics(
                request.user,
                **query.validated_data,
            )
        )

        return Response(
            EnhancedReportSerializer(
                data
            ).data
        )


class ReportInvoiceListAPIView(ListAPIView):
    required_module = "reports"
    permission_classes = [
        IsAuthenticated,
        IsSubscriptionActive,
        HasModuleAccess,
    ]
    serializer_class = (
        InvoiceSummarySerializer
    )
    pagination_class = (
        ReportsPagination
    )

    def get_queryset(self):
        query = ReportInvoiceQuerySerializer(
            data=self.request.query_params
        )

        query.is_valid(
            raise_exception=True
        )

        return (
            EnhancedReportService
            .invoices(
                self.request.user,
                **query.validated_data,
            )
        )


def _optional_date_range(request):
    start_date = request.query_params.get(
        "start_date"
    )
    end_date = request.query_params.get(
        "end_date"
    )

    if not start_date and not end_date:
        return None, None

    query = ReportRangeQuerySerializer(
        data={
            "start_date": start_date,
            "end_date": end_date,
        }
    )

    query.is_valid(
        raise_exception=True
    )

    return (
        query.validated_data[
            "start_date"
        ],
        query.validated_data[
            "end_date"
        ],
    )


class RevenueTrendChartAPIView(APIView):
    required_module = "reports"
    permission_classes = [
        IsAuthenticated,
        IsSubscriptionActive,
        HasModuleAccess,
    ]

    def get(self, request):
        days = int(
            request.query_params.get(
                "days",
                30,
            )
        )

        group_by = (
            request.query_params.get(
                "group_by",
                "day",
            )
        )

        (
            start_date,
            end_date,
        ) = _optional_date_range(
            request
        )

        data = (
            ChartDataService
            .revenue_trend(
                request.user,
                days=days,
                group_by=group_by,
                start_date=start_date,
                end_date=end_date,
            )
        )

        return Response(
            RevenueTrendSerializer(
                data
            ).data
        )


class CategorySalesChartAPIView(APIView):
    required_module = "reports"
    permission_classes = [
        IsAuthenticated,
        IsSubscriptionActive,
        HasModuleAccess,
    ]

    def get(self, request):
        days = int(
            request.query_params.get(
                "days",
                30,
            )
        )

        (
            start_date,
            end_date,
        ) = _optional_date_range(
            request
        )

        data = (
            ChartDataService
            .category_sales(
                request.user,
                days=days,
                start_date=start_date,
                end_date=end_date,
            )
        )

        return Response(
            CategorySalesSerializer(
                data,
                many=True,
            ).data
        )


class PaymentMethodChartAPIView(APIView):
    required_module = "reports"
    permission_classes = [
        IsAuthenticated,
        IsSubscriptionActive,
        HasModuleAccess,
    ]

    def get(self, request):
        days = int(
            request.query_params.get(
                "days",
                30,
            )
        )

        (
            start_date,
            end_date,
        ) = _optional_date_range(
            request
        )

        data = (
            ChartDataService
            .payment_method_split(
                request.user,
                days=days,
                start_date=start_date,
                end_date=end_date,
            )
        )

        return Response(
            PaymentMethodSplitSerializer(
                data,
                many=True,
            ).data
        )


class TopProductsChartAPIView(APIView):
    required_module = "reports"
    permission_classes = [
        IsAuthenticated,
        IsSubscriptionActive,
        HasModuleAccess,
    ]

    def get(self, request):
        days = int(
            request.query_params.get(
                "days",
                30,
            )
        )

        limit = int(
            request.query_params.get(
                "limit",
                10,
            )
        )

        limit = max(
            1,
            min(
                limit,
                20,
            ),
        )

        (
            start_date,
            end_date,
        ) = _optional_date_range(
            request
        )

        data = (
            ChartDataService
            .top_products(
                request.user,
                days=days,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
            )
        )

        return Response(
            TopProductSerializer(
                data,
                many=True,
            ).data
        )
