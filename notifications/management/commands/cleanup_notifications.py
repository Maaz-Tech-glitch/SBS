from django.core.management.base import BaseCommand

from notifications.services import NotificationService


class Command(BaseCommand):
    help = (
        "Delete read notifications whose read_at is older than 7 days."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
        )

    def handle(self, *args, **options):
        days = max(
            1,
            options["days"],
        )

        deleted = (
            NotificationService
            .cleanup_read_notifications(
                days=days
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted} old read notification record(s)."
            )
        )
