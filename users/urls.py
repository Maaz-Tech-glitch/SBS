from django.urls import path

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from .views import (
    # Signup
    SignupOTPRequestAPIView,
    SignupOTPVerifyAPIView,
    SignupAPIView,

    # Login
    LoginAPIView,
    LogoutAPIView,

    # Password Reset
    ForgotPasswordAPIView,
    VerifyPasswordOTPAPIView,
    SetNewPasswordAPIView,

    # Users
    UserListCreateAPIView,
    UserDetailAPIView,
    UserModulePermissionAPIView,
)


urlpatterns = [

    # =====================================================
    # SIGNUP
    # =====================================================

    path(
        "auth/signup/request-otp/",
        SignupOTPRequestAPIView.as_view(),
        name="signup-request-otp",
    ),

    path(
        "auth/signup/verify-otp/",
        SignupOTPVerifyAPIView.as_view(),
        name="signup-verify-otp",
    ),

    path(
        "auth/signup/",
        SignupAPIView.as_view(),
        name="auth-signup",
    ),


    # =====================================================
    # LOGIN / LOGOUT
    # =====================================================

    path(
        "auth/login/",
        LoginAPIView.as_view(),
        name="auth-login",
    ),

    path(
        "auth/logout/",
        LogoutAPIView.as_view(),
        name="auth-logout",
    ),

    path(
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="auth-token-refresh",
    ),


    # =====================================================
    # PASSWORD RESET
    # =====================================================

    path(
        "auth/password/forgot/",
        ForgotPasswordAPIView.as_view(),
        name="auth-password-forgot",
    ),

    path(
        "auth/password/verify-otp/",
        VerifyPasswordOTPAPIView.as_view(),
        name="auth-password-verify-otp",
    ),

    path(
        "auth/password/set-new/",
        SetNewPasswordAPIView.as_view(),
        name="auth-password-set-new",
    ),


    # =====================================================
    # USERS
    # =====================================================

    path(
        "users/",
        UserListCreateAPIView.as_view(),
        name="user-list-create",
    ),

    path(
        "users/<int:pk>/",
        UserDetailAPIView.as_view(),
        name="user-detail",
    ),

    path(
        "users/<int:user_id>/module-permissions/",
        UserModulePermissionAPIView.as_view(),
        name="user-module-permissions",
    ),
]