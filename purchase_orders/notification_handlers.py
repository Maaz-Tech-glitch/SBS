from django.db import transaction

from notifications.models import Notification
from notifications.services import NotificationService


class PurchaseOrderNotificationService:
    ACTION_URL = "/purchase-orders"

    @staticmethod
    def _schedule(callback):
        transaction.on_commit(
            callback,
            robust=True,
        )

    @staticmethod
    def _safe_order_data(order):
        if order is None:
            return {}

        supplier = getattr(order, "supplier", None)

        return {
            "purchase_order_id": getattr(order, "pk", None),
            "po_number": getattr(order, "po_number", None),
            "status": getattr(order, "status", ""),
            "supplier_id": getattr(order, "supplier_id", None),
            "supplier_name": getattr(supplier, "name", ""),
        }

    @classmethod
    def schedule_draft_created(
        cls,
        *,
        order,
        actor,
    ):
        tenant = order.tenant
        data = cls._safe_order_data(order)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Purchase Order Draft Created",
                message=(
                    f"Purchase order draft for "
                    f"{data.get('supplier_name') or 'supplier'} "
                    f"was created."
                ),
                event_type="PURCHASE_ORDER_DRAFT_CREATED",
                level=Notification.Level.INFO,
                entity_type="PURCHASE_ORDER",
                entity_id=order.pk,
                action_url=cls.ACTION_URL,
                metadata=data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_updated(
        cls,
        *,
        order,
        actor,
        changed_fields,
    ):
        fields = sorted(set(changed_fields or []))

        if not fields:
            return

        tenant = order.tenant
        data = cls._safe_order_data(order)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Purchase Order Updated",
                message="Purchase order draft was updated successfully.",
                event_type="PURCHASE_ORDER_UPDATED",
                level=Notification.Level.INFO,
                entity_type="PURCHASE_ORDER",
                entity_id=order.pk,
                action_url=cls.ACTION_URL,
                metadata={
                    **data,
                    "changed_fields": fields,
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_created_final(
        cls,
        *,
        order,
        actor,
    ):
        tenant = order.tenant
        data = cls._safe_order_data(order)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Purchase Order Created",
                message=(
                    f"{order.po_number} was created for "
                    f"{data.get('supplier_name') or 'supplier'}."
                ),
                event_type="PURCHASE_ORDER_CREATED",
                level=Notification.Level.SUCCESS,
                entity_type="PURCHASE_ORDER",
                entity_id=order.pk,
                action_url=cls.ACTION_URL,
                metadata=data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_finalized(
        cls,
        *,
        order,
        actor,
    ):
        tenant = order.tenant
        data = cls._safe_order_data(order)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Purchase Order Finalized",
                message=f"{order.po_number} was finalized successfully.",
                event_type="PURCHASE_ORDER_FINALIZED",
                level=Notification.Level.SUCCESS,
                entity_type="PURCHASE_ORDER",
                entity_id=order.pk,
                action_url=cls.ACTION_URL,
                metadata=data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_discarded(
        cls,
        *,
        tenant,
        actor,
        order_data,
    ):
        order_id = order_data.get("purchase_order_id", "")
        supplier_name = order_data.get("supplier_name", "")

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Purchase Order Draft Discarded",
                message=(
                    "Purchase order draft"
                    + (
                        f" for {supplier_name}"
                        if supplier_name
                        else ""
                    )
                    + " was discarded."
                ),
                event_type="PURCHASE_ORDER_DISCARDED",
                level=Notification.Level.WARNING,
                entity_type="PURCHASE_ORDER",
                entity_id=order_id,
                action_url=cls.ACTION_URL,
                metadata=order_data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_failure(
        cls,
        *,
        tenant,
        actor,
        operation,
        error,
        order=None,
    ):
        if tenant is None:
            return

        operation = str(operation or "PURCHASE_ORDER").upper()
        data = cls._safe_order_data(order)
        safe_error = str(error)[:300]

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Purchase Order Operation Failed",
                message=(
                    f"{operation.replace('_', ' ').title()} failed."
                ),
                event_type=f"PURCHASE_ORDER_{operation}_FAILED",
                level=Notification.Level.ERROR,
                entity_type="PURCHASE_ORDER",
                entity_id=data.get("purchase_order_id", ""),
                action_url=cls.ACTION_URL,
                metadata={
                    **data,
                    "error": safe_error,
                },
            )

        cls._schedule(create_notification)
