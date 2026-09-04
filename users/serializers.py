import smtplib
import dns.resolver
from rest_framework import serializers
from .models import User

# Login Serializer
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    def validate(self, data):
        if not data.get("username") and not data.get("email"):
            raise serializers.ValidationError("Either username or email is required.")
        return data
# Shopkeeper Serializer
class CreateShopkeeperSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "phone",
        ]
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            phone=validated_data["phone"],
            role="shopkeeper",
        )
        return user
# User Serializer   
class UserSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True, default=None)
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

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=15)
class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    
    


def validate_email_exists(email):
    domain = email.split("@")[-1]
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = str(mx_records[0].exchange)
    except Exception:
        raise serializers.ValidationError("This email domain does not exist.")

    try:
        server = smtplib.SMTP(timeout=10)
        server.connect(mx_host)
        server.helo(server.local_hostname)
        server.mail("verify@example.com")
        code, _ = server.rcpt(email)
        server.quit()

        if code not in (250, 251):
            raise serializers.ValidationError("This email address does not exist.")
    except serializers.ValidationError:
        raise
    except Exception:
        # SMTP server response na de (Gmail jaise providers block karte hain) -
        # to hum reject nahi karte, warna real users bhi block ho jayenge
        pass


# class SignupSerializer(serializers.Serializer):
#     username = serializers.CharField(max_length=150)
#     email = serializers.EmailField(validators=[validate_email_exists])
#     password = serializers.CharField(write_only=True, min_length=8)
#     phone = serializers.CharField(required=False, allow_blank=True, max_length=15)
class SignupSerializer(serializers.Serializer):
    shop_name = serializers.CharField(max_length=200)
    shop_address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    business_type = serializers.CharField(required=False, allow_blank=True, max_length=100)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(validators=[validate_email_exists])
    password = serializers.CharField(write_only=True, min_length=8)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=15)