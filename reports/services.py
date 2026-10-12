# from django.utils import timezone
# from django.db.models import Sum
# from calendar import monthrange
# from billing.repositories import InvoiceRepository
# from datetime import timedelta
# from .repositories import ChartsRepository


# class SalesReportService:
#     @staticmethod
#     def _summarize(invoices):
#         total_sales = invoices.count()
#         total_revenue = invoices.aggregate(total=Sum("final_amount"))["total"] or 0
#         return total_sales, total_revenue, invoices

#     @staticmethod
#     def daily(user):
#         today = timezone.now().date()
#         invoices = InvoiceRepository.get_completed_in_range(user.tenant, today, today)
#         total_sales, total_revenue, invoices = SalesReportService._summarize(invoices)
#         return {"date": today, "total_sales": total_sales, "total_revenue": total_revenue, "invoices": invoices}

#     @staticmethod
#     def monthly(user):
#         now = timezone.now()
#         start = now.replace(day=1).date()
#         end = now.replace(day=monthrange(now.year, now.month)[1]).date()
#         invoices = InvoiceRepository.get_completed_in_range(user.tenant, start, end)
#         total_sales, total_revenue, invoices = SalesReportService._summarize(invoices)
#         return {"month": now.strftime("%B"), "year": now.year, "total_sales": total_sales,
#                 "total_revenue": total_revenue, "invoices": invoices}

#     @staticmethod
#     def yearly(user):
#         now = timezone.now()
#         start = now.replace(month=1, day=1).date()
#         end = now.replace(month=12, day=31).date()
#         invoices = InvoiceRepository.get_completed_in_range(user.tenant, start, end)
#         total_sales, total_revenue, invoices = SalesReportService._summarize(invoices)
#         return {"year": now.year, "total_sales": total_sales, "total_revenue": total_revenue, "invoices": invoices}
    
    


# class ChartDataService:
#     @staticmethod
#     def _default_range(days):
#         end_date = timezone.now().date()
#         start_date = end_date - timedelta(days=days - 1)
#         return start_date, end_date

#     @staticmethod
#     def revenue_trend(user, days=30, group_by="day"):
#         start_date, end_date = ChartDataService._default_range(days)
#         if group_by == "month":
#             rows = ChartsRepository.revenue_by_month(user.tenant, start_date, end_date)
#             label_format = "%b %Y"
#         else:
#             rows = ChartsRepository.revenue_by_day(user.tenant, start_date, end_date)
#             label_format = "%d %b"

#         labels, revenue, sales_count = [], [], []
#         for row in rows:
#             labels.append(row["period"].strftime(label_format))
#             revenue.append(row["revenue"] or 0)
#             sales_count.append(row["sales_count"])
#         return {"labels": labels, "revenue": revenue, "sales_count": sales_count}

#     @staticmethod
#     def category_sales(user, days=30):
#         start_date, end_date = ChartDataService._default_range(days)
#         rows = ChartsRepository.category_wise_sales(user.tenant, start_date, end_date)
#         return [
#             {"category": row["category_name"] or "Uncategorized",
#             "revenue": row["revenue"] or 0, "quantity": row["quantity"] or 0}
#             for row in rows
#         ]

#     @staticmethod
#     def payment_method_split(user, days=30):
#         start_date, end_date = ChartDataService._default_range(days)
#         rows = ChartsRepository.payment_method_split(user.tenant, start_date, end_date)
#         return [
#             {"payment_method": row["payment_method"] or "N/A",
#             "revenue": row["revenue"] or 0, "count": row["count"]}
#             for row in rows
#         ]

#     @staticmethod
#     def top_products(user, days=30, limit=10):
#         start_date, end_date = ChartDataService._default_range(days)
#         rows = ChartsRepository.top_products(user.tenant, start_date, end_date, limit)
#         return [
#             {"product": row["product_name"], "quantity_sold": row["quantity_sold"] or 0,
#             "revenue": row["revenue"] or 0}
#             for row in rows
#         ]


from calendar import monthrange
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from billing.repositories import InvoiceRepository

from .repositories import (
    ChartsRepository,
    SalesReportRepository,
)


