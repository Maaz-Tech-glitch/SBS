# from django.db.models import Sum, Count, F
# from django.db.models.functions import TruncDate, TruncMonth
# from billing.models import Invoice, InvoiceItem

# class ChartsRepository:

#     @staticmethod
#     def revenue_by_day(tenant, start_date, end_date):
#         return (
#             Invoice.objects.filter(
#                 tenant=tenant, status="COMPLETED",
#                 created_at__date__gte=start_date, created_at__date__lte=end_date,
#             )
#             .annotate(period=TruncDate("created_at"))
#             .values("period")
#             .annotate(revenue=Sum("final_amount"), sales_count=Count("id"))
#             .order_by("period")
#         )

#     @staticmethod
#     def revenue_by_month(tenant, start_date, end_date):
#         return (
#             Invoice.objects.filter(
#                 tenant=tenant, status="COMPLETED",
#                 created_at__date__gte=start_date, created_at__date__lte=end_date,
#             )
#             .annotate(period=TruncMonth("created_at"))
#             .values("period")
#             .annotate(revenue=Sum("final_amount"), sales_count=Count("id"))
#             .order_by("period")
#         )

#     @staticmethod
#     def category_wise_sales(tenant, start_date, end_date):
#         return (
#             InvoiceItem.objects.filter(
#                 invoice__tenant=tenant, invoice__status="COMPLETED",
#                 invoice__created_at__date__gte=start_date,
#                 invoice__created_at__date__lte=end_date,
#             )
#             .values(category_name=F("product__category__name"))
#             .annotate(revenue=Sum("total_price"), quantity=Sum("quantity"))
#             .order_by("-revenue")
#         )

#     @staticmethod
#     def payment_method_split(tenant, start_date, end_date):
#         return (
#             Invoice.objects.filter(
#                 tenant=tenant, status="COMPLETED",
#                 created_at__date__gte=start_date, created_at__date__lte=end_date,
#             )
#             .values("payment_method")
#             .annotate(revenue=Sum("final_amount"), count=Count("id"))
#             .order_by("-revenue")
#         )

#     @staticmethod
#     def top_products(tenant, start_date, end_date, limit=10):
#         return (
#             InvoiceItem.objects.filter(
#                 invoice__tenant=tenant, invoice__status="COMPLETED",
#                 invoice__created_at__date__gte=start_date,
#                 invoice__created_at__date__lte=end_date,
#             )
#             .values(product_name=F("product__name"))
#             .annotate(quantity_sold=Sum("quantity"), revenue=Sum("total_price"))
#             .order_by("-revenue")[:limit]
#         )

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth

from billing.models import Invoice, InvoiceItem


class SalesReportRepository:
    @staticmethod
    def completed_invoices(tenant, start_date, end_date):
        return (
            Invoice.objects
            .filter(
                tenant=tenant,
                status="COMPLETED",
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .order_by("-created_at")
        )

    @staticmethod
    def invoice_items(tenant, start_date, end_date):
        return InvoiceItem.objects.filter(
            invoice__tenant=tenant,
            invoice__status="COMPLETED",
            invoice__created_at__date__gte=start_date,
            invoice__created_at__date__lte=end_date,
        )

    @staticmethod
    def summary(tenant, start_date, end_date):
        invoices = SalesReportRepository.completed_invoices(
            tenant,
            start_date,
            end_date,
        )

        totals = invoices.aggregate(
            total_sales=Count("id"),
            total_revenue=Sum("final_amount"),
        )

        items_sold = (
            SalesReportRepository
            .invoice_items(
                tenant,
                start_date,
                end_date,
            )
            .aggregate(total=Sum("quantity"))
            .get("total")
            or 0
        )

        return {
            "total_sales": totals.get("total_sales") or 0,
            "total_revenue": totals.get("total_revenue") or 0,
            "items_sold": items_sold,
        }

    @staticmethod
    def filtered_invoices(
        tenant,
        start_date,
        end_date,
        *,
        search="",
        payment_method="",
    ):
        queryset = (
            SalesReportRepository
            .completed_invoices(
                tenant,
                start_date,
                end_date,
            )
        )

        search = (search or "").strip()
        payment_method = (payment_method or "").strip().upper()

        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search)
                | Q(customer_name__icontains=search)
            )

        if payment_method:
            queryset = queryset.filter(
                payment_method=payment_method
            )

        return queryset


class ChartsRepository:
    @staticmethod
    def revenue_by_day(tenant, start_date, end_date):
        return (
            Invoice.objects
            .filter(
                tenant=tenant,
                status="COMPLETED",
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .annotate(period=TruncDate("created_at"))
            .values("period")
            .annotate(
                revenue=Sum("final_amount"),
                sales_count=Count("id"),
            )
            .order_by("period")
        )

    @staticmethod
    def revenue_by_month(tenant, start_date, end_date):
        return (
            Invoice.objects
            .filter(
                tenant=tenant,
                status="COMPLETED",
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .annotate(period=TruncMonth("created_at"))
            .values("period")
            .annotate(
                revenue=Sum("final_amount"),
                sales_count=Count("id"),
            )
            .order_by("period")
        )

    @staticmethod
    def category_wise_sales(tenant, start_date, end_date):
        return (
            InvoiceItem.objects
            .filter(
                invoice__tenant=tenant,
                invoice__status="COMPLETED",
                invoice__created_at__date__gte=start_date,
                invoice__created_at__date__lte=end_date,
            )
            .values(
                category_name=F("product__category__name")
            )
            .annotate(
                revenue=Sum("total_price"),
                quantity=Sum("quantity"),
            )
            .order_by("-revenue")
        )

    @staticmethod
    def payment_method_split(tenant, start_date, end_date):
        return (
            Invoice.objects
            .filter(
                tenant=tenant,
                status="COMPLETED",
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .values("payment_method")
            .annotate(
                revenue=Sum("final_amount"),
                count=Count("id"),
            )
            .order_by("-revenue")
        )

    @staticmethod
    def top_products(
        tenant,
        start_date,
        end_date,
        limit=10,
    ):
        return (
            InvoiceItem.objects
            .filter(
                invoice__tenant=tenant,
                invoice__status="COMPLETED",
                invoice__created_at__date__gte=start_date,
                invoice__created_at__date__lte=end_date,
            )
            .values(
                product_name=F("product__name")
            )
            .annotate(
                quantity_sold=Sum("quantity"),
                revenue=Sum("total_price"),
            )
            .order_by("-revenue")[:limit]
        )
