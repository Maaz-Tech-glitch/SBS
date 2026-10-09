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
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from accounting.services import AccountingIntegrationService
from products.notification_handlers import ProductNotificationService

from .repositories import (
    InvoiceRepository,
    InvoiceItemRepository,
    ProductStockRepository,
)
from .strategies import DiscountFactory
from .exceptions import (
    UnauthorizedInvoiceActionException,
    InvalidInvoiceStateException,
    InsufficientStockException,
    EmptyInvoiceException,
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
