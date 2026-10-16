# import os
# from decimal import Decimal
# from django.conf import settings
# from django.db import transaction
# from django.db.models import F
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
# from accounting.services import AccountingIntegrationService
# from .repositories import InvoiceRepository, InvoiceItemRepository, ProductStockRepository
# from .strategies import DiscountFactory
# from .exceptions import (
#     UnauthorizedInvoiceActionException,
#     InvalidInvoiceStateException,
#     InsufficientStockException,
#     EmptyInvoiceException,
# )


# class PricingService:
#     @staticmethod
#     def calculate_item_total(quantity, unit_price, discount, discount_type):
#         discount = discount or Decimal("0.00")
#         gross = quantity * unit_price
#         strategy = DiscountFactory.get(discount_type)
#         return strategy.apply(gross, discount)

#     @staticmethod
#     def format_discount(discount, discount_type):
#         return DiscountFactory.get(discount_type).display(discount)


# class InvoiceOwnershipService:
#     @staticmethod
#     def ensure_owner(invoice, user):
#         if invoice.tenant != user.tenant:
#             raise UnauthorizedInvoiceActionException()

#     @staticmethod
#     def ensure_pending(invoice):
#         if invoice.status != "PENDING":
#             raise InvalidInvoiceStateException()


# class InvoiceItemService:
#     @staticmethod
#     def upsert_item(invoice, product_id, quantity, discount, discount_type):
#         # [DATA ISOLATION FIX]: invoice.tenant pass kiya taake doosre tenant ka product access na ho
#         product = ProductStockRepository.get_locked_by_id(product_id, tenant=invoice.tenant)
#         item = InvoiceItemRepository.get_existing_locked(invoice, product)

#         if quantity == 0:
#             if item:
#                 item.delete()
#             return

#         if quantity > product.stock:
#             raise InsufficientStockException(f"Only {product.stock} item(s) available in stock.")

#         final_discount = discount if discount is not None else (item.discount if item else Decimal("0.00"))
#         final_discount_type = discount_type or (item.discount_type if item else "PERCENTAGE")
#         total_price = PricingService.calculate_item_total(quantity, product.price, final_discount, final_discount_type)

#         if item:
#             item.quantity = quantity
#             item.discount = final_discount
#             item.discount_type = final_discount_type
#             item.total_price = total_price
#             item.save()
#         else:
#             InvoiceItemRepository.create(
#                 invoice=invoice,
#                 product=product,
#                 quantity=quantity,
#                 cost_price=product.cost_price,  
#                 unit_price=product.price,      
#                 discount=final_discount,
#                 discount_type=final_discount_type,
#                 total_price=total_price,
#             )


# class InvoiceService:
#     @staticmethod
#     def get_or_create_draft(invoice_id, user):
#         if invoice_id:
#             invoice = InvoiceRepository.get_locked_by_id(invoice_id, tenant=user.tenant)
#             InvoiceOwnershipService.ensure_pending(invoice)
#             return invoice
#         return InvoiceRepository.create(tenant=user.tenant, shopkeeper=user)

#     @staticmethod
#     def list_pending(user):
#         return InvoiceRepository.list_by_tenant(user.tenant)

#     @staticmethod
#     def get_detail(invoice_id, tenant):
#         """Fixed: now accepts tenant parameter for data isolation"""
#         return InvoiceRepository.get_by_id(invoice_id, tenant)

#     @staticmethod
#     def add_item(*, invoice_id=None, customer_name=None, product_id=None, quantity=1,
#                 discount=None, discount_type=None, invoice_discount=None,
#                 invoice_discount_type=None, user):
#         with transaction.atomic():
#             invoice = InvoiceService.get_or_create_draft(invoice_id, user)

#             if customer_name is not None:
#                 invoice.customer_name = customer_name
#                 invoice.save(update_fields=["customer_name", "updated_at"])

#             if product_id is not None:
#                 InvoiceItemService.upsert_item(invoice, product_id, quantity, discount, discount_type)
#                 invoice.recalculate_totals()

#             if invoice_discount is not None:
#                 invoice.discount = invoice_discount
#                 invoice.discount_type = invoice_discount_type or invoice.discount_type or "PERCENTAGE"
#                 invoice.recalculate_totals()

