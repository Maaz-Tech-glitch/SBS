from django.utils import timezone
from django.db.models import Sum
from calendar import monthrange
from billing.repositories import InvoiceRepository


class SalesReportService:
    @staticmethod
    def _summarize(invoices):
        total_sales = invoices.count()
        total_revenue = invoices.aggregate(total=Sum("final_amount"))["total"] or 0
        return total_sales, total_revenue, invoices

    @staticmethod
    def daily(user):
        today = timezone.now().date()
        invoices = InvoiceRepository.get_completed_in_range(user, today, today)
        total_sales, total_revenue, invoices = SalesReportService._summarize(invoices)
        return {"date": today, "total_sales": total_sales, "total_revenue": total_revenue, "invoices": invoices}

    @staticmethod
    def monthly(user):
        now = timezone.now()
        start = now.replace(day=1).date()
        end = now.replace(day=monthrange(now.year, now.month)[1]).date()
        invoices = InvoiceRepository.get_completed_in_range(user, start, end)
        total_sales, total_revenue, invoices = SalesReportService._summarize(invoices)
        return {"month": now.strftime("%B"), "year": now.year, "total_sales": total_sales,
                "total_revenue": total_revenue, "invoices": invoices}

    @staticmethod
    def yearly(user):
        now = timezone.now()
        start = now.replace(month=1, day=1).date()
        end = now.replace(month=12, day=31).date()
        invoices = InvoiceRepository.get_completed_in_range(user, start, end)
        total_sales, total_revenue, invoices = SalesReportService._summarize(invoices)
        return {"year": now.year, "total_sales": total_sales, "total_revenue": total_revenue, "invoices": invoices}