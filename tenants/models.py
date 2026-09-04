from django.conf import settings
from django.db import models

from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=200 , unique=True  )
    address = models.CharField(max_length=255,)
    business_type = models.CharField(max_length=100, )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, default="")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


