import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models 
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import UserManager as DjangoUserManager

class UserManager(DjangoUserManager):
    def get_by_email(self, email):
        return self.get(email=email)
    def get_by_username(self, username):
        return self.get(username=username)
    def get_admins(self):
        return self.filter(role='admin')
    def get_shopkeepers(self):
        return self.filter(role='shopkeeper')
    def get_active(self):
        return self.filter(is_active=True)
class OTPManager(models.Manager):
    
    def get_valid(self, user, otp):
        return self.get(user=user, otp=otp, is_used=False)
    
    def get_recent(self, user, minutes=1):
        time_limit = timezone.now() - timedelta(minutes=minutes)
        return self.filter(user=user, created_at__gte=time_limit)


class User(AbstractUser):    
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('shopkeeper', 'Shopkeeper'),
    )
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='users',null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='shopkeeper')
    phone = models.CharField(max_length=15, blank=True, null=True )
    email = models.EmailField(unique=True)
    objects = UserManager()
    def is_admin(self):
        return self.role == 'admin'    
    def is_shopkeeper(self):
        return self.role == 'shopkeeper'
    
    def change_password(self, new_password):
        self.set_password(new_password)
        self.save(update_fields=['password'])
    
    def update_profile(self, **kwargs):
        allowed_fields = ['email', 'phone', 'first_name', 'last_name']
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(self, key, value)
        self.save()
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    class Meta:
        ordering = ['-date_joined']

class PasswordResetOTP(models.Model):
    
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="password_otps")
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    objects = OTPManager()  
        
    def is_expired(self):
        return timezone.now() > self.expires_at
    def is_valid(self):
        return not self.is_used and not self.is_expired()
    def mark_as_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=1)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - OTP"    
    class Meta:
        ordering = ['-created_at']
        
class EmailVerificationOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="verification_otps")
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    objects = OTPManager()   # same generic manager reuse ho raha hai
    def is_expired(self):
        return timezone.now() > self.expires_at
    def mark_as_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.user.username} - Verification OTP"
    class Meta:
        ordering = ['-created_at']