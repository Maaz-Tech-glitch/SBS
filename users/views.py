from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdmin
from .serializers import CreateShopkeeperSerializer, UserSerializer, LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from .models import User, PasswordResetOTP
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from .services import generate_otp, send_otp_email
from django.utils import timezone
from datetime import timedelta
from  config.pagination import CustomPagination


# 
class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]

            user = authenticate(username=username, password=password)

            if user is None:
                return Response(
                    {"message": "Invalid username or password"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Login Successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "role": user.role,
                }
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout Successful"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"message": "Invalid Token"}, status=status.HTTP_400_BAD_REQUEST)


class CreateShopkeeperAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    def post(self, request):
        serializer = CreateShopkeeperSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Shopkeeper Created Successfully"}, status=status.HTTP_201_CREATED)


class UserListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    def get(self, request):
        users = User.objects.all()
        paginator = CustomPagination()
        paginated_users = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(paginated_users, many=True)
        return paginator.get_paginated_response(serializer.data)


class UserDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class ForgotPasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            one_minute_ago = timezone.now() - timedelta(minutes=1)
            recent_otp = PasswordResetOTP.objects.filter(user=user, created_at__gte=one_minute_ago).exists()
            if recent_otp:
                return Response(
                    {"message": "Please wait 1 minute before requesting another OTP."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            PasswordResetOTP.objects.filter(user=user, is_used=False).delete()
        except User.DoesNotExist:
            return Response({"message": "No account found with this email."}, status=404)

        otp = generate_otp()
        PasswordResetOTP.objects.create(user=user, otp=otp)
        send_otp_email(user, otp)
        return Response({"message": "OTP sent successfully."}, status=200)


class ResetPasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]
        try:
            user = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.get(user=user, otp=otp, is_used=False)
        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            return Response({"message": "Invalid OTP"}, status=400)

        if otp_obj.expires_at < timezone.now():
            return Response({"message": "OTP Expired"}, status=400)

        user.set_password(new_password)
        user.save()
        otp_obj.is_used = True
        otp_obj.save()
        return Response({"message": "Password Reset Successfully"})