#             # Fixed: now passing tenant parameter
#             return InvoiceService.get_detail(invoice.id, user.tenant)

#     @staticmethod
#     def complete_sale(invoice_id, payment_method, user):
#         with transaction.atomic():
#             invoice = InvoiceRepository.get_locked_by_id(invoice_id, tenant=user.tenant)
#             InvoiceOwnershipService.ensure_pending(invoice)
#             items = list(invoice.items.select_related("product"))
#             if not items:
#                 raise EmptyInvoiceException()

#             # Aggregate requested quantities per product
#             product_quantities = {}
#             for item in items:
#                 product_quantities[item.product_id] = product_quantities.get(item.product_id, 0) + item.quantity

#             # Lock products in ascending product_id order to eliminate counter deadlocks
#             locked_products = {}
#             for product_id in sorted(product_quantities.keys()):
#                 product = ProductStockRepository.get_locked_by_id(product_id, tenant=invoice.tenant)
#                 if product_quantities[product_id] > product.stock:
#                     raise InsufficientStockException(f"Insufficient stock for {product.name}.")
#                 locked_products[product_id] = product

#             # Atomic database subtraction using F()
#             for product_id, total_qty in product_quantities.items():
#                 product = locked_products[product_id]
#                 product.stock = F("stock") - total_qty
#                 product.save(update_fields=["stock"])
#                 product.refresh_from_db(fields=["stock"])

#             invoice.payment_method = payment_method
#             invoice.status = "COMPLETED"
#             invoice.save(update_fields=["payment_method", "status", "updated_at"])
#             AccountingIntegrationService.record_transaction(tenant=invoice.tenant, user=user, transaction_type="SALE", invoice=invoice)
#             return invoice

#     @staticmethod
#     def cancel(invoice_id, user):
#         with transaction.atomic():
#             invoice = InvoiceRepository.get_locked_by_id(invoice_id, tenant=user.tenant)
#             InvoiceOwnershipService.ensure_pending(invoice)
#             invoice.status = "CANCELLED"
#             invoice.save(update_fields=["status", "updated_at"])
#             return invoice


# class ReceiptService:
#     """PDF/Receipt generation — presentation concern, business logic se alag"""

#     @staticmethod
#     def generate_pdf(invoice):
#         tenant_folder = os.path.join(settings.MEDIA_ROOT, "invoices", f"tenant_{invoice.tenant_id}")
#         os.makedirs(tenant_folder, exist_ok=True)
#         file_name = f"{invoice.invoice_number}.pdf"
#         file_path = os.path.join(tenant_folder, file_name)
#         doc = SimpleDocTemplate(file_path)
#         styles = getSampleStyleSheet()
#         elements = [
#             Paragraph("SBS Shopkeeper Billing System", styles["Title"]),
#             Spacer(1, 12),
#             Paragraph(f"Invoice Number: {invoice.invoice_number}", styles["BodyText"]),
#             Paragraph(f"Customer: {invoice.customer_name or '-'}", styles["BodyText"]),
#             Paragraph(f"Status: {invoice.status}", styles["BodyText"]),
#             Paragraph(f"Payment Method: {invoice.payment_method}", styles["BodyText"]),
#             Paragraph(f"Final Amount: {invoice.final_amount}", styles["BodyText"]),
#             Spacer(1, 20),
#             Paragraph("Items", styles["Heading2"]),
#         ]
#         for item in invoice.items.all():
#             disc = PricingService.format_discount(item.discount, item.discount_type)
#             elements.append(Paragraph(
#                 f"{item.product.name} x {item.quantity} @ {item.unit_price} (Disc {disc}) = {item.total_price}",
#                 styles["BodyText"],
#             ))
#         doc.build(elements)
#         return file_name

