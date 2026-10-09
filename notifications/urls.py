from django.urls import path

from .views import (
    NotificationListAPIView,
    NotificationMarkAllReadAPIView,
    NotificationMarkReadAPIView,
    NotificationUnreadCountAPIView,
)


urlpatterns = [
    path(
        "notifications/",
        NotificationListAPIView.as_view(),
        name="notification-list",
    ),
    path(
        "notifications/unread-count/",
        NotificationUnreadCountAPIView.as_view(),
        name="notification-unread-count",
    ),
    path(
        "notifications/read-all/",
        NotificationMarkAllReadAPIView.as_view(),
        name="notification-read-all",
    ),
    path(
        "notifications/<int:pk>/read/",
        NotificationMarkReadAPIView.as_view(),
        name="notification-read",
    ),
]
