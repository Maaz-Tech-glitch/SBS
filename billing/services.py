import os
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from products.models import Product
from .models import Invoice, InvoiceItem


def calculate_item_total(quantity, unit_price, discount, discount_type):
    discount = discount or Decimal("0.00")
    if discount < 0:
        discount = Decimal("0.00")
    gross = quantity * unit_price
    if discount_type == "PERCENTAGE":
        if discount > 100:
            discount = Decimal("100")
        discount_amount = (gross * discount) / Decimal("100")
    else:
        discount_amount = discount
    if discount_amount > gross:
        discount_amount = gross
    return gross - discount_amount


def update_invoice_totals(invoice):
    total = Decimal("0.00")
    for item in invoice.items.all():
        total += item.total_price
    invoice.total_amount = total
    discount = invoice.discount or Decimal("0.00")
    if discount < 0:
        discount = Decimal("0.00")
    final_amount = total
    if invoice.discount_type == "FIXED":
        if discount > total:
            discount = total
        final_amount = total - discount
    elif invoice.discount_type == "PERCENTAGE":
        if discount > 100:
            discount = Decimal("100")
        discount_amount = (total * discount) / Decimal("100")
        final_amount = total - discount_amount

    invoice.discount = discount
    invoice.final_amount = final_amount
    invoice.save(update_fields=["total_amount", "discount", "final_amount", "updated_at"])
    return invoice


def get_invoice_detail(invoice_id):
    return Invoice.objects.get(id=invoice_id)   # DoesNotExist -> global handler


def _get_or_create_draft(invoice_id, shopkeeper):
    if invoice_id:
        invoice = Invoice.objects.select_for_update().get(id=invoice_id)   # DoesNotExist -> global handler
        if invoice.shopkeeper != shopkeeper:
            raise ValueError("You cannot modify this invoice.")
        if invoice.status != "PENDING":
            raise ValueError("Only pending (draft) invoices can be modified.")
        return invoice
    return Invoice.objects.create(shopkeeper=shopkeeper)


def list_pending_invoices(shopkeeper):
    return Invoice.objects.filter(shopkeeper=shopkeeper).order_by("-created_at")


def AddItem(
    *,
    invoice_id=None,
    customer_name=None,
    product_id=None,
    quantity=1,
    discount=None,
    discount_type=None,
    invoice_discount=None,
    invoice_discount_type=None,
    shopkeeper,
):
    with transaction.atomic():
        invoice = _get_or_create_draft(invoice_id, shopkeeper)

        if customer_name is not None:
            invoice.customer_name = customer_name
            invoice.save(update_fields=["customer_name", "updated_at"])

        if product_id is not None:
            product = Product.objects.select_for_update().get(id=product_id)   # DoesNotExist -> global handler

            item = (
                InvoiceItem.objects
                .select_for_update()
                .filter(invoice=invoice, product=product)
                .first()
            )

            if quantity == 0:
                if item:
                    item.delete()

            else:
                if quantity > product.stock:
                    raise ValueError(f"Only {product.stock} item(s) available in stock.")
                final_discount = discount if discount is not None else (
                    item.discount if item else Decimal("0.00")
                )
                final_discount_type = discount_type or (
                    item.discount_type if item else "PERCENTAGE"
                )
                total_price = calculate_item_total(
                    quantity, product.price, final_discount, final_discount_type
                )

                if item:
                    item.quantity = quantity
                    item.discount = final_discount
                    item.discount_type = final_discount_type
                    item.total_price = total_price
                    item.save()
                else:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product=product,
                        quantity=quantity,
                        unit_price=product.price,
                        discount=final_discount,
                        discount_type=final_discount_type,
                        total_price=total_price,
                    )

            update_invoice_totals(invoice)

        if invoice_discount is not None:
            invoice.discount = invoice_discount
            invoice.discount_type = invoice_discount_type or invoice.discount_type or "PERCENTAGE"
            update_invoice_totals(invoice)

        return get_invoice_detail(invoice.id)


