from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from tenants.models import Tenant

from .models import Notification
from .services import NotificationService


User = get_user_model()


class NotificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.tenant = Tenant.objects.create(
            name="Shop One",
            address="One Road",
            business_type="Retail",
        )

        self.other_tenant = Tenant.objects.create(
            name="Shop Two",
            address="Two Road",
            business_type="Retail",
        )

        self.admin = User.objects.create_user(
            username="admin-one",
            email="admin-one@example.com",
            password="password",
            tenant=self.tenant,
            role="admin",
        )

        self.shopkeeper = User.objects.create_user(
            username="staff-one",
            email="staff-one@example.com",
            password="password",
            tenant=self.tenant,
            role="shopkeeper",
        )

        self.other_admin = User.objects.create_user(
            username="admin-two",
            email="admin-two@example.com",
            password="password",
            tenant=self.other_tenant,
            role="admin",
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(
            user=user or self.admin
        )

    def create_notification(
        self,
        tenant=None,
        **overrides,
    ):
        payload = {
            "tenant": tenant or self.tenant,
            "title": "Test notification",
            "message": "Something happened.",
            "event_type": "TEST_EVENT",
            "level": Notification.Level.INFO,
        }
        payload.update(overrides)

        notification, _ = (
            NotificationService.create(
                **payload
            )
        )

        return notification

    def test_admin_only_access(self):
        self.create_notification()

        self.authenticate(self.shopkeeper)

        response = self.client.get(
            "/api/notifications/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_notifications_are_tenant_isolated(self):
        own = self.create_notification()

        self.create_notification(
            tenant=self.other_tenant,
            title="Other tenant",
        )

        self.authenticate()

        response = self.client.get(
            "/api/notifications/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["id"],
            own.id,
        )

    def test_single_notification_can_be_marked_read(self):
        notification = self.create_notification()

        self.authenticate()

        response = self.client.patch(
            f"/api/notifications/{notification.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read
        )
        self.assertIsNotNone(
            notification.read_at
        )

    def test_mark_all_read_only_updates_current_tenant(self):
        own_one = self.create_notification()
        own_two = self.create_notification(
            title="Second"
        )
        other = self.create_notification(
            tenant=self.other_tenant,
            title="Other",
        )

        self.authenticate()

        response = self.client.post(
            "/api/notifications/read-all/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["updated_count"],
            2,
        )

        own_one.refresh_from_db()
        own_two.refresh_from_db()
        other.refresh_from_db()

        self.assertTrue(own_one.is_read)
        self.assertTrue(own_two.is_read)
        self.assertFalse(other.is_read)

    def test_cleanup_deletes_only_read_notifications_older_than_7_days(self):
        old_read = self.create_notification(
            title="Old read"
        )
        recent_read = self.create_notification(
            title="Recent read"
        )
        unread = self.create_notification(
            title="Unread"
        )

        Notification.objects.filter(
            pk=old_read.pk
        ).update(
            is_read=True,
            read_at=timezone.now()
            - timedelta(days=8),
        )

        Notification.objects.filter(
            pk=recent_read.pk
        ).update(
            is_read=True,
            read_at=timezone.now()
            - timedelta(days=3),
        )

        NotificationService.cleanup_read_notifications(
            days=7
        )

        self.assertFalse(
            Notification.objects.filter(
                pk=old_read.pk
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                pk=recent_read.pk
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                pk=unread.pk
            ).exists()
        )

    def test_unread_dedupe_can_prevent_retry_spam(self):
        first, created_first = (
            NotificationService.create(
                tenant=self.tenant,
                title="Low stock",
                message="Only 4 remaining.",
                event_type="LOW_STOCK",
                dedupe_key="LOW_STOCK:PRODUCT:10",
                dedupe_unread=True,
            )
        )

        second, created_second = (
            NotificationService.create(
                tenant=self.tenant,
                title="Low stock",
                message="Only 4 remaining.",
                event_type="LOW_STOCK",
                dedupe_key="LOW_STOCK:PRODUCT:10",
                dedupe_unread=True,
            )
        )

        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(
            first.id,
            second.id,
        )
