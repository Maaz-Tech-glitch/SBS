from django.utils import timezone
from django.db.models import Sum
from billing.models import Invoice

def daily_sales_report(user):
    today = timezone.now().date()
    invoices = Invoice.objects.filter(shopkeeper=user,status="COMPLETED",created_at__date=today)
    total_sales = invoices.count()
    total_revenue = invoices.aggregate(
        total=Sum("final_amount")
    )["total"] or 0
    
    return {
        "date": today,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "invoices": invoices
    }
    
def monthly_sales_report(user):
    now = timezone.now()
    invoices = Invoice.objects.filter(
        shopkeeper=user,
        status="COMPLETED",
        created_at__month=now.month,
        created_at__year=now.year
)
    total_sales = invoices.count()
    total_revenue = invoices.aggregate(
        total=Sum("final_amount")
    )["total"] or 0
    return {
        "month": now.strftime("%B"),
        "year": now.year,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "invoices": invoices
    }
    
def yearly_sales_report(user):
    now = timezone.now()
    invoices = Invoice.objects.filter(
        shopkeeper=user,
        status="COMPLETED",
        created_at__year=now.year
    )
    total_sales = invoices.count()
    total_revenue = invoices.aggregate(
        total=Sum("final_amount")
    )["total"] or 0
    return {
        "year": now.year,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "invoices": invoices
    }
    