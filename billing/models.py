import uuid
from django.db import models
from users.models import User
from products.models import Product
from .strategies import DiscountFactory
from decimal import Decimal


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    PAYMENT_CHOICES = [
        ("CASH", "Cash"),
        ("CARD", "Card"),
        ("ONLINE", "Online"),
    ]

    DISCOUNT_TYPE_CHOICES = (
        ("FIXED", "Fixed"),
        ("PERCENTAGE", "Percentage"),
    )
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name="invoices")
    invoice_number = models.CharField(max_length=40, unique=True)
    customer_name = models.CharField(max_length=150, blank=True, default="")
    shopkeeper = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invoices")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default="PERCENTAGE")
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not self.invoice_number:
            self.invoice_number = f"TEMP-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)

        if is_new and self.invoice_number.startswith("TEMP-"):
            self.invoice_number = f"INV-{self.pk:06d}"
            super().save(update_fields=["invoice_number"])
    def recalculate_totals(self):
        total = sum((item.total_price for item in self.items.all()), Decimal("0.00"))
        self.total_amount = total

        discount = self.discount or Decimal("0.00")
        if discount < 0:
            discount = Decimal("0.00")

        strategy = DiscountFactory.get(self.discount_type)
        self.final_amount = strategy.apply(total, discount)
        self.discount = discount
        self.save(update_fields=["total_amount", "discount", "final_amount", "updated_at"])
        return self
    def __str__(self):
        return f"{self.invoice_number} ({self.customer_name or 'No Name'})"
    


class InvoiceItem(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ("FIXED", "Fixed"),
        ("PERCENTAGE", "Percentage"),
    )

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default="PERCENTAGE")
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("invoice", "product")

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.product.name}"
    @property
    def profit(self):
        item_cost = self.cost_price * self.quantity
        return self.total_price - item_cost
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.product.name}"

class SaleReturn(models.Model):
    """
    Immutable header for a completed-sale return/refund.

    The original Invoice remains COMPLETED and unchanged. Every return is a
    separate document linked back to that invoice.
    """
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="sale_returns",
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="returns",
    )
    return_number = models.CharField(max_length=40, unique=True, blank=True)
    request_id = models.UUIDField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="sale_returns_created",
    )
    refund_method = models.CharField(
        max_length=20,
        choices=Invoice.PAYMENT_CHOICES,
    )
    reason = models.CharField(max_length=255, blank=True, default="")
    total_refund = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "request_id"],
                name="uniq_return_request_per_tenant",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "-created_at"],
                name="ret_tenant_created_idx",
            ),
            models.Index(
                fields=["invoice", "-created_at"],
                name="ret_invoice_created_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not self.return_number:
            self.return_number = f"TEMP-{uuid.uuid4().hex[:12]}"

        super().save(*args, **kwargs)

        if is_new and self.return_number.startswith("TEMP-"):
            self.return_number = f"RET-{self.pk:06d}"
            super().save(update_fields=["return_number"])

    def __str__(self):
        return f"{self.return_number} - {self.invoice.invoice_number}"


class SaleReturnItem(models.Model):
    sale_return = models.ForeignKey(
        SaleReturn,
        on_delete=models.CASCADE,
        related_name="items",
    )
    invoice_item = models.ForeignKey(
        InvoiceItem,
        on_delete=models.PROTECT,
        related_name="return_items",
    )
    quantity = models.PositiveIntegerField()
    # Effective net sold price after item-level AND invoice-level discounts.
    # Four decimals preserve fair proportional pricing; refund_amount is money.
    refund_unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
    )
    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sale_return", "invoice_item"],
                name="uniq_item_once_per_return",
            ),
        ]
        indexes = [
            models.Index(
                fields=["invoice_item"],
                name="ret_item_invoice_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.sale_return.return_number} - "
            f"{self.invoice_item.product.name} x {self.quantity}"
        )

