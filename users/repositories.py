# DIP: Dependency Inversion Principle
# Database logic abstracted - services don't know about models directly

from django.utils import timezone
from datetime import timedelta
from .models import User, PasswordResetOTP , EmailVerificationOTP
from .exceptions import (
    UserNotFoundException,
    InvalidOTPException,
    OTPExpiredException,
    RateLimitException, 
)

class UserRepository:    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise UserNotFoundException(f"User with email not found")
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise UserNotFoundException(f"User with username not found")
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by id"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise UserNotFoundException(f"User not found")


class OTPRepository:
    """OTP database operations - DIP abstraction"""
    
    @staticmethod
    def create(user, otp):
        """Create new OTP"""
        return PasswordResetOTP.objects.create(user=user, otp=otp)
    
    @staticmethod
    def get_valid(user, otp):
        """Get valid OTP"""
        try:
            otp_obj = PasswordResetOTP.objects.get(
                user=user,
                otp=otp,
                is_used=False
            )
            if otp_obj.is_expired():
                raise OTPExpiredException()
            return otp_obj
        except PasswordResetOTP.DoesNotExist:
            raise InvalidOTPException()
    
    @staticmethod
    def check_rate_limit(user):
        """Check if user can request new OTP"""
        recent_otp = PasswordResetOTP.objects.get_recent(user, minutes=1).exists()
        if recent_otp:
            raise RateLimitException()
    
    @staticmethod
    def delete_old(user):
        """Delete old unused OTPs"""
        PasswordResetOTP.objects.filter(user=user, is_used=False).delete()
        
        


class EmailOTPRepository:
    @staticmethod
    def create(user, otp):
        return EmailVerificationOTP.objects.create(user=user, otp=otp)

    @staticmethod
    def get_valid(user, otp):
        try:
            otp_obj = EmailVerificationOTP.objects.get(user=user, otp=otp, is_used=False)
            if otp_obj.is_expired():
                raise OTPExpiredException()
            return otp_obj
        except EmailVerificationOTP.DoesNotExist:
            raise InvalidOTPException()

    @staticmethod
    def check_rate_limit(user):
        recent = EmailVerificationOTP.objects.get_recent(user, minutes=1).exists()
        if recent:
            raise RateLimitException()

    @staticmethod
    def delete_old(user):
        EmailVerificationOTP.objects.filter(user=user, is_used=False).delete()