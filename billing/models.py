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
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default="PERCENTAGE")
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("invoice", "product")

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.product.name}"