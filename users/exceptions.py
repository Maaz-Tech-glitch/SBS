class AppException(Exception):
    """
    Base application exception.
    """

    status_code = 400
    message = "An error occurred"

    def __init__(self, detail=None):
        self.detail = detail or self.message
        super().__init__(self.detail)


# =========================================================
# AUTHENTICATION
# =========================================================

class AuthenticationException(AppException):
    status_code = 401
    message = "Authentication failed"


class InvalidCredentialsException(AuthenticationException):
    status_code = 401
    message = "Invalid username or password"


class InvalidTokenException(AuthenticationException):
    status_code = 400
    message = "Invalid refresh token"


class TokenExpiredException(AuthenticationException):
    status_code = 400
    message = "Token expired"


# =========================================================
# USER
# =========================================================

class UserException(AppException):
    status_code = 400
    message = "User error"


class UserNotFoundException(UserException):
    status_code = 404
    message = "User not found"


class UserAlreadyExistsException(UserException):
    status_code = 409
    message = "User already exists"


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
    message = (
        "Maximum staff users reached "
        "for your current plan"
    )


# =========================================================
# PASSWORD RESET / OTP
# =========================================================

class PasswordResetException(AppException):
    status_code = 400
    message = "Password reset failed"


class OTPException(PasswordResetException):
    status_code = 400
    message = "OTP error"


class InvalidOTPException(OTPException):
    status_code = 400
    message = "Invalid OTP"


class OTPExpiredException(OTPException):
    status_code = 400
    message = "OTP Expired"


class RateLimitException(PasswordResetException):
    status_code = 429
    message = (
        "Please wait 1 minute before "
        "requesting another OTP"
    )


# =========================================================
# PASSWORD RESET TOKEN
# =========================================================

class InvalidResetTokenException(PasswordResetException):
    status_code = 400
    message = "Invalid password reset session"


class ResetTokenExpiredException(PasswordResetException):
    status_code = 400
    message = "Password reset session expired"


# =========================================================
# SIGNUP VERIFICATION TOKEN
# =========================================================

class SignupVerificationException(UserException):
    status_code = 400
    message = "Email verification failed"


class InvalidSignupVerificationTokenException(
    SignupVerificationException
):
    status_code = 400
    message = (
        "Email verification is invalid. "
        "Please verify your email again."
    )


class SignupVerificationExpiredException(
    SignupVerificationException
):
    status_code = 400
    message = (
        "Email verification expired. "
        "Please verify your email again."
    )