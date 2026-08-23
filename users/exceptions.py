
class AppException(Exception):
    """Base exception - sab yahan se inherit karte hain"""
    status_code = 400
    message = "An error occurred"
    
    def __init__(self, detail=None):
        self.detail = detail or self.message
        super().__init__(self.detail)


# ========== AUTHENTICATION EXCEPTIONS ==========

class AuthenticationException(AppException):
    """Base authentication exception"""
    status_code = 401
    message = "Authentication failed"


class InvalidCredentialsException(AuthenticationException):
    """Invalid username/password"""
    status_code = 401
    message = "Invalid username or password"


class InvalidTokenException(AuthenticationException):
    """Invalid refresh token"""
    status_code = 400
    message = "Invalid refresh token"


class TokenExpiredException(AuthenticationException):
    """Token expired"""
    status_code = 400
    message = "Token expired"


# ========== USER EXCEPTIONS ==========

class UserException(AppException):
    """Base user exception"""
    status_code = 400
    message = "User error"


class UserNotFoundException(UserException):
    """User not found"""
    status_code = 404
    message = "User not found"


class UserAlreadyExistsException(UserException):
    """User already exists"""
    status_code = 409
    message = "User already exists"


# ========== PASSWORD RESET EXCEPTIONS ==========

class PasswordResetException(AppException):
    """Base password reset exception"""
    status_code = 400
    message = "Password reset failed"


class OTPException(PasswordResetException):
    """OTP related exception"""
    status_code = 400
    message = "OTP error"


class InvalidOTPException(OTPException):
    """Invalid OTP"""
    status_code = 400
    message = "Invalid OTP"


class OTPExpiredException(OTPException):
    """OTP expired"""
    status_code = 400
    message = "OTP Expired"


class RateLimitException(PasswordResetException):
    """Rate limit exceeded"""
    status_code = 429
    message = "Please wait 1 minute before requesting another OTP"
    
class UserAlreadyVerifiedException(UserException):
    status_code = 409
    message = "This account is already verified"
    
class UsernameAlreadyExistsException(UserException):
    status_code = 409
    message = "Username already taken"


class EmailAlreadyExistsException(UserException):
    status_code = 409
    message = "Email already registered"
    
class UserLimitExceededException(UserException):
    status_code = 403
    message = "Maximum staff users reached for your current plan"