class SalesReportService:
    @staticmethod
    def _summarize(invoices):
        total_sales = invoices.count()
        total_revenue = (
            invoices.aggregate(
                total=Sum("final_amount")
            )["total"]
            or 0
        )
        return (
            total_sales,
            total_revenue,
            invoices,
        )

    @staticmethod
    def daily(user):
        today = timezone.now().date()

        invoices = (
            InvoiceRepository
            .get_completed_in_range(
                user.tenant,
                today,
                today,
            )
        )

        (
            total_sales,
            total_revenue,
            invoices,
        ) = SalesReportService._summarize(
            invoices
        )

        return {
            "date": today,
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "invoices": invoices,
        }

    @staticmethod
    def monthly(user):
        now = timezone.now()

        start = now.replace(
            day=1
        ).date()

        end = now.replace(
            day=monthrange(
                now.year,
                now.month,
            )[1]
        ).date()

        invoices = (
            InvoiceRepository
            .get_completed_in_range(
                user.tenant,
                start,
                end,
            )
        )

        (
            total_sales,
            total_revenue,
            invoices,
        ) = SalesReportService._summarize(
            invoices
        )

        return {
            "month": now.strftime("%B"),
            "year": now.year,
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "invoices": invoices,
        }

    @staticmethod
    def yearly(user):
        now = timezone.now()

        start = now.replace(
            month=1,
            day=1,
        ).date()

        end = now.replace(
            month=12,
            day=31,
        ).date()

        invoices = (
            InvoiceRepository
            .get_completed_in_range(
                user.tenant,
                start,
                end,
            )
        )

        (
            total_sales,
            total_revenue,
            invoices,
        ) = SalesReportService._summarize(
            invoices
        )

        return {
            "year": now.year,
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "invoices": invoices,
        }


class ChartDataService:
    @staticmethod
    def _default_range(days):
        end_date = timezone.now().date()

        start_date = (
            end_date
            - timedelta(
                days=days - 1
            )
        )

        return start_date, end_date

    @staticmethod
    def _resolve_range(
        *,
        days=30,
        start_date=None,
        end_date=None,
    ):
        if (
            start_date is not None
            and end_date is not None
        ):
            return start_date, end_date

        return (
            ChartDataService
            ._default_range(days)
        )

    @staticmethod
    def revenue_trend(
        user,
        days=30,
        group_by="day",
        start_date=None,
        end_date=None,
    ):
        (
            start_date,
            end_date,
        ) = ChartDataService._resolve_range(
            days=days,
            start_date=start_date,
            end_date=end_date,
        )

        if group_by == "month":
            rows = (
                ChartsRepository
                .revenue_by_month(
                    user.tenant,
                    start_date,
                    end_date,
                )
            )
            label_format = "%b %Y"
        else:
            rows = (
                ChartsRepository
                .revenue_by_day(
                    user.tenant,
                    start_date,
                    end_date,
                )
            )
            label_format = "%d %b"

        labels = []
        revenue = []
        sales_count = []

        for row in rows:
            labels.append(
                row["period"].strftime(
                    label_format
                )
            )
            revenue.append(
                row["revenue"] or 0
            )
            sales_count.append(
                row["sales_count"]
            )

        return {
            "labels": labels,
            "revenue": revenue,
            "sales_count": sales_count,
        }

    @staticmethod
    def category_sales(
        user,
        days=30,
        start_date=None,
        end_date=None,
    ):
        (
            start_date,
            end_date,
        ) = ChartDataService._resolve_range(
            days=days,
            start_date=start_date,
            end_date=end_date,
        )

        rows = (
            ChartsRepository
            .category_wise_sales(
                user.tenant,
                start_date,
                end_date,
            )
        )

        return [
            {
                "category":
                    row["category_name"]
                    or "Uncategorized",

                "revenue":
                    row["revenue"]
                    or 0,

                "quantity":
                    row["quantity"]
                    or 0,
            }
            for row in rows
        ]

    @staticmethod
    def payment_method_split(
        user,
        days=30,
        start_date=None,
        end_date=None,
    ):
        (
            start_date,
            end_date,
        ) = ChartDataService._resolve_range(
            days=days,
            start_date=start_date,
            end_date=end_date,
        )

        rows = (
            ChartsRepository
            .payment_method_split(
                user.tenant,
                start_date,
                end_date,
            )
        )

        return [
            {
                "payment_method":
                    row["payment_method"]
                    or "N/A",

                "revenue":
                    row["revenue"]
                    or 0,

                "count":
                    row["count"],
            }
            for row in rows
        ]

    @staticmethod
    def top_products(
        user,
        days=30,
        limit=10,
        start_date=None,
        end_date=None,
    ):
        (
            start_date,
            end_date,
        ) = ChartDataService._resolve_range(
            days=days,
            start_date=start_date,
            end_date=end_date,
        )

        rows = (
            ChartsRepository
            .top_products(
                user.tenant,
                start_date,
                end_date,
                limit,
            )
        )

        return [
            {
                "product":
                    row["product_name"],

                "quantity_sold":
                    row["quantity_sold"]
                    or 0,

                "revenue":
                    row["revenue"]
                    or 0,
            }
            for row in rows
        ]


