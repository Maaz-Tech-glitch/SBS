from django.urls import path
from .views import ShopSetupAPIView

urlpatterns = [
    path("shop/setup/", ShopSetupAPIView.as_view(), name="shop-setup"),
]