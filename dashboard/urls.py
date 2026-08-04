from django.urls import path
from .views import DashboardSummaryAPIView

urlpatterns = [
    path("summary/",DashboardSummaryAPIView.as_view(),),
    ]