import random

from django.conf import settings
from django.contrib.auth.hashers import (
    make_password,
    check_password,
)
from django.core import signing
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction

from rest_framework_simplejwt.tokens import RefreshToken

from .repositories import (
    UserRepository,
    OTPRepository,
)

from .models import AccessModule, UserModulePermission

from .strategies import AuthenticationFactory

from .exceptions import (
    InvalidTokenException,
    UsernameAlreadyExistsException,
    EmailAlreadyExistsException,
    InvalidOTPException,
    OTPExpiredException,
    RateLimitException,
    InvalidResetTokenException,
    ResetTokenExpiredException,
    InvalidSignupVerificationTokenException,
    SignupVerificationExpiredException,
)


# =========================================================
# BASE SERVICE
# =========================================================

class BaseService:

    @staticmethod
    def validate_not_none(value, message):
        if not value:
            raise ValueError(message)


# =========================================================
# OTP GENERATOR
# =========================================================

def generate_otp():
    return str(
        random.randint(
            100000,
            999999
        )
    )


# =========================================================
# PASSWORD RESET EMAIL
# =========================================================

def send_otp_email(user, otp):
    subject = "SBS POS - Password Reset OTP"

    message = f"""
Hello {user.username},

Your OTP for password reset is:

{otp}

This OTP will expire in 1 minute.

If you did not request this,
please ignore this email.

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


# =========================================================
# SIGNUP OTP EMAIL
# =========================================================

def send_signup_otp_email(email, otp):
    subject = "SBS POS - Verify Your Email"

    message = f"""
Hello,

Your SBS POS email verification code is:

{otp}

This OTP will expire in 1 minute.

If you did not request this code,
please ignore this email.

Thank you,
SBS POS Team
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


# =========================================================
# SIGNUP OTP SERVICE
# =========================================================

class SignupOTPService(BaseService):

    # OTP itself valid for 1 minute
    OTP_EXPIRE_SECONDS = 60

    # User can request another OTP after 1 minute
    RESEND_COOLDOWN_SECONDS = 60

    # After email verification,
    # user has 5 minutes to create account
    VERIFICATION_TOKEN_SECONDS = 300

    @staticmethod
    def _otp_key(email):
        email = email.strip().lower()

        return f"signup_otp:{email}"

    @staticmethod
    def _cooldown_key(email):
        email = email.strip().lower()

        return f"signup_otp_cooldown:{email}"

    # =====================================================
    # STEP 1 - SEND SIGNUP OTP
    # =====================================================

    @staticmethod
    def request_otp(
        shop_name,
        business_type,
        email,
    ):
        from .models import User

        email = email.strip().lower()
        shop_name = shop_name.strip()
        business_type = business_type.strip()

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not shop_name:
            raise ValueError(
                "Shop name is required"
            )

        if not business_type:
            raise ValueError(
                "Business type is required"
            )

        # -------------------------------------------------
        # EMAIL ALREADY REGISTERED
        # -------------------------------------------------

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise EmailAlreadyExistsException()

        # -------------------------------------------------
        # RESEND LIMIT
        # -------------------------------------------------

        cooldown_key = (
            SignupOTPService
            ._cooldown_key(email)
        )

        if cache.get(cooldown_key):
            raise RateLimitException()

        # -------------------------------------------------
        # GENERATE OTP
        # -------------------------------------------------

        otp = generate_otp()

        otp_key = (
            SignupOTPService
            ._otp_key(email)
        )

        # Store OTP hash + signup information temporarily.
        # Nothing is created in Tenant/User tables yet.

        cache.set(
            otp_key,
            {
                "otp_hash": make_password(otp),
                "shop_name": shop_name,
                "business_type": business_type,
            },
            timeout=(
                SignupOTPService
                .OTP_EXPIRE_SECONDS
            ),
        )

        # Prevent immediate resend

        cache.set(
            cooldown_key,
            True,
            timeout=(
                SignupOTPService
                .RESEND_COOLDOWN_SECONDS
            ),
        )

        # -------------------------------------------------
        # SEND EMAIL
        # -------------------------------------------------

        send_signup_otp_email(
            email=email,
            otp=otp,
        )

        return {
            "otp_sent": True,
            "expires_in": 60,
        }

    # =====================================================
    # STEP 2 - VERIFY OTP ONLY
    #
    # ACCOUNT IS NOT CREATED HERE
    # =====================================================

    @staticmethod
    def verify_otp(email, otp):
        from .models import User

        email = email.strip().lower()

        # Prevent verification if account
        # was already created meanwhile.

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise EmailAlreadyExistsException()

        otp_key = (
            SignupOTPService
            ._otp_key(email)
        )

        otp_data = cache.get(
            otp_key
        )

        # -------------------------------------------------
        # OTP MISSING / EXPIRED
        # -------------------------------------------------

        if not otp_data:
            raise OTPExpiredException()

        stored_otp_hash = (
            otp_data.get(
                "otp_hash"
            )
        )

        if not stored_otp_hash:
            raise OTPExpiredException()

        # -------------------------------------------------
        # OTP CHECK
        # -------------------------------------------------

        if not check_password(
            otp,
            stored_otp_hash
        ):
            raise InvalidOTPException()

        # -------------------------------------------------
        # EMAIL VERIFIED
        #
        # Create temporary signed token.
        # This does NOT create shop/user.
        # -------------------------------------------------

        verification_token = signing.dumps(
            {
                "email": email,

                "shop_name":
                    otp_data["shop_name"],

                "business_type":
                    otp_data[
                        "business_type"
                    ],

                "purpose":
                    "signup_email_verified",
            },
            salt=
                "sbs-signup-verification",
        )

        # OTP cannot be used again

        cache.delete(
            otp_key
        )

        cache.delete(
            SignupOTPService
            ._cooldown_key(email)
        )

        return {
            "verified": True,

            "verification_token":
                verification_token,

            # Frontend shows verified state
            # for maximum 5 minutes.
            "expires_in":
                SignupOTPService
                .VERIFICATION_TOKEN_SECONDS,
        }


