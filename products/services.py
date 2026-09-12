# from .repositories import ProductRepository
# from accounting.services import AccountingIntegrationService
# from django.db import transaction
# from decimal import Decimal
# from .models import Product


# def restock_product(product_id, quantity, user, unit_cost=None, payment_method="CASH"):
#     with transaction.atomic():
#         product = ProductRepository.get_by_id(product_id)
#         product.stock += quantity
#         product.save()

#         cost = unit_cost if unit_cost is not None else product.price
#         total_cost = cost * quantity


#         AccountingIntegrationService.record_transaction(
#             tenant=product.tenant, user=user, transaction_type="PURCHASE",
#             amount=total_cost, payment_method=payment_method,
#             description=f"Restock: {product.name} x {quantity}",)
#         return product

# def low_stock_products(tenant):
#     return ProductRepository.get_low_stock(tenant)

# def out_of_stock_products(tenant):
#     return ProductRepository.get_out_of_stock(tenant)



# # def create_product_with_purchase(validated_data, tenant, user):
# #     payment_method = validated_data.pop("payment_method", "CASH")

# #     with transaction.atomic():
# #         product = Product.objects.create(tenant=tenant, **validated_data)

# #         if product.stock > 0:
# #             total_cost = product.price * product.stock
# #             AccountingIntegrationService.record_transaction(
# #                 tenant=tenant, user=user, transaction_type="PURCHASE",
# #                 amount=total_cost, payment_method=payment_method,
# #                 description=f"Initial stock purchase: {product.name} x {product.stock}",
# #             )
# #         return product
# def create_product_with_purchase(validated_data, tenant, user):
#     payment_method = validated_data.pop("payment_method", "CASH")
#     is_opening_stock = validated_data.pop("is_opening_stock", False) 
#     with transaction.atomic():
#         product = Product.objects.create(tenant=tenant, **validated_data)
#         if product.stock > 0:
#             total_cost = product.price * product.stock
#             transaction_type = "OPENING_STOCK" if is_opening_stock else "PURCHASE"
#             AccountingIntegrationService.record_transaction(
#                 tenant=tenant, user=user, transaction_type=transaction_type,
#                 amount=total_cost, payment_method=payment_method,
#                 description=f"{'Opening stock' if is_opening_stock else 'Initial stock purchase'}: {product.name} x {product.stock}",
#             )
#         return product

from .repositories import ProductRepository
from accounting.services import AccountingIntegrationService
from django.db import transaction
from decimal import Decimal
from .models import Product


def restock_product(product_id, quantity, user, tenant, unit_cost=None, payment_method="CASH"):
    with transaction.atomic():
        product = ProductRepository.get_by_id(product_id, tenant=tenant)
        product.stock += quantity
        product.save()

        cost = unit_cost if unit_cost is not None else product.cost_price
        total_cost = cost * quantity

        AccountingIntegrationService.record_transaction(
            tenant=product.tenant, user=user, transaction_type="PURCHASE",
            amount=total_cost, payment_method=payment_method,
            description=f"Restock: {product.name} x {quantity}",
        )
        return product


def low_stock_products(tenant):
    return ProductRepository.get_low_stock(tenant)


def out_of_stock_products(tenant):
    return ProductRepository.get_out_of_stock(tenant)


def create_product_with_purchase(validated_data, tenant, user):
    payment_method = validated_data.pop("payment_method", "CASH")
    is_opening_stock = validated_data.pop("is_opening_stock", False)
    with transaction.atomic():
        product = Product.objects.create(tenant=tenant, **validated_data)
        if product.stock > 0:
            total_cost = product.cost_price * product.stock
            transaction_type = "OPENING_STOCK" if is_opening_stock else "PURCHASE"
            AccountingIntegrationService.record_transaction(
                tenant=tenant, user=user, transaction_type=transaction_type,
                amount=total_cost, payment_method=payment_method,
                description=f"{'Opening stock' if is_opening_stock else 'Initial stock purchase'}: {product.name} x {product.stock}",
            )
        return product