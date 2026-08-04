from django.contrib import admin
from .models import Invoice, InvoiceItem


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "customer_name",
        "shopkeeper",
        "status",
        "total_amount",
        "discount",
        "final_amount",
        "created_at",
    )
    list_filter = ("status", "payment_method")
    search_fields = ("invoice_number", "customer_name")


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "product",
        "quantity",
        "unit_price",
        "discount",
        "total_price",
    )
    search_fields = ("invoice__invoice_number", "product__name")