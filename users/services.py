from django.conf import settings
from django.core.mail import send_mail
import random

# Generate OTP
def generate_otp():
    """
    Generate a random 6-digit OTP
    """
    return str(random.randint(100000, 999999))

# 
def send_otp_email(user, otp):
    subject = "SBS POS - Password Reset OTP"
    message = f"""
Hello {user.username},
Your OTP for password reset is:
{otp}
This OTP will expire in 5 minutes.
If you didn't request this, please ignore this email.
Thank you,
SBS POS Team
"""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )