import smtplib
import dns.resolver
from rest_framework import serializers
from .models import User


from rest_framework import serializers

from .models import User


# =========================================================
# LOGIN
# =========================================================

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=False,
        allow_blank=True
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True
    )

    password = serializers.CharField(
        write_only=True
    )

    def validate(self, data):
        if (
            not data.get("username")
            and not data.get("email")
        ):
            raise serializers.ValidationError(
                "Either username or email is required."
            )

        return data


# =========================================================
# CREATE SHOPKEEPER / STAFF
# =========================================================

class CreateShopkeeperSerializer(
    serializers.ModelSerializer
):
    password = serializers.CharField(
        write_only=True
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password",
            "phone",
        ]

    def create(self, validated_data):
        tenant = validated_data.pop(
            "tenant",
            None
        )

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            phone=validated_data.get(
                "phone",
                ""
            ),
            tenant=tenant,
            role="shopkeeper",
        )

        return user


# =========================================================
# USER
# =========================================================

class UserSerializer(
    serializers.ModelSerializer
):
    tenant_name = serializers.CharField(
        source="tenant.name",
        read_only=True,
        default=None
    )

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "role",
            "phone",
            "tenant",
            "tenant_name",
        ]

        read_only_fields = [
            "id",
            "tenant",
            "role",
        ]


# =========================================================
# PASSWORD RESET
# =========================================================

class ForgotPasswordSerializer(
    serializers.Serializer
):
    email = serializers.EmailField()


class VerifyPasswordOTPSerializer(
    serializers.Serializer
):
    email = serializers.EmailField()

    otp = serializers.CharField(
        min_length=6,
        max_length=6
    )

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP must contain only numbers."
            )

        return value


class SetNewPasswordSerializer(
    serializers.Serializer
):
    reset_token = serializers.CharField()

    new_password = serializers.CharField(
        min_length=8,
        write_only=True
    )


# # =========================================================
# # SIGNUP - GET OTP
# # =========================================================

# class SignupOTPRequestSerializer(
#     serializers.Serializer
# ):
#     shop_name = serializers.CharField(
#         max_length=200
#     )

#     business_type = serializers.CharField(
#         max_length=100
#     )

#     email = serializers.EmailField()


# # =========================================================
# # SIGNUP - VERIFY OTP + CREATE ACCOUNT
# # =========================================================

# class SignupOTPVerifySerializer(
#     serializers.Serializer
# ):
#     shop_name = serializers.CharField(
#         max_length=200
#     )

#     shop_address = serializers.CharField(
#         required=False,
#         allow_blank=True,
#         max_length=255
#     )

#     business_type = serializers.CharField(
#         max_length=100
#     )

#     username = serializers.CharField(
#         max_length=150
#     )

#     email = serializers.EmailField()

#     password = serializers.CharField(
#         write_only=True,
#         min_length=8
#     )

#     phone = serializers.CharField(
#         required=False,
#         allow_blank=True,
#         max_length=15
#     )

#     otp = serializers.CharField(
#         min_length=6,
#         max_length=6
#     )

#     def validate_otp(self, value):
#         if not value.isdigit():
#             raise serializers.ValidationError(
#                 "OTP must contain only numbers."
#             )

#         return value

# =========================================================
# SIGNUP - GET OTP
# =========================================================

class SignupOTPRequestSerializer(serializers.Serializer):
    shop_name = serializers.CharField(
        max_length=200
    )

    business_type = serializers.CharField(
        max_length=100
    )

    email = serializers.EmailField()


# =========================================================
# SIGNUP - VERIFY OTP ONLY
# =========================================================

class SignupOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()

    otp = serializers.CharField(
        min_length=6,
        max_length=6
    )

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP must contain only numbers."
            )

        return value


# =========================================================
# SIGNUP - ACTUAL CREATE ACCOUNT
# =========================================================

class SignupSerializer(serializers.Serializer):
    shop_name = serializers.CharField(
        max_length=200
    )

    shop_address = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255
    )

    business_type = serializers.CharField(
        max_length=100
    )

    username = serializers.CharField(
        max_length=150
    )

    email = serializers.EmailField()

    password = serializers.CharField(
        min_length=8,
        write_only=True
    )

    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=15
    )

    verification_token = serializers.CharField(
        write_only=True
    )