# =========================================================
# FINAL SIGNUP SERVICE
# =========================================================

class SignupService(BaseService):

    @staticmethod
    def register(
        shop_name,
        business_type,
        username,
        email,
        password,
        verification_token,
        phone="",
        shop_address="",
    ):
        from .models import User

        from tenants.services import (
            TenantService,
        )

        # =====================================================
        # CLEAN INPUT
        # =====================================================

        email = email.strip().lower()
        username = username.strip()
        shop_name = shop_name.strip()
        business_type = business_type.strip()


        # =====================================================
        # VERIFY EMAIL VERIFICATION TOKEN
        # =====================================================

        try:
            payload = signing.loads(
                verification_token,

                salt="sbs-signup-verification",

                # Email verification valid for 5 minutes
                max_age=(
                    SignupOTPService
                    .VERIFICATION_TOKEN_SECONDS
                ),
            )

        except signing.SignatureExpired:
            raise SignupVerificationExpiredException()

        except signing.BadSignature:
            raise InvalidSignupVerificationTokenException()


        # =====================================================
        # TOKEN PURPOSE CHECK
        # =====================================================

        if (
            payload.get("purpose")
            != "signup_email_verified"
        ):
            raise InvalidSignupVerificationTokenException()


        # =====================================================
        # VERIFIED EMAIL MUST MATCH
        # =====================================================

        verified_email = (
            payload
            .get("email", "")
            .strip()
            .lower()
        )

        if verified_email != email:
            raise InvalidSignupVerificationTokenException(
                "Email was changed. "
                "Please verify the email again."
            )


        # =====================================================
        # VERIFIED SHOP NAME MUST MATCH
        # =====================================================

        verified_shop_name = (
            payload
            .get("shop_name", "")
            .strip()
        )

        if verified_shop_name != shop_name:
            raise InvalidSignupVerificationTokenException(
                "Shop name was changed. "
                "Please verify email again."
            )


        # =====================================================
        # VERIFIED BUSINESS TYPE MUST MATCH
        # =====================================================

        verified_business_type = (
            payload
            .get(
                "business_type",
                ""
            )
            .strip()
        )

        if (
            verified_business_type
            != business_type
        ):
            raise InvalidSignupVerificationTokenException(
                "Business type was changed. "
                "Please verify email again."
            )


        # =====================================================
        # DUPLICATE CHECK
        # =====================================================

        if User.objects.filter(
            username=username
        ).exists():
            raise UsernameAlreadyExistsException()

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise EmailAlreadyExistsException()


        # =====================================================
        # CREATE TENANT + ADMIN
        # =====================================================

        with transaction.atomic():

            # Double-check inside transaction

            if User.objects.filter(
                username=username
            ).exists():
                raise UsernameAlreadyExistsException()

            if User.objects.filter(
                email__iexact=email
            ).exists():
                raise EmailAlreadyExistsException()


            # =================================================
            # CREATE SHOP / TENANT
            # =================================================

            tenant = (
                TenantService
                .create_tenant(
                    name=shop_name,
                    email=email,
                    phone=phone,
                    address=shop_address,
                    business_type=business_type,
                )
            )


            # =================================================
            # CREATE ADMIN USER
            # =================================================

            user = (
                User.objects
                .create_user(
                    username=username,
                    email=email,
                    password=password,
                    phone=phone,
                    role="admin",
                    tenant=tenant,

                    # Email already verified using OTP
                    is_email_verified=True,
                )
            )


        # =====================================================
        # GENERATE JWT TOKENS
        #
        # Account create hone ke baad user temporarily
        # authenticated hoga taake subscription choose kar sake.
        # =====================================================

        tokens = (
            TokenService
            .generate_tokens(user)
        )


        # =====================================================
        # RESPONSE
        # =====================================================

        return {
            "account_created": True,

            "access":
                tokens["access"],

            "refresh":
                tokens["refresh"],

            "user": {
                "id":
                    user.id,

                "username":
                    user.username,

                "email":
                    user.email,

                "phone":
                    user.phone,

                "role":
                    user.role,

                "tenant_id":
                    user.tenant_id,

                "tenant_name":
                    (
                        user.tenant.name
                        if user.tenant
                        else None
                    ),
            },

            # New user ne abhi plan choose nahi kiya
            "subscription_active": False,
        }

