from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginAPIView, LogoutAPIView, UserListCreateAPIView, UserDetailAPIView,
    ForgotPasswordAPIView, ResetPasswordAPIView,
    SignupAPIView, VerifyEmailAPIView, ResendVerificationEmailAPIView,
)

urlpatterns = [
    # Auth Endpoints
    path("auth/signup/", SignupAPIView.as_view(), name="auth-signup"),
    path("auth/verify-email/", VerifyEmailAPIView.as_view(), name="auth-verify-email"),
    path("auth/resend-verification/", ResendVerificationEmailAPIView.as_view(), name="auth-resend-verification"),
    path("auth/login/", LoginAPIView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="auth-logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/password/forgot/", ForgotPasswordAPIView.as_view(), name="auth-password-forgot"),
    path("auth/password/reset/", ResetPasswordAPIView.as_view(), name="auth-password-reset"),

    # Users RESTful Endpoints
    path("users/", UserListCreateAPIView.as_view(), name="user-list-create"),
    path("users/<int:pk>/", UserDetailAPIView.as_view(), name="user-detail"),
]