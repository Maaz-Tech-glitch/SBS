import random
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .repositories import UserRepository, OTPRepository
from .strategies import AuthenticationFactory
from .exceptions import InvalidTokenException

def generate_otp():
    """Generate random 6-digit OTP"""
    return str(random.randint(100000, 999999))

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

class BaseService:
    
    @staticmethod
    def validate_not_none(value, message):
        """Validate value is not None"""
        if not value:
            raise ValueError(message)



class AuthenticationService(BaseService):    
    @staticmethod
    def authenticate_user(username, password, strategy_type="username"):
        strategy = AuthenticationFactory.get_strategy(strategy_type)
        return strategy.authenticate(username=username, password=password)

class TokenService(BaseService):    
    @staticmethod
    def generate_tokens(user):
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }    
    @staticmethod
    def validate_refresh_token(refresh_token):
        if not refresh_token:
            raise InvalidTokenException("Refresh token required") 
        try:
            token = RefreshToken(refresh_token)
            return token
        except Exception:
            raise InvalidTokenException()

class LogoutService(BaseService):
    @staticmethod
    def logout_user(refresh_token):
        token = TokenService.validate_refresh_token(refresh_token)
        token.blacklist()
        return True

class ResponseFormatterService(BaseService):
    @staticmethod
    def format_user_data(user):
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
        }    
    @staticmethod
    def format_login_response(user, tokens):
        """Format login response"""
        return {
            "message": "Login Successful",
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "user": ResponseFormatterService.format_user_data(user)
        }

class PasswordResetService(BaseService):
    @staticmethod
    def request_password_reset(email):
        user = UserRepository.get_by_email(email)
        OTPRepository.check_rate_limit(user)
        OTPRepository.delete_old(user)
        otp = generate_otp()
        OTPRepository.create(user, otp)
        send_otp_email(user, otp)
        return {"message": "OTP sent successfully"}
    
class PasswordResetConfirmService(BaseService):    
    @staticmethod
    def reset_password(email, otp, new_password):
        """Reset password with OTP"""
        user = UserRepository.get_by_email(email)
        otp_obj = OTPRepository.get_valid(user, otp)
        user.change_password(new_password)
        otp_obj.mark_as_used()
        return {"message": "Password Reset Successfully"}