#     @staticmethod
#     def generate_thermal_receipt(invoice):
#         bill_disc = PricingService.format_discount(invoice.discount, invoice.discount_type)
#         receipt = [
#             "SBS SHOPKEEPER SYSTEM", "-" * 48,
#             f"Invoice: {invoice.invoice_number}",
#             f"Customer: {invoice.customer_name or '-'}", "-" * 48,
#             f"{'Product':<14}{'Qty':>5}{'Price':>9}{'Disc':>8}{'Total':>12}", "-" * 48,
#         ]
#         for item in invoice.items.all():
#             disc = PricingService.format_discount(item.discount, item.discount_type)
#             receipt.append(
#                 f"{item.product.name[:14]:<14}{item.quantity:>5}{item.unit_price:>9}{disc:>8}{item.total_price:>12}"
#             )
#         receipt += [
#             "-" * 48,
#             f"{'Sub Total':<30}{invoice.total_amount:>18}",
#             f"{'Bill Discount (' + bill_disc + ')':<30}{'':>18}", "-" * 48,
#             f"{'Final Amount':<30}{invoice.final_amount:>18}", "-" * 48,
#             f"Payment: {invoice.payment_method or '-'}", "", "Thank You!",
#         ]
#         return "\n".join(receipt)

import os
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from accounting.services import AccountingIntegrationService
from products.notification_handlers import ProductNotificationService

from .repositories import (
    InvoiceRepository,
    InvoiceItemRepository,
    ProductStockRepository,
    SaleReturnRepository,
    SaleReturnItemRepository,
)
from .strategies import DiscountFactory
from .exceptions import (
    UnauthorizedInvoiceActionException,
    InvalidInvoiceStateException,
    InsufficientStockException,
    EmptyInvoiceException,
    ReturnNotAllowedException,
    InvalidReturnQuantityException,
    ReturnItemNotFoundException,
    ReturnRequestConflictException,
)


class PricingService:
    @staticmethod
    def calculate_item_total(
        quantity,
        unit_price,
        discount,
        discount_type,
    ):
        discount = discount or Decimal("0.00")
        gross = quantity * unit_price
        strategy = DiscountFactory.get(discount_type)
        return strategy.apply(gross, discount)

    @staticmethod
    def format_discount(discount, discount_type):
        return DiscountFactory.get(
            discount_type
        ).display(discount)


class InvoiceOwnershipService:
    @staticmethod
    def ensure_owner(invoice, user):
        if invoice.tenant != user.tenant:
            raise UnauthorizedInvoiceActionException()

    @staticmethod
    def ensure_pending(invoice):
        if invoice.status != "PENDING":
            raise InvalidInvoiceStateException()


class InvoiceItemService:
    @staticmethod
    def upsert_item(
        invoice,
        product_id,
        quantity,
        discount,
        discount_type,
    ):
        # Tenant is enforced when retrieving the product.
        product = ProductStockRepository.get_locked_by_id(
            product_id,
            tenant=invoice.tenant,
        )

        item = InvoiceItemRepository.get_existing_locked(
            invoice,
            product,
        )

        if quantity == 0:
            if item:
                item.delete()
            return

        if quantity > product.stock:
            raise InsufficientStockException(
                f"Only {product.stock} item(s) available in stock."
            )

        final_discount = (
            discount
            if discount is not None
            else (
                item.discount
                if item
                else Decimal("0.00")
            )
        )

        final_discount_type = (
            discount_type
            or (
                item.discount_type
                if item
                else "PERCENTAGE"
            )
        )

        total_price = PricingService.calculate_item_total(
            quantity,
            product.price,
            final_discount,
            final_discount_type,
        )

        if item:
            item.quantity = quantity
            item.discount = final_discount
            item.discount_type = final_discount_type
            item.total_price = total_price
            item.save()
        else:
            InvoiceItemRepository.create(
                invoice=invoice,
                product=product,
                quantity=quantity,
                cost_price=product.cost_price,
                unit_price=product.price,
                discount=final_discount,
                discount_type=final_discount_type,
                total_price=total_price,
            )


