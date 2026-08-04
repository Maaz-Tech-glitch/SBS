from django.contrib.auth.models import AbstractUser
from django.db import models 
from django.db import models
from django.utils import timezone
from datetime import timedelta
# User model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('shopkeeper', 'Shopkeeper'),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='shopkeeper'
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )
    def __str__(self):
        return self.username

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_otps"
    )
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.user.username} - {self.otp}"
