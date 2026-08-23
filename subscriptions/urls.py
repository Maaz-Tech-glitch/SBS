from django.urls import path
from .views import PlanListAPIView, SubscribeAPIView, CurrentSubscriptionAPIView, SubscriptionHistoryAPIView

urlpatterns = [
    path("plans/", PlanListAPIView.as_view(), name="plan-list"),
    path("subscribe/", SubscribeAPIView.as_view(), name="subscribe"),
    path("current/", CurrentSubscriptionAPIView.as_view(), name="current-subscription"),
    path("history/", SubscriptionHistoryAPIView.as_view(), name="subscription-history"),
]