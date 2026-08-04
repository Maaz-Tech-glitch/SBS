from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CreateShopkeeperAPIView,LoginAPIView,LogoutAPIView,UserListAPIView,UserDetailAPIView,ForgotPasswordAPIView,ResetPasswordAPIView


urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("create-shopkeeper/",CreateShopkeeperAPIView.as_view(),name="create-shopkeeper",),
    path("list/", UserListAPIView.as_view(), name="user-list"),
    path("update-user-detail/<int:pk>/", UserDetailAPIView.as_view(), name="user-detail"),
    path("forgot-password/",ForgotPasswordAPIView.as_view(),name="forgot-password",),
    path("reset-password/",ResetPasswordAPIView.as_view(),name="reset-password",),
]