class InvoiceService:
    @staticmethod
    def get_or_create_draft(invoice_id, user):
        if invoice_id:
            invoice = InvoiceRepository.get_locked_by_id(
                invoice_id,
                tenant=user.tenant,
            )
            InvoiceOwnershipService.ensure_pending(
                invoice
            )
            return invoice

        return InvoiceRepository.create(
            tenant=user.tenant,
            shopkeeper=user,
        )

    @staticmethod
    def list_pending(user):
        return InvoiceRepository.list_by_tenant(
            user.tenant
        )

    @staticmethod
    def get_detail(invoice_id, tenant):
        return InvoiceRepository.get_by_id(
            invoice_id,
            tenant,
        )

    @staticmethod
    def add_item(
        *,
        invoice_id=None,
        customer_name=None,
        product_id=None,
        quantity=1,
        discount=None,
        discount_type=None,
        invoice_discount=None,
        invoice_discount_type=None,
        user,
    ):
        with transaction.atomic():
            invoice = InvoiceService.get_or_create_draft(
                invoice_id,
                user,
            )

            if customer_name is not None:
                invoice.customer_name = customer_name
                invoice.save(
                    update_fields=[
                        "customer_name",
                        "updated_at",
                    ]
                )

            if product_id is not None:
                InvoiceItemService.upsert_item(
                    invoice,
                    product_id,
                    quantity,
                    discount,
                    discount_type,
                )
                invoice.recalculate_totals()

            if invoice_discount is not None:
                invoice.discount = invoice_discount
                invoice.discount_type = (
                    invoice_discount_type
                    or invoice.discount_type
                    or "PERCENTAGE"
                )
                invoice.recalculate_totals()

            return InvoiceService.get_detail(
                invoice.id,
                user.tenant,
            )

    @staticmethod
    def complete_sale(
        invoice_id,
        payment_method,
        user,
    ):
        with transaction.atomic():
            invoice = InvoiceRepository.get_locked_by_id(
                invoice_id,
                tenant=user.tenant,
            )

            InvoiceOwnershipService.ensure_pending(
                invoice
            )

            items = list(
                invoice.items.select_related(
                    "product"
                )
            )

            if not items:
                raise EmptyInvoiceException()

            locked_products = {}

            for item in items:
                product = (
                    ProductStockRepository
                    .get_locked_by_id(
                        item.product_id,
                        tenant=invoice.tenant,
                    )
                )

                locked_products[
                    item.product_id
                ] = product

                if item.quantity > product.stock:
                    raise InsufficientStockException(
                        f"Insufficient stock for {product.name}."
                    )

            for item in items:
                product = locked_products[
                    item.product_id
                ]

                old_stock = product.stock
                new_stock = (
                    old_stock - item.quantity
                )

                product.stock = new_stock
                product.save(
                    update_fields=["stock"]
                )

                # No normal-sale notification is created.
                # Only threshold transitions create an admin notification.
                # This callback runs only if the entire sale transaction,
                # including accounting, commits successfully.
                ProductNotificationService.schedule_stock_transition(
                    product=product,
                    old_stock=old_stock,
                    new_stock=new_stock,
                    actor=user,
                    source="SALE",
                )

            invoice.payment_method = payment_method
            invoice.status = "COMPLETED"
            invoice.save(
                update_fields=[
                    "payment_method",
                    "status",
                    "updated_at",
                ]
            )

            AccountingIntegrationService.record_transaction(
                tenant=invoice.tenant,
                user=user,
                transaction_type="SALE",
                invoice=invoice,
            )

            return invoice

    @staticmethod
    def cancel(invoice_id, user):
        with transaction.atomic():
            invoice = InvoiceRepository.get_locked_by_id(
                invoice_id,
                tenant=user.tenant,
            )

            InvoiceOwnershipService.ensure_pending(
                invoice
            )

            invoice.status = "CANCELLED"
            invoice.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return invoice


