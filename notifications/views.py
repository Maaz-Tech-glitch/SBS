from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .pagination import NotificationPagination
from .permissions import IsNotificationAdmin
from .serializers import NotificationSerializer
from .services import NotificationService


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    pagination_class = NotificationPagination
    permission_classes = [
        IsAuthenticated,
        IsNotificationAdmin,
    ]

    def get_queryset(self):
        queryset = (
            Notification.objects
            .filter(
                tenant=self.request.user.tenant
            )
            .select_related("actor")
            .order_by("-created_at", "-id")
        )

        unread = self.request.query_params.get("unread")
        level = self.request.query_params.get("level")
        event_type = self.request.query_params.get("event_type")

        if unread is not None:
            normalized = unread.strip().lower()

            if normalized in {"1", "true", "yes"}:
                queryset = queryset.filter(is_read=False)
            elif normalized in {"0", "false", "no"}:
                queryset = queryset.filter(is_read=True)

        if level:
            queryset = queryset.filter(
                level=level.strip().upper()
            )

        if event_type:
            queryset = queryset.filter(
                event_type=event_type.strip().upper()
            )

        return queryset


class NotificationUnreadCountAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsNotificationAdmin,
    ]

    def get(self, request):
        count = (
            Notification.objects
            .filter(
                tenant=request.user.tenant,
                is_read=False,
            )
            .count()
        )

        return Response(
            {"unread_count": count},
            status=status.HTTP_200_OK,
        )


class NotificationMarkReadAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsNotificationAdmin,
    ]

    def patch(self, request, pk):
        notification = (
            Notification.objects
            .filter(
                pk=pk,
                tenant=request.user.tenant,
            )
            .first()
        )

        if notification is None:
            return Response(
                {
                    "detail": "Notification not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        NotificationService.mark_read(
            notification=notification,
            tenant=request.user.tenant,
        )

        return Response(
            NotificationSerializer(
                notification
            ).data,
            status=status.HTTP_200_OK,
        )


class NotificationMarkAllReadAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsNotificationAdmin,
    ]

    def post(self, request):
        updated = (
            NotificationService
            .mark_all_read(
                tenant=request.user.tenant
            )
        )

        return Response(
            {
                "message": "Notifications marked as read.",
                "updated_count": updated,
            },
            status=status.HTTP_200_OK,
        )
