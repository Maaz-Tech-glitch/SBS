from products.models import Product
from products.exceptions import ProductNotFoundException
from .models import Invoice, InvoiceItem
from .exceptions import InvoiceNotFoundException


class InvoiceRepository:
    @staticmethod
    def get_by_id(invoice_id):
        try:
            return Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            raise InvoiceNotFoundException()

    @staticmethod
    def get_locked_by_id(invoice_id):
        try:
            return Invoice.objects.select_for_update().get(id=invoice_id)
        except Invoice.DoesNotExist:
            raise InvoiceNotFoundException()

    @staticmethod
    def create(shopkeeper):
        return Invoice.objects.create(shopkeeper=shopkeeper)

    @staticmethod
    def list_by_shopkeeper(shopkeeper):
        return Invoice.objects.filter(shopkeeper=shopkeeper).order_by("-created_at")
    @staticmethod
    def get_completed_in_range(shopkeeper, start_date, end_date):
        return Invoice.objects.filter(
            shopkeeper=shopkeeper, status="COMPLETED",
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
    def create(invoice, product, quantity, unit_price, discount, discount_type, total_price):
        return InvoiceItem.objects.create(
            invoice=invoice, product=product, quantity=quantity,
            unit_price=unit_price, discount=discount,
            discount_type=discount_type, total_price=total_price,
        )


class ProductStockRepository:
    @staticmethod
    def get_locked_by_id(product_id):
        try:
            return Product.objects.select_for_update().get(id=product_id)
        except Product.DoesNotExist:
            raise ProductNotFoundException()