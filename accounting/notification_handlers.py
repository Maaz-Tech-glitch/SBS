from django.db import transaction

from notifications.models import Notification
from notifications.services import NotificationService


class AccountingNotificationService:
    ACTION_URL = "/accounting"

    @staticmethod
    def _schedule(callback):
        transaction.on_commit(
            callback,
            robust=True,
        )

    @staticmethod
    def _create_now(**kwargs):
        """
        Failure notifications are intentionally created immediately.

        Call this only after the failed business/accounting transaction has
        already unwound back to the view/caller. Any notification-system error
        is swallowed so it cannot replace the original business error.
        """
        try:
            NotificationService.create(**kwargs)
        except Exception:
            return None

    @staticmethod
    def _safe_entry_data(entry):
        if entry is None:
            return {}

        return {
            "journal_entry_id": getattr(entry, "pk", None),
            "reference": getattr(entry, "reference", ""),
            "status": getattr(entry, "status", ""),
            "date": (
                str(entry.date)
                if getattr(entry, "date", None)
                else None
            ),
            "description": getattr(entry, "description", ""),
        }

    @classmethod
    def schedule_journal_created(
        cls,
        *,
        entry,
        actor,
        line_count,
        auto_post,
    ):
        tenant = entry.tenant
        data = cls._safe_entry_data(entry)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Journal Entry Created",
                message=(
                    f"{entry.reference} was created"
                    + (
                        " and posted."
                        if auto_post
                        else " as draft."
                    )
                ),
                event_type="JOURNAL_ENTRY_CREATED",
                level=Notification.Level.SUCCESS,
                entity_type="JOURNAL_ENTRY",
                entity_id=entry.pk,
                action_url=cls.ACTION_URL,
                metadata={
                    **data,
                    "line_count": int(line_count),
                    "auto_post": bool(auto_post),
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_journal_posted(
        cls,
        *,
        entry,
        actor,
    ):
        tenant = entry.tenant
        data = cls._safe_entry_data(entry)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Journal Entry Posted",
                message=f"{entry.reference} was posted successfully.",
                event_type="JOURNAL_ENTRY_POSTED",
                level=Notification.Level.SUCCESS,
                entity_type="JOURNAL_ENTRY",
                entity_id=entry.pk,
                action_url=cls.ACTION_URL,
                metadata=data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_journal_voided(
        cls,
        *,
        entry,
        actor,
    ):
        tenant = entry.tenant
        data = cls._safe_entry_data(entry)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Journal Entry Voided",
                message=f"{entry.reference} was voided.",
                event_type="JOURNAL_ENTRY_VOIDED",
                level=Notification.Level.WARNING,
                entity_type="JOURNAL_ENTRY",
                entity_id=entry.pk,
                action_url=cls.ACTION_URL,
                metadata=data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_manual_transaction_recorded(
        cls,
        *,
        entry,
        actor,
        transaction_type,
        amount,
        payment_method,
    ):
        tenant = entry.tenant
        data = cls._safe_entry_data(entry)
        transaction_type = str(transaction_type or "").upper()

        if transaction_type == "SUPPLIER_PAYMENT":
            title = "Supplier Payment Recorded"
            event_type = "SUPPLIER_PAYMENT_RECORDED"
            message = (
                entry.description
                or "Supplier payment was recorded successfully."
            )
        else:
            title = "Accounting Transaction Recorded"
            event_type = "ACCOUNTING_TRANSACTION_RECORDED"
            message = (
                entry.description
                or f"{transaction_type.replace('_', ' ').title()} recorded."
            )

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title=title,
                message=message,
                event_type=event_type,
                level=Notification.Level.SUCCESS,
                entity_type="JOURNAL_ENTRY",
                entity_id=entry.pk,
                action_url=cls.ACTION_URL,
                metadata={
                    **data,
                    "transaction_type": transaction_type,
                    "amount": str(amount),
                    "payment_method": str(payment_method or ""),
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def journal_failure(
        cls,
        *,
        tenant,
        actor,
        operation,
        error,
        entry_id=None,
    ):
        operation = str(operation or "JOURNAL").upper()
        safe_error = str(error)[:300]

        cls._create_now(
            tenant=tenant,
            actor=actor,
            title="Journal Entry Operation Failed",
            message=(
                f"{operation.replace('_', ' ').title()} failed."
            ),
            event_type=f"JOURNAL_ENTRY_{operation}_FAILED",
            level=Notification.Level.ERROR,
            entity_type="JOURNAL_ENTRY",
            entity_id=entry_id or "",
            action_url=cls.ACTION_URL,
            metadata={
                "operation": operation,
                "error": safe_error,
            },
        )

    @classmethod
    def manual_transaction_failure(
        cls,
        *,
        tenant,
        actor,
        transaction_type,
        error,
        amount=None,
        payment_method=None,
    ):
        transaction_type = str(
            transaction_type or "ACCOUNTING"
        ).upper()

        safe_error = str(error)[:300]

        event_type = (
            "SUPPLIER_PAYMENT_FAILED"
            if transaction_type == "SUPPLIER_PAYMENT"
            else "ACCOUNTING_TRANSACTION_FAILED"
        )

        title = (
            "Supplier Payment Failed"
            if transaction_type == "SUPPLIER_PAYMENT"
            else "Accounting Transaction Failed"
        )

        cls._create_now(
            tenant=tenant,
            actor=actor,
            title=title,
            message=(
                f"{transaction_type.replace('_', ' ').title()} "
                f"could not be recorded."
            ),
            event_type=event_type,
            level=Notification.Level.ERROR,
            entity_type="ACCOUNTING",
            action_url=cls.ACTION_URL,
            metadata={
                "transaction_type": transaction_type,
                "amount": (
                    str(amount)
                    if amount is not None
                    else None
                ),
                "payment_method": str(payment_method or ""),
                "error": safe_error,
            },
        )

    @classmethod
    def sync_failure(
        cls,
        *,
        tenant,
        actor,
        source,
        error,
        entity_type="",
        entity_id="",
    ):
        """
        Used by POS/Product caller boundaries after their outer transaction
        has rolled back. This makes inventory/sale vs accounting mismatch
        failures visible to the tenant admin.
        """
        source = str(source or "ACCOUNTING_SYNC").upper()
        safe_error = str(error)[:300]

        cls._create_now(
            tenant=tenant,
            actor=actor,
            title="Accounting Sync Failed",
            message=(
                f"{source.replace('_', ' ').title()} "
                f"could not be synced with accounting."
            ),
            event_type="ACCOUNTING_SYNC_FAILED",
            level=Notification.Level.CRITICAL,
            entity_type=entity_type or "ACCOUNTING",
            entity_id=entity_id or "",
            action_url=cls.ACTION_URL,
            metadata={
                "source": source,
                "error": safe_error,
            },
        )