def complete_sale(invoice_id, payment_method, user):
    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(id=invoice_id)   # DoesNotExist -> global handler

        if invoice.shopkeeper != user:
            raise ValueError("You cannot complete this invoice.")
        if invoice.status != "PENDING":
            raise ValueError("Only pending invoices can be completed.")
        items = list(invoice.items.select_related("product"))
        if not items:
            raise ValueError("Invoice must contain at least one item.")
        locked_products = {}
        for item in items:
            product = Product.objects.select_for_update().get(id=item.product_id)
            locked_products[item.product_id] = product
            if item.quantity > product.stock:
                raise ValueError(f"Insufficient stock for {product.name}.")
        for item in items:
            product = locked_products[item.product_id]
            product.stock -= item.quantity
            product.save(update_fields=["stock"])
        invoice.payment_method = payment_method
        invoice.status = "COMPLETED"
        invoice.save(update_fields=["payment_method", "status", "updated_at"])
        return invoice


def cancel_invoice(invoice_id, user):
    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(id=invoice_id)   # DoesNotExist -> global handler
        if invoice.shopkeeper != user:
            raise ValueError("You cannot cancel this invoice.")
        if invoice.status != "PENDING":
            raise ValueError("Only pending invoices can be cancelled.")
        invoice.status = "CANCELLED"
        invoice.save(update_fields=["status", "updated_at"])
        return invoice


def generate_invoice_pdf(invoice):
    file_name = f"invoice_{invoice.id}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("SBS Shopkeeper Billing System", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Invoice Number: {invoice.invoice_number}", styles["BodyText"]),
        Paragraph(f"Customer: {invoice.customer_name or '-'}", styles["BodyText"]),
        Paragraph(f"Status: {invoice.status}", styles["BodyText"]),
        Paragraph(f"Payment Method: {invoice.payment_method}", styles["BodyText"]),
        Paragraph(f"Final Amount: {invoice.final_amount}", styles["BodyText"]),
        Spacer(1, 20),
        Paragraph("Items", styles["Heading2"]),
    ]
    for item in invoice.items.all():
        disc = f"{item.discount}%" if item.discount_type == "PERCENTAGE" else f"Rs. {item.discount}"
        elements.append(
            Paragraph(
                f"{item.product.name} x {item.quantity} @ {item.unit_price} "
                f"(Disc {disc}) = {item.total_price}",
                styles["BodyText"],
            )
        )
    doc.build(elements)
    return file_name


def generate_thermal_receipt(invoice):
    bill_disc = (f"{invoice.discount}%" if invoice.discount_type == "PERCENTAGE" else f"Rs. {invoice.discount}")
    receipt = [
        "SBS SHOPKEEPER SYSTEM",
        "-" * 48,
        f"Invoice: {invoice.invoice_number}",
        f"Customer: {invoice.customer_name or '-'}",
        "-" * 48,
        f"{'Product':<14}{'Qty':>5}{'Price':>9}{'Disc':>8}{'Total':>12}",
        "-" * 48,
    ]
    for item in invoice.items.all():
        disc = f"{item.discount}%" if item.discount_type == "PERCENTAGE" else f"{item.discount}"
        receipt.append(
            f"{item.product.name[:14]:<14}{item.quantity:>5}{item.unit_price:>9}{disc:>8}{item.total_price:>12}"
        )
    receipt += [
        "-" * 48,
        f"{'Sub Total':<30}{invoice.total_amount:>18}",
        f"{'Bill Discount (' + bill_disc + ')':<30}{'':>18}",
        "-" * 48,
        f"{'Final Amount':<30}{invoice.final_amount:>18}",
        "-" * 48,
        f"Payment: {invoice.payment_method or '-'}",
        "",
        "Thank You!",
    ]
    return "\n".join(receipt)