from django.utils import timezone
from django.db.models import Sum
from calendar import monthrange
from billing.repositories import InvoiceRepository
from datetime import timedelta
from .repositories import ChartsRepository


class SalesReportService:
    @staticmethod
    def _summarize(invoices):
        total_sales = invoices.count()
        total_revenue = invoices.aggregate(total=Sum("final_amount"))["total"] or 0
        return total_sales, total_revenue, invoices

    @staticmethod
    def daily(user):
        today = timezone.now().date()
        invoices = InvoiceRepository.get_completed_in_range(user.tenant, today, today)
        total_sales, total_revenue, invoices = SalesReportService._summarize(invoices)
        return {"date": today, "total_sales": total_sales, "total_revenue": total_revenue, "invoices": invoices}

    @staticmethod
    def monthly(user):
        now = timezone.now()
        start = now.replace(day=1).date()
        end = now.replace(day=monthrange(now.year, now.month)[1]).date()
        invoices = InvoiceRepository.get_completed_in_range(user.tenant, start, end)
        total_sales, total_revenue, invoices = SalesReportService._summarize(invoices)
        return {"month": now.strftime("%B"), "year": now.year, "total_sales": total_sales,
                "total_revenue": total_revenue, "invoices": invoices}

    @staticmethod
    def yearly(user):
        now = timezone.now()
        start = now.replace(month=1, day=1).date()
        end = now.replace(month=12, day=31).date()
        invoices = InvoiceRepository.get_completed_in_range(user.tenant, start, end)
        total_sales, total_revenue, invoices = SalesReportService._summarize(invoices)
        return {"year": now.year, "total_sales": total_sales, "total_revenue": total_revenue, "invoices": invoices}
    
    


class ChartDataService:
    @staticmethod
    def _default_range(days):
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)
        return start_date, end_date

    @staticmethod
    def revenue_trend(user, days=30, group_by="day"):
        start_date, end_date = ChartDataService._default_range(days)
        if group_by == "month":
            rows = ChartsRepository.revenue_by_month(user.tenant, start_date, end_date)
            label_format = "%b %Y"
        else:
            rows = ChartsRepository.revenue_by_day(user.tenant, start_date, end_date)
            label_format = "%d %b"

        labels, revenue, sales_count = [], [], []
        for row in rows:
            labels.append(row["period"].strftime(label_format))
            revenue.append(row["revenue"] or 0)
            sales_count.append(row["sales_count"])
        return {"labels": labels, "revenue": revenue, "sales_count": sales_count}

    @staticmethod
    def category_sales(user, days=30):
        start_date, end_date = ChartDataService._default_range(days)
        rows = ChartsRepository.category_wise_sales(user.tenant, start_date, end_date)
        return [
            {"category": row["category_name"] or "Uncategorized",
            "revenue": row["revenue"] or 0, "quantity": row["quantity"] or 0}
            for row in rows
        ]

    @staticmethod
    def payment_method_split(user, days=30):
        start_date, end_date = ChartDataService._default_range(days)
        rows = ChartsRepository.payment_method_split(user.tenant, start_date, end_date)
        return [
            {"payment_method": row["payment_method"] or "N/A",
            "revenue": row["revenue"] or 0, "count": row["count"]}
            for row in rows
        ]

    @staticmethod
    def top_products(user, days=30, limit=10):
        start_date, end_date = ChartDataService._default_range(days)
        rows = ChartsRepository.top_products(user.tenant, start_date, end_date, limit)
        return [
            {"product": row["product_name"], "quantity_sold": row["quantity_sold"] or 0,
            "revenue": row["revenue"] or 0}
            for row in rows
        ]