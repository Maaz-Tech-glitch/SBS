from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django.utils import timezone
from datetime import timedelta

from .permissions import IsAdmin
from .serializers import (
    CreateShopkeeperSerializer, 
    UserSerializer, 
    LoginSerializer, 
    ForgotPasswordSerializer, 
    ResetPasswordSerializer
)
from .models import User, PasswordResetOTP
from .services import generate_otp, send_otp_email
from config.pagination import CustomPagination


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
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


# Combined GET /api/users/ (List) & POST /api/users/ (Create)
class UserListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateShopkeeperSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = User.objects.all()
        search_param = self.request.query_params.get("search")
        if search_param:
            queryset = queryset.filter(username__icontains=search_param)
        
        role_param = self.request.query_params.get("role")
        if role_param:
            queryset = queryset.filter(role=role_param.lower())
            
        ordering_param = self.request.query_params.get("ordering")
        if ordering_param in ("id", "-id", "username", "-username"):
            queryset = queryset.order_by(ordering_param)
            
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_serializer = UserSerializer(user)
        return Response(
            {"message": "User Created Successfully", "data": response_serializer.data}, 
            status=status.HTTP_201_CREATED
        )



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
            return Response({"message": "this email is not our User."}, status=status.HTTP_404_NOT_FOUND)

        otp = generate_otp()
        PasswordResetOTP.objects.create(user=user, otp=otp)
        send_otp_email(user, otp)
        return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)


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
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.expires_at < timezone.now():
            return Response({"message": "OTP Expired"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        otp_obj.is_used = True
        otp_obj.save()
        return Response({"message": "Password Reset Successfully"}, status=status.HTTP_200_OK)