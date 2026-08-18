from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .permissions import IsAdmin
from .serializers import (
    CreateShopkeeperSerializer, 
    UserSerializer, 
    LoginSerializer, 
    ForgotPasswordSerializer, 
    ResetPasswordSerializer
)
from .models import User
from .services import (
    AuthenticationService,
    TokenService,
    LogoutService,
    ResponseFormatterService,
    PasswordResetService,
    PasswordResetConfirmService
)
from config.pagination import CustomPagination


# ========== BASE VIEW (ABSTRACTION) ==========

class BaseAPIView(APIView):
    """Base view - avoid code repetition"""
    
    def success_response(self, data=None, message="Success", status_code=200):
        """Standard success response"""
        response = {"message": message}
        if data:
            response["data"] = data
        return Response(response, status=status_code)
    
    def error_response(self, error, status_code=400):
        """Standard error response"""
        return Response({"error": error}, status=status_code)


# ========== AUTHENTICATION VIEWS ==========

class LoginAPIView(BaseAPIView):
    """Login endpoint"""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = AuthenticationService.authenticate_user(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"]
        )
        
        tokens = TokenService.generate_tokens(user)
        response_data = ResponseFormatterService.format_login_response(user, tokens)
        
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutAPIView(BaseAPIView):
    """Logout endpoint"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        LogoutService.logout_user(refresh_token)
        
        return self.success_response(message="Logout Successful")


# ========== USER MANAGEMENT VIEWS ==========

class UserListCreateAPIView(ListCreateAPIView):
    """List users and create new user"""
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        return CreateShopkeeperSerializer if self.request.method == 'POST' else UserSerializer

    def get_queryset(self):
        queryset = User.objects.all()
        
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(username__icontains=search)
        
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role.lower())
            
        ordering = self.request.query_params.get("ordering")
        if ordering in ("id", "-id", "username", "-username"):
            queryset = queryset.order_by(ordering)
            
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(
            {"message": "User Created Successfully", "data": UserSerializer(user).data}, 
            status=status.HTTP_201_CREATED
        )


class UserDetailAPIView(RetrieveUpdateDestroyAPIView):
    """Get, update, delete user"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


# ========== PASSWORD RESET VIEWS ==========

class ForgotPasswordAPIView(BaseAPIView):
    """Request password reset"""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = PasswordResetService.request_password_reset(
            serializer.validated_data["email"]
        )
        
        return Response(result, status=status.HTTP_200_OK)


class ResetPasswordAPIView(BaseAPIView):
    """Confirm password reset"""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = PasswordResetConfirmService.reset_password(
            email=serializer.validated_data["email"],
            otp=serializer.validated_data["otp"],
            new_password=serializer.validated_data["new_password"]
        )
        
        return Response(result, status=status.HTTP_200_OK)