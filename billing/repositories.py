from products.models import Product
from products.exceptions import ProductNotFoundException
from .models import Invoice, InvoiceItem, SaleReturn, SaleReturnItem
from .exceptions import InvoiceNotFoundException, SaleReturnException


class InvoiceRepository:
    @staticmethod
    def get_by_id(invoice_id, tenant):
        try:
            return Invoice.objects.get(id=invoice_id, tenant=tenant)
        except Invoice.DoesNotExist:
            raise InvoiceNotFoundException()

    @staticmethod
    def get_locked_by_id(invoice_id, tenant):
        try:
            return Invoice.objects.select_for_update().get(id=invoice_id, tenant=tenant)
        except Invoice.DoesNotExist:
            raise InvoiceNotFoundException()

    @staticmethod
    def create(tenant, shopkeeper):
        return Invoice.objects.create(tenant=tenant, shopkeeper=shopkeeper)

    @staticmethod
    def list_by_tenant(tenant):
        return Invoice.objects.filter(tenant=tenant).order_by("-created_at")

    @staticmethod
    def get_completed_in_range(tenant, start_date, end_date):
        return Invoice.objects.filter(
            tenant=tenant, status="COMPLETED",
            created_at__date__gte=start_date, created_at__date__lte=end_date,
        )


class InvoiceItemRepository:
    @staticmethod
    def get_existing_locked(invoice, product):
        return (
            InvoiceItem.objects
            .select_for_update()
            .filter(invoice=invoice, product=product)
            .first()
        )

    @staticmethod
    def list_locked_for_invoice(invoice):
        return (
            InvoiceItem.objects
            .select_for_update()
            .filter(invoice=invoice)
            .select_related("product")
            .order_by("id")
        )

    @staticmethod
    def create(invoice, product, quantity, unit_price, discount, discount_type, total_price, cost_price=0):
        return InvoiceItem.objects.create(
            invoice=invoice, product=product, quantity=quantity,
            cost_price=cost_price,
            unit_price=unit_price, discount=discount,
            discount_type=discount_type, total_price=total_price,
        )




class SaleReturnRepository:
    @staticmethod
    def get_by_request_id(tenant, request_id):
        return (
            SaleReturn.objects
            .filter(tenant=tenant, request_id=request_id)
            .select_related("invoice", "created_by")
            .prefetch_related("items__invoice_item__product")
            .first()
        )

    @staticmethod
    def create(*, tenant, invoice, request_id, created_by, refund_method, reason=""):
        return SaleReturn.objects.create(
            tenant=tenant,
            invoice=invoice,
            request_id=request_id,
            created_by=created_by,
            refund_method=refund_method,
            reason=reason,
        )

    @staticmethod
    def list_by_invoice(invoice):
        return (
            SaleReturn.objects
            .filter(invoice=invoice, tenant=invoice.tenant)
            .select_related("created_by")
            .prefetch_related("items__invoice_item__product")
            .order_by("-created_at", "-id")
        )

    @staticmethod
    def get_detailed(return_id, tenant):
        try:
            return (
                SaleReturn.objects
                .filter(id=return_id, tenant=tenant)
                .select_related("invoice", "created_by")
                .prefetch_related("items__invoice_item__product")
                .get()
            )
        except SaleReturn.DoesNotExist:
            raise SaleReturnException("Return record not found.")


class SaleReturnItemRepository:
    @staticmethod
    def create(*, sale_return, invoice_item, quantity, refund_unit_price, refund_amount):
        return SaleReturnItem.objects.create(
            sale_return=sale_return,
            invoice_item=invoice_item,
            quantity=quantity,
            refund_unit_price=refund_unit_price,
            refund_amount=refund_amount,
        )

class ProductStockRepository:
    @staticmethod
    def get_locked_by_id(product_id, tenant):
        try:
            return Product.objects.select_for_update().get(id=product_id, tenant=tenant)
        except Product.DoesNotExist:
            raise ProductNotFoundException()