class ReceiptService:
    """PDF/receipt presentation logic."""

    @staticmethod
    def generate_pdf(invoice):
        tenant_folder = os.path.join(
            settings.MEDIA_ROOT,
            "invoices",
            f"tenant_{invoice.tenant_id}",
        )

        os.makedirs(
            tenant_folder,
            exist_ok=True,
        )

        file_name = (
            f"{invoice.invoice_number}.pdf"
        )
        file_path = os.path.join(
            tenant_folder,
            file_name,
        )

        doc = SimpleDocTemplate(file_path)
        styles = getSampleStyleSheet()

        elements = [
            Paragraph(
                "SBS Shopkeeper Billing System",
                styles["Title"],
            ),
            Spacer(1, 12),
            Paragraph(
                f"Invoice Number: {invoice.invoice_number}",
                styles["BodyText"],
            ),
            Paragraph(
                f"Customer: {invoice.customer_name or '-'}",
                styles["BodyText"],
            ),
            Paragraph(
                f"Status: {invoice.status}",
                styles["BodyText"],
            ),
            Paragraph(
                f"Payment Method: {invoice.payment_method}",
                styles["BodyText"],
            ),
            Paragraph(
                f"Final Amount: {invoice.final_amount}",
                styles["BodyText"],
            ),
            Spacer(1, 20),
            Paragraph(
                "Items",
                styles["Heading2"],
            ),
        ]

        for item in invoice.items.all():
            disc = PricingService.format_discount(
                item.discount,
                item.discount_type,
            )

            elements.append(
                Paragraph(
                    (
                        f"{item.product.name} x {item.quantity} "
                        f"@ {item.unit_price} "
                        f"(Disc {disc}) = {item.total_price}"
                    ),
                    styles["BodyText"],
                )
            )

        doc.build(elements)
        return file_name

    @staticmethod
    def generate_thermal_receipt(invoice):
        bill_disc = PricingService.format_discount(
            invoice.discount,
            invoice.discount_type,
        )

        receipt = [
            "SBS SHOPKEEPER SYSTEM",
            "-" * 48,
            f"Invoice: {invoice.invoice_number}",
            f"Customer: {invoice.customer_name or '-'}",
            "-" * 48,
            (
                f"{'Product':<14}"
                f"{'Qty':>5}"
                f"{'Price':>9}"
                f"{'Disc':>8}"
                f"{'Total':>12}"
            ),
            "-" * 48,
        ]

        for item in invoice.items.all():
            disc = PricingService.format_discount(
                item.discount,
                item.discount_type,
            )

            receipt.append(
                (
                    f"{item.product.name[:14]:<14}"
                    f"{item.quantity:>5}"
                    f"{item.unit_price:>9}"
                    f"{disc:>8}"
                    f"{item.total_price:>12}"
                )
            )

        receipt += [
            "-" * 48,
            f"{'Sub Total':<30}{invoice.total_amount:>18}",
            (
                f"{'Bill Discount (' + bill_disc + ')':<30}"
                f"{'':>18}"
            ),
            "-" * 48,
            f"{'Final Amount':<30}{invoice.final_amount:>18}",
            "-" * 48,
            f"Payment: {invoice.payment_method or '-'}",
            "",
            "Thank You!",
        ]

        return "\n".join(receipt)

