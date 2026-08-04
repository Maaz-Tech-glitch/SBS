import uuid
from django.db import models
from users.models import User

# category model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    
# product model
class Product(models.Model):
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="products")
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"SKU-{uuid.uuid4().hex[:6].upper()}"
        if not self.barcode:
            self.barcode = f"896{uuid.uuid4().int % 10000000000000:010d}"
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name
    
