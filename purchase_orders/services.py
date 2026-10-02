from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import PurchaseOrder, PurchaseOrderNumberSequence


class PurchaseOrderService:
    @staticmethod
    @transaction.atomic
    def finalize(order_id, tenant):
        order = PurchaseOrder.objects.select_for_update().filter(
            id=order_id, tenant=tenant
        ).first()
        if order is None:
            return None
        if order.status != PurchaseOrder.Status.DRAFT:
            raise ValidationError("Only draft purchase orders can be created.")
        if order.po_number is not None:
            raise ValidationError("This draft already has a purchase order number.")
        if not order.items.exists():
            raise ValidationError("A purchase order must contain at least one product.")
        sequence, _ = PurchaseOrderNumberSequence.objects.get_or_create(
            pk=1,
            defaults={"next_number": 1},
        )
        sequence = PurchaseOrderNumberSequence.objects.select_for_update().get(pk=sequence.pk)
        order.po_number = f"PO-{sequence.next_number:06d}"
        sequence.next_number += 1
        sequence.save(update_fields=["next_number"])
        order.status = PurchaseOrder.Status.CREATED
        order.finalized_at = timezone.now()
        order.save(update_fields=["po_number", "status", "finalized_at", "updated_at"])
        return order

    @staticmethod
    @transaction.atomic
    def discard(order_id, tenant):
        order = PurchaseOrder.objects.select_for_update().filter(
            id=order_id, tenant=tenant
        ).first()
        if order is None:
            return None
        if order.status != PurchaseOrder.Status.DRAFT or order.po_number is not None:
            raise ValidationError("Only an unnumbered draft can be discarded.")
        order.delete()
        return True