# =========================================================
# AUTHENTICATION
# =========================================================

class AuthenticationService(BaseService):

    @staticmethod
    def authenticate_user(
        username,
        password,
        strategy_type="username"
    ):
        strategy = (
            AuthenticationFactory
            .get_strategy(
                strategy_type
            )
        )

        return strategy.authenticate(
            username=username,
            password=password
        )


# =========================================================
# JWT TOKEN SERVICE
# =========================================================

class TokenService(BaseService):

    @staticmethod
    def generate_tokens(user):

        refresh = (
            RefreshToken.for_user(
                user
            )
        )

        return {
            "access":
                str(
                    refresh.access_token
                ),

            "refresh":
                str(refresh),
        }

    @staticmethod
    def validate_refresh_token(
        refresh_token
    ):

        if not refresh_token:
            raise InvalidTokenException(
                "Refresh token required"
            )

        try:
            return RefreshToken(
                refresh_token
            )

        except Exception:
            raise (
                InvalidTokenException()
            )


# =========================================================
# LOGOUT
# =========================================================

class LogoutService(BaseService):

    @staticmethod
    def logout_user(
        refresh_token
    ):

        token = (
            TokenService
            .validate_refresh_token(
                refresh_token
            )
        )

        token.blacklist()

        return True


# =========================================================
# RESPONSE FORMATTER
# =========================================================

class ModulePermissionService(BaseService):

    DEFAULT_MODULES = [
        {"key": "dashboard", "name": "Dashboard", "category": "Overview"},
        {"key": "products", "name": "Products", "category": "Inventory"},
        {"key": "billing", "name": "Billing", "category": "Sales"},
        {"key": "accounting", "name": "Accounting", "category": "Finance"},
        {"key": "reports", "name": "Reports", "category": "Analytics"},
    ]

    @staticmethod
    def ensure_default_modules():
        for module_data in ModulePermissionService.DEFAULT_MODULES:
            AccessModule.objects.get_or_create(
                key=module_data["key"],
                defaults={
                    "name": module_data["name"],
                    "category": module_data["category"],
                    "is_active": True,
                },
            )

    @staticmethod
    def get_active_modules():
        ModulePermissionService.ensure_default_modules()
        return AccessModule.objects.filter(is_active=True).order_by("category", "name")

    @staticmethod
    def get_allowed_module_keys(user):
        if not user or not getattr(user, "is_authenticated", False):
            return []

        if getattr(user, "role", None) == "admin":
            return list(
                ModulePermissionService
                .get_active_modules()
                .values_list("key", flat=True)
            )

        return list(
            UserModulePermission.objects.filter(
                user=user,
                module__is_active=True,
                can_access=True,
            ).values_list("module__key", flat=True)
        )

    @staticmethod
    def has_module_access(user, module_key):
        if not user or not getattr(user, "is_authenticated", False):
            return False

        if getattr(user, "role", None) == "admin":
            return AccessModule.objects.filter(key=module_key, is_active=True).exists()

        return UserModulePermission.objects.filter(
            user=user,
            module__key=module_key,
            module__is_active=True,
            can_access=True,
        ).exists()

    @staticmethod
    def get_user_module_status(user):
        active_modules = ModulePermissionService.get_active_modules()
        granted_keys = set(ModulePermissionService.get_allowed_module_keys(user))

        return [
            {
                "key": module.key,
                "name": module.name,
                "category": module.category,
                "can_access": module.key in granted_keys,
            }
            for module in active_modules
        ]

    @staticmethod
    def set_user_permissions(admin_user, target_user, module_keys):
        if not admin_user or not admin_user.is_authenticated:
            raise ValueError("Authentication required.")

        if getattr(admin_user, "role", None) != "admin":
            raise ValueError("Only admin users can manage module permissions.")

        if target_user is None:
            raise ValueError("Target user is required.")

        if target_user.role != "shopkeeper":
            raise ValueError("Permissions can only be assigned to shopkeepers.")

        if target_user.tenant_id != admin_user.tenant_id:
            raise ValueError("You cannot manage permissions for a different tenant.")

        if target_user.id == admin_user.id:
            raise ValueError("You cannot change your own module permissions.")

        valid_module_keys = set(
            ModulePermissionService.get_active_modules().values_list("key", flat=True)
        )

        invalid_keys = [key for key in module_keys if key not in valid_module_keys]
        if invalid_keys:
            raise ValueError(f"Invalid module keys: {', '.join(invalid_keys)}")

        allowed_set = set(module_keys)

        with transaction.atomic():
            for module in ModulePermissionService.get_active_modules():
                permission, created = UserModulePermission.objects.get_or_create(
                    user=target_user,
                    module=module,
                    defaults={"can_access": module.key in allowed_set, "granted_by": admin_user},
                )
                permission.can_access = module.key in allowed_set
                permission.granted_by = admin_user
                permission.save(update_fields=["can_access", "granted_by", "updated_at"])

        return ModulePermissionService.get_user_module_status(target_user)