class ReturnService:
    MONEY_QUANT = Decimal("0.01")
    UNIT_QUANT = Decimal("0.0001")

    @staticmethod
    def _ensure_completed(invoice):
        if invoice.status != "COMPLETED":
            raise ReturnNotAllowedException(
                "Only COMPLETED invoices can be returned."
            )

    @classmethod
    def _allocate_invoice_net_totals(cls, invoice, invoice_items):
        """
        Allocate the invoice-level discount across items proportionally.

        InvoiceItem.total_price already includes item-level discount.
        Invoice.final_amount additionally includes invoice-level discount.
        The final item absorbs any one-cent rounding remainder so returning all
        products always totals exactly invoice.final_amount.
        """
        items = list(invoice_items)

        if not items:
            return {}

        total_amount = Decimal(invoice.total_amount or 0)
        final_amount = Decimal(invoice.final_amount or 0)

        if total_amount <= 0 or final_amount <= 0:
            return {item.id: Decimal("0.00") for item in items}

        allocations = {}
        remaining = final_amount.quantize(
            cls.MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )

        for index, item in enumerate(items):
            if index == len(items) - 1:
                allocated = remaining
            else:
                allocated = (
                    final_amount
                    * Decimal(item.total_price)
                    / total_amount
                ).quantize(
                    cls.MONEY_QUANT,
                    rounding=ROUND_HALF_UP,
                )
                allocated = max(
                    Decimal("0.00"),
                    min(allocated, remaining),
                )

            allocations[item.id] = allocated
            remaining -= allocated

        return allocations

    @staticmethod
    def _returned_totals(invoice_item_ids):
        if not invoice_item_ids:
            return {}

        from .models import SaleReturnItem

        rows = (
            SaleReturnItem.objects
            .filter(invoice_item_id__in=invoice_item_ids)
            .values("invoice_item_id")
            .annotate(
                returned_quantity=Sum("quantity"),
                refunded_amount=Sum("refund_amount"),
            )
        )

        return {
            row["invoice_item_id"]: {
                "quantity": int(row["returned_quantity"] or 0),
                "amount": Decimal(row["refunded_amount"] or 0),
            }
            for row in rows
        }

    @classmethod
    def get_snapshot(cls, invoice_id, user):
        invoice = InvoiceRepository.get_by_id(
            invoice_id,
            tenant=user.tenant,
        )
        cls._ensure_completed(invoice)

        invoice_items = list(
            invoice.items
            .select_related("product")
            .order_by("id")
        )

        allocations = cls._allocate_invoice_net_totals(
            invoice,
            invoice_items,
        )
        returned = cls._returned_totals(
            [item.id for item in invoice_items]
        )

        item_rows = []
        total_sold_quantity = 0
        total_returned_quantity = 0

        for item in invoice_items:
            state = returned.get(
                item.id,
                {"quantity": 0, "amount": Decimal("0.00")},
            )
            already_returned = state["quantity"]
            available = max(
                int(item.quantity) - already_returned,
                0,
            )
            allocated_total = allocations.get(
                item.id,
                Decimal("0.00"),
            )
            remaining_refund = max(
                allocated_total - state["amount"],
                Decimal("0.00"),
            )

            if available > 0:
                effective_unit = (
                    remaining_refund / Decimal(available)
                ).quantize(
                    cls.UNIT_QUANT,
                    rounding=ROUND_HALF_UP,
                )
            else:
                effective_unit = Decimal("0.0000")

            total_sold_quantity += int(item.quantity)
            total_returned_quantity += already_returned

            item_rows.append({
                "invoice_item_id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "sold_quantity": int(item.quantity),
                "already_returned_quantity": already_returned,
                "returnable_quantity": available,
                "original_unit_price": item.unit_price,
                "original_item_total": item.total_price,
                "refund_unit_price": effective_unit,
                "remaining_refundable_amount": remaining_refund,
            })

        if total_returned_quantity == 0:
            return_status = "NONE"
        elif (
            total_sold_quantity > 0
            and total_returned_quantity >= total_sold_quantity
        ):
            return_status = "FULL"
        else:
            return_status = "PARTIAL"

        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_status": invoice.status,
            "payment_method": invoice.payment_method,
            "original_total": invoice.total_amount,
            "original_final_amount": invoice.final_amount,
            "return_status": return_status,
            "items": item_rows,
            "returns": list(
                SaleReturnRepository.list_by_invoice(invoice)
            ),
        }

    @classmethod
    def create_return(
        cls,
        *,
        invoice_id,
        request_id,
        items,
        reason,
        user,
    ):
        """
        Atomic + idempotent return processing.

        Lock order:
          1. invoice
          2. all invoice items
          3. affected products sorted by product_id

        The invoice lock serializes concurrent returns for the same invoice,
        preventing two requests from returning the same sold quantity twice.
        """
        with transaction.atomic():
            invoice = InvoiceRepository.get_locked_by_id(
                invoice_id,
                tenant=user.tenant,
            )
            cls._ensure_completed(invoice)

            # Double-click / network retry safety.
            existing = SaleReturnRepository.get_by_request_id(
                user.tenant,
                request_id,
            )
            if existing:
                if existing.invoice_id != invoice.id:
                    raise ReturnRequestConflictException()
                return existing, False

            invoice_items = list(
                InvoiceItemRepository.list_locked_for_invoice(
                    invoice
                )
            )

            if not invoice_items:
                raise ReturnItemNotFoundException(
                    "This invoice has no returnable items."
                )

            invoice_item_map = {
                item.id: item
                for item in invoice_items
            }

            requested_item_ids = [
                int(item["invoice_item_id"])
                for item in items
            ]

            if len(requested_item_ids) != len(set(requested_item_ids)):
                raise ReturnItemNotFoundException(
                    "The same invoice item cannot be returned twice in one request."
                )

            missing_ids = [
                item_id
                for item_id in requested_item_ids
                if item_id not in invoice_item_map
            ]

            if missing_ids:
                raise ReturnItemNotFoundException(
                    "One or more selected items do not belong to this invoice."
                )

            allocations = cls._allocate_invoice_net_totals(
                invoice,
                invoice_items,
            )
            returned = cls._returned_totals(
                [item.id for item in invoice_items]
            )

            # Validate every quantity before changing stock or creating rows.
            prepared = []

            for requested in items:
                item = invoice_item_map[
                    int(requested["invoice_item_id"])
                ]
                return_quantity = int(requested["quantity"])

                state = returned.get(
                    item.id,
                    {"quantity": 0, "amount": Decimal("0.00")},
                )
                already_returned = state["quantity"]
                available_quantity = (
                    int(item.quantity) - already_returned
                )

                if (
                    return_quantity <= 0
                    or return_quantity > available_quantity
                ):
                    raise InvalidReturnQuantityException(
                        (
                            f"{item.product.name}: sold {item.quantity}, "
                            f"already returned {already_returned}, "
                            f"available to return {max(available_quantity, 0)}."
                        )
                    )

                allocated_total = allocations.get(
                    item.id,
                    Decimal("0.00"),
                )
                remaining_refund = max(
                    allocated_total - state["amount"],
                    Decimal("0.00"),
                )

                # If this return finishes the item, refund the exact remainder
                # so repeated partial returns never create a rounding mismatch.
                if return_quantity == available_quantity:
                    refund_amount = remaining_refund
                elif available_quantity > 0:
                    refund_amount = (
                        remaining_refund
                        * Decimal(return_quantity)
                        / Decimal(available_quantity)
                    ).quantize(
                        cls.MONEY_QUANT,
                        rounding=ROUND_HALF_UP,
                    )
                else:
                    refund_amount = Decimal("0.00")

                refund_amount = refund_amount.quantize(
                    cls.MONEY_QUANT,
                    rounding=ROUND_HALF_UP,
                )

                refund_unit_price = (
                    (
                        refund_amount / Decimal(return_quantity)
                    ).quantize(
                        cls.UNIT_QUANT,
                        rounding=ROUND_HALF_UP,
                    )
                    if return_quantity
                    else Decimal("0.0000")
                )

                prepared.append({
                    "invoice_item": item,
                    "quantity": return_quantity,
                    "refund_amount": refund_amount,
                    "refund_unit_price": refund_unit_price,
                })

            # Lock all affected products in stable order to reduce deadlock risk.
            locked_products = {}
            for product_id in sorted({
                row["invoice_item"].product_id
                for row in prepared
            }):
                locked_products[product_id] = (
                    ProductStockRepository.get_locked_by_id(
                        product_id,
                        tenant=invoice.tenant,
                    )
                )

            sale_return = SaleReturnRepository.create(
                tenant=invoice.tenant,
                invoice=invoice,
                request_id=request_id,
                created_by=user,
                refund_method=invoice.payment_method,
                reason=reason or "",
            )

            total_refund = Decimal("0.00")

            for row in prepared:
                invoice_item = row["invoice_item"]
                product = locked_products[
                    invoice_item.product_id
                ]

                product.stock = (
                    int(product.stock)
                    + int(row["quantity"])
                )
                product.save(
                    update_fields=["stock", "updated_at"]
                )

                SaleReturnItemRepository.create(
                    sale_return=sale_return,
                    invoice_item=invoice_item,
                    quantity=row["quantity"],
                    refund_unit_price=row["refund_unit_price"],
                    refund_amount=row["refund_amount"],
                )

                total_refund += row["refund_amount"]

            total_refund = total_refund.quantize(
                cls.MONEY_QUANT,
                rounding=ROUND_HALF_UP,
            )
            sale_return.total_refund = total_refund
            sale_return.save(
                update_fields=["total_refund"]
            )

            # The refund is sent back through the original payment method.
            # If accounting fails, this outer atomic block rolls back the
            # return rows AND all stock restoration.
            if total_refund > 0:
                AccountingIntegrationService.record_transaction(
                    tenant=invoice.tenant,
                    user=user,
                    transaction_type="SALE_RETURN",
                    invoice=invoice,
                    amount=total_refund,
                    payment_method=invoice.payment_method,
                    return_number=sale_return.return_number,
                    description=(
                        f"Sale Return {sale_return.return_number} "
                        f"for Invoice {invoice.invoice_number}"
                    ),
                )

            return (
                SaleReturnRepository.get_detailed(
                    sale_return.id,
                    invoice.tenant,
                ),
                True,
            )

