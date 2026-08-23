from django.conf import settings
from django.db import models

from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True, default="")
    business_type = models.CharField(max_length=100, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


