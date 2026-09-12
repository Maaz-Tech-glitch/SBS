from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate, TruncMonth
from billing.models import Invoice, InvoiceItem

class ChartsRepository:

    @staticmethod
    def revenue_by_day(tenant, start_date, end_date):
        return (
            Invoice.objects.filter(
                tenant=tenant, status="COMPLETED",
                created_at__date__gte=start_date, created_at__date__lte=end_date,
            )
            .annotate(period=TruncDate("created_at"))
            .values("period")
            .annotate(revenue=Sum("final_amount"), sales_count=Count("id"))
            .order_by("period")
        )

    @staticmethod
    def revenue_by_month(tenant, start_date, end_date):
        return (
            Invoice.objects.filter(
                tenant=tenant, status="COMPLETED",
                created_at__date__gte=start_date, created_at__date__lte=end_date,
            )
            .annotate(period=TruncMonth("created_at"))
            .values("period")
            .annotate(revenue=Sum("final_amount"), sales_count=Count("id"))
            .order_by("period")
        )

    @staticmethod
    def category_wise_sales(tenant, start_date, end_date):
        return (
            InvoiceItem.objects.filter(
                invoice__tenant=tenant, invoice__status="COMPLETED",
                invoice__created_at__date__gte=start_date,
                invoice__created_at__date__lte=end_date,
            )
            .values(category_name=F("product__category__name"))
            .annotate(revenue=Sum("total_price"), quantity=Sum("quantity"))
            .order_by("-revenue")
        )

    @staticmethod
    def payment_method_split(tenant, start_date, end_date):
        return (
            Invoice.objects.filter(
                tenant=tenant, status="COMPLETED",
                created_at__date__gte=start_date, created_at__date__lte=end_date,
            )
            .values("payment_method")
            .annotate(revenue=Sum("final_amount"), count=Count("id"))
            .order_by("-revenue")
        )

    @staticmethod
    def top_products(tenant, start_date, end_date, limit=10):
        return (
            InvoiceItem.objects.filter(
                invoice__tenant=tenant, invoice__status="COMPLETED",
                invoice__created_at__date__gte=start_date,
                invoice__created_at__date__lte=end_date,
            )
            .values(product_name=F("product__name"))
            .annotate(quantity_sold=Sum("quantity"), revenue=Sum("total_price"))
            .order_by("-revenue")[:limit]
        )