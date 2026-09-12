import uuid
from django.db import models
from tenants.models import Tenant
class Category(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ("tenant", "name")   
    def __str__(self):
        return self.name
class Product(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200, blank=False, null=False)
    barcode = models.CharField(max_length=100, blank=True, null=True) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sku = models.CharField(max_length=50, blank=True, null=True)       

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_tenant_product_name",
            ),
            models.UniqueConstraint(
                fields=["tenant", "barcode"],
                name="unique_tenant_barcode",
                condition=models.Q(barcode__isnull=False) & ~models.Q(barcode=""),
            ),
            models.UniqueConstraint(
                fields=["tenant", "sku"],
                name="unique_tenant_sku",
                condition=models.Q(sku__isnull=False) & ~models.Q(sku=""),
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"SKU-{uuid.uuid4().hex[:6].upper()}"
        if not self.barcode:
            self.barcode = f"896{uuid.uuid4().int % 10000000000000:010d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name