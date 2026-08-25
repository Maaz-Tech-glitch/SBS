from products.models import Product
from billing.models import Invoice
from django.db.models import Sum
from django.utils import timezone

def get_dashboard_summary(user):
    tenant = user.tenant
    today = timezone.now().date()
    total_products = Product.objects.filter(tenant=tenant).count()
    low_stock_products = Product.objects.filter(tenant=tenant, stock__lte=5).count()
    out_of_stock_products = Product.objects.filter(tenant=tenant, stock=0).count()
    total_sales_today = Invoice.objects.filter(
        tenant=tenant,
        status="COMPLETED",
        created_at__date=today
    ).count()
    total_revenue_today = (
        Invoice.objects.filter(
            tenant=tenant,
            status="COMPLETED",
            created_at__date=today
        ).aggregate(total=Sum("final_amount"))["total"] or 0)
    pending_invoices = Invoice.objects.filter(
        tenant=tenant,
        status="PENDING"
    ).count()
    return {
        "total_products": total_products,
        "low_stock_products": low_stock_products,
        "out_of_stock_products": out_of_stock_products,
        "total_sales_today": total_sales_today,
        "total_revenue_today": total_revenue_today,
        "pending_invoices": pending_invoices,
    }