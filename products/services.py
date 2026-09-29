from django.db import transaction
from django.db.models import F
from decimal import Decimal
from .repositories import ProductRepository, ProductStockRepository
from accounting.services import AccountingIntegrationService
from .models import Product

def low_stock_products(tenant):
    return ProductRepository.get_low_stock(tenant)

def out_of_stock_products(tenant):
    return ProductRepository.get_out_of_stock(tenant)

def restock_product(product_id, quantity, user, tenant, unit_cost=None,
                    payment_method="CASH", supplier_name=None, paid_amount=None):
    with transaction.atomic():
        # Row-level lock via select_for_update and atomic DB math with F() to eliminate race conditions
        product = ProductStockRepository.get_locked_by_id(product_id, tenant=tenant)
        product.stock = F("stock") + quantity
        product.save(update_fields=["stock", "updated_at"])
        product.refresh_from_db(fields=["stock"])

        cost = unit_cost if unit_cost is not None else (product.cost_price if product.cost_price > 0 else product.price)
        total_cost = cost * quantity

        if paid_amount is not None:
            paid = paid_amount
        elif supplier_name:
            paid = Decimal("0.00")
        else:
            paid = total_cost

        AccountingIntegrationService.record_transaction(
            tenant=product.tenant, user=user, transaction_type="PURCHASE",
            amount=total_cost, paid_amount=paid, payment_method=payment_method,
            supplier_name=supplier_name,
            description=f"Restock: {product.name} x {quantity}",
        )
        return product

def create_product_with_purchase(validated_data, tenant, user):
    payment_method = validated_data.pop("payment_method", "CASH")
    is_opening_stock = validated_data.pop("is_opening_stock", False)
    supplier_name = validated_data.pop("supplier_name", None)
    paid_amount = validated_data.pop("paid_amount", None)

    with transaction.atomic():
        product = Product.objects.create(tenant=tenant, **validated_data)
        if product.stock > 0:
            unit_cost = product.cost_price if product.cost_price > 0 else product.price
            total_cost = unit_cost * product.stock
            if paid_amount is not None:
                paid = paid_amount
            elif supplier_name:
                paid = Decimal("0.00")  
            else:
                paid = total_cost  
            transaction_type = "OPENING_STOCK" if is_opening_stock else "PURCHASE"
            kwargs = dict(
                tenant=tenant, user=user, transaction_type=transaction_type,
                amount=total_cost, payment_method=payment_method,
                description=f"{'Opening stock' if is_opening_stock else 'Initial stock purchase'}: {product.name} x {product.stock}",
            )
            if transaction_type == "PURCHASE":
                kwargs["paid_amount"] = paid
                kwargs["supplier_name"] = supplier_name

            AccountingIntegrationService.record_transaction(**kwargs)
        return product