class EnhancedReportService:
    @staticmethod
    def _average_sale(
        total_revenue,
        total_sales,
    ):
        if not total_sales:
            return Decimal("0.00")

        return (
            Decimal(total_revenue)
            / Decimal(total_sales)
        ).quantize(
            Decimal("0.01")
        )

    @staticmethod
    def _change_percent(
        current,
        previous,
    ):
        current = Decimal(current or 0)
        previous = Decimal(previous or 0)

        if previous == 0:
            return (
                0.0
                if current == 0
                else None
            )

        return round(
            float(
                (
                    (current - previous)
                    / previous
                )
                * Decimal("100")
            ),
            2,
        )

    @staticmethod
    def _previous_period(
        start_date,
        end_date,
    ):
        days = (
            end_date - start_date
        ).days + 1

        previous_end = (
            start_date
            - timedelta(days=1)
        )

        previous_start = (
            previous_end
            - timedelta(
                days=days - 1
            )
        )

        return (
            previous_start,
            previous_end,
        )

    @staticmethod
    def _daily_breakdown(
        tenant,
        start_date,
        end_date,
    ):
        rows = list(
            ChartsRepository
            .revenue_by_day(
                tenant,
                start_date,
                end_date,
            )
        )

        by_date = {
            row["period"]: row
            for row in rows
        }

        result = []
        current_date = start_date

        while current_date <= end_date:
            row = by_date.get(
                current_date
            )

            total_sales = (
                row["sales_count"]
                if row
                else 0
            )

            total_revenue = (
                row["revenue"]
                if row
                and row["revenue"]
                is not None
                else Decimal("0.00")
            )

            result.append(
                {
                    "date":
                        current_date,

                    "total_sales":
                        total_sales,

                    "total_revenue":
                        total_revenue,

                    "average_sale":
                        EnhancedReportService
                        ._average_sale(
                            total_revenue,
                            total_sales,
                        ),
                }
            )

            current_date += timedelta(
                days=1
            )

        return result

    @staticmethod
    def analytics(
        user,
        *,
        start_date,
        end_date,
        top_limit=5,
    ):
        tenant = user.tenant

        summary = (
            SalesReportRepository
            .summary(
                tenant,
                start_date,
                end_date,
            )
        )

        summary["average_sale"] = (
            EnhancedReportService
            ._average_sale(
                summary["total_revenue"],
                summary["total_sales"],
            )
        )

        (
            previous_start,
            previous_end,
        ) = (
            EnhancedReportService
            ._previous_period(
                start_date,
                end_date,
            )
        )

        previous = (
            SalesReportRepository
            .summary(
                tenant,
                previous_start,
                previous_end,
            )
        )

        comparison = {
            "previous_start_date":
                previous_start,

            "previous_end_date":
                previous_end,

            "total_sales":
                previous["total_sales"],

            "total_revenue":
                previous["total_revenue"],

            "sales_change_percent":
                EnhancedReportService
                ._change_percent(
                    summary["total_sales"],
                    previous["total_sales"],
                ),

            "revenue_change_percent":
                EnhancedReportService
                ._change_percent(
                    summary["total_revenue"],
                    previous["total_revenue"],
                ),
        }

        return {
            "start_date":
                start_date,

            "end_date":
                end_date,

            "days":
                (
                    end_date - start_date
                ).days + 1,

            "summary":
                summary,

            "comparison":
                comparison,

            "daily_breakdown":
                EnhancedReportService
                ._daily_breakdown(
                    tenant,
                    start_date,
                    end_date,
                ),

            "category_sales":
                ChartDataService
                .category_sales(
                    user,
                    start_date=start_date,
                    end_date=end_date,
                ),

            "payment_methods":
                ChartDataService
                .payment_method_split(
                    user,
                    start_date=start_date,
                    end_date=end_date,
                ),

            "top_products":
                ChartDataService
                .top_products(
                    user,
                    limit=top_limit,
                    start_date=start_date,
                    end_date=end_date,
                ),
        }

    @staticmethod
    def invoices(
        user,
        *,
        start_date,
        end_date,
        search="",
        payment_method="",
    ):
        return (
            SalesReportRepository
            .filtered_invoices(
                user.tenant,
                start_date,
                end_date,
                search=search,
                payment_method=payment_method,
            )
        )
