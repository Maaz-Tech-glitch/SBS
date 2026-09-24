# =========================================================
# REPOSITORIES
# Database access logic
# =========================================================

from .models import (
    User,
    PasswordResetOTP,
    EmailVerificationOTP,
)

from .exceptions import (
    UserNotFoundException,
    InvalidOTPException,
    OTPExpiredException,
    RateLimitException,
)


# =========================================================
# USER REPOSITORY
# =========================================================

class UserRepository:

    @staticmethod
    def get_by_email(email):
        try:
            return User.objects.get(
                email__iexact=email
            )

        except User.DoesNotExist:
            raise UserNotFoundException(
                "User with email not found"
            )


    @staticmethod
    def get_by_username(username):
        try:
            return User.objects.get(
                username=username
            )

        except User.DoesNotExist:
            raise UserNotFoundException(
                "User with username not found"
            )


    @staticmethod
    def get_by_id(user_id):
        try:
            return User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:
            raise UserNotFoundException(
                "User not found"
            )


# =========================================================
# PASSWORD RESET OTP REPOSITORY
# =========================================================

class OTPRepository:

    @staticmethod
    def create(user, otp):
        return (
            PasswordResetOTP
            .objects
            .create(
                user=user,
                otp=otp,
            )
        )


    @staticmethod
    def get_valid(user, otp):
        try:
            otp_obj = (
                PasswordResetOTP
                .objects
                .get(
                    user=user,
                    otp=otp,
                    is_used=False,
                )
            )

        except PasswordResetOTP.DoesNotExist:
            raise InvalidOTPException()

        if otp_obj.is_expired():
            raise OTPExpiredException()

        return otp_obj


    @staticmethod
    def check_rate_limit(user):

        recent_otp = (
            PasswordResetOTP
            .objects
            .get_recent(
                user,
                minutes=1
            )
            .exists()
        )

        if recent_otp:
            raise RateLimitException()


    @staticmethod
    def delete_old(user):

        (
            PasswordResetOTP
            .objects
            .filter(
                user=user,
                is_used=False,
            )
            .delete()
        )


# =========================================================
# OLD EMAIL OTP REPOSITORY
#
# Ab new signup flow isko use nahi karta,
# lekin filhal remove nahi kar rahe taa-ke
# kisi purane code par unnecessary effect na aaye.
# =========================================================

class EmailOTPRepository:

    @staticmethod
    def create(user, otp):
        return (
            EmailVerificationOTP
            .objects
            .create(
                user=user,
                otp=otp,
            )
        )


    @staticmethod
    def get_valid(user, otp):
        try:
            otp_obj = (
                EmailVerificationOTP
                .objects
                .get(
                    user=user,
                    otp=otp,
                    is_used=False,
                )
            )

        except EmailVerificationOTP.DoesNotExist:
            raise InvalidOTPException()

        if otp_obj.is_expired():
            raise OTPExpiredException()

        return otp_obj


    @staticmethod
    def check_rate_limit(user):

        recent_otp = (
            EmailVerificationOTP
            .objects
            .get_recent(
                user,
                minutes=1
            )
            .exists()
        )

        if recent_otp:
            raise RateLimitException()


    @staticmethod
    def delete_old(user):

        (
            EmailVerificationOTP
            .objects
            .filter(
                user=user,
                is_used=False,
            )
            .delete()
        )