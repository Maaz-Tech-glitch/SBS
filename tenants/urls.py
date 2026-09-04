from django.urls import path
from .views import TenantAPIView

urlpatterns = [
    path("", TenantAPIView.as_view(), name="tenant-me"),
]