class ResponseFormatterService(BaseService):

    @staticmethod
    def format_user_data(user):

        return {
            "tenant_id":
                user.tenant_id,

            "tenant_name":
                user.tenant.name
                if user.tenant
                else None,

            "id":
                user.id,

            "username":
                user.username,

            "email":
                user.email,

            "phone":
                user.phone,

            "role":
                user.role,
        }

    @staticmethod
    def format_login_response(
        user,
        tokens
    ):

        return {
            "message":
                "Login Successful",

            "access":
                tokens["access"],

            "refresh":
                tokens["refresh"],

            "user":
                ResponseFormatterService
                .format_user_data(user),
        }


# =========================================================
# PASSWORD RESET - SEND OTP
# =========================================================

class PasswordResetService(BaseService):

    @staticmethod
    def request_password_reset(
        email
    ):

        user = (
            UserRepository
            .get_by_email(email)
        )

        OTPRepository.check_rate_limit(
            user
        )

        OTPRepository.delete_old(
            user
        )

        otp = generate_otp()

        OTPRepository.create(
            user,
            otp
        )

        send_otp_email(
            user,
            otp
        )

        return {
            "message":
                "OTP sent successfully"
        }


# =========================================================
# PASSWORD RESET - VERIFY OTP
# =========================================================

class PasswordOTPVerificationService(
    BaseService
):

    @staticmethod
    def verify(
        email,
        otp
    ):

        user = (
            UserRepository
            .get_by_email(email)
        )

        otp_obj = (
            OTPRepository
            .get_valid(
                user,
                otp
            )
        )

        # OTP cannot be reused

        otp_obj.mark_as_used()

        # Temporary reset token

        reset_token = signing.dumps(
            {
                "user_id":
                    user.id,

                "password_hash":
                    user.password,

                "purpose":
                    "password_reset",
            },

            salt=
                "sbs-password-reset",
        )

        return {
            "message":
                "OTP verified successfully",

            "reset_token":
                reset_token,
        }


# =========================================================
# PASSWORD RESET - SET NEW PASSWORD
# =========================================================

class SetNewPasswordService(BaseService):

    @staticmethod
    def set_password(
        reset_token,
        new_password
    ):

        try:
            payload = signing.loads(
                reset_token,

                salt=
                    "sbs-password-reset",

                max_age=600,
            )

        except signing.SignatureExpired:
            raise (
                ResetTokenExpiredException()
            )

        except signing.BadSignature:
            raise (
                InvalidResetTokenException()
            )

        # -------------------------------------------------
        # PURPOSE CHECK
        # -------------------------------------------------

        if (
            payload.get("purpose")
            != "password_reset"
        ):
            raise (
                InvalidResetTokenException()
            )

        # -------------------------------------------------
        # GET USER
        # -------------------------------------------------

        user = (
            UserRepository
            .get_by_id(
                payload["user_id"]
            )
        )

        # -------------------------------------------------
        # PREVENT TOKEN REUSE
        # -------------------------------------------------

        if (
            user.password
            != payload.get(
                "password_hash"
            )
        ):
            raise (
                InvalidResetTokenException(
                    "Password reset session "
                    "already used"
                )
            )

        # -------------------------------------------------
        # CHANGE PASSWORD
        # -------------------------------------------------

        user.change_password(
            new_password
        )

        return {
            "message":
                "Password Reset Successfully"
        }