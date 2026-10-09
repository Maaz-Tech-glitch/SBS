# # from django.db import transaction
# # from django.db.models import F
# # from decimal import Decimal
# # from .repositories import ProductRepository, ProductStockRepository
# # from accounting.services import AccountingIntegrationService
# # from .models import Product

# # def low_stock_products(tenant):
# #     return ProductRepository.get_low_stock(tenant)

# # def out_of_stock_products(tenant):
# #     return ProductRepository.get_out_of_stock(tenant)

# # def restock_product(product_id, quantity, user, tenant, unit_cost=None,
# #                     payment_method="CASH", supplier_name=None, paid_amount=None):
# #     with transaction.atomic():
# #         # Row-level lock via select_for_update and atomic DB math with F() to eliminate race conditions
# #         product = ProductStockRepository.get_locked_by_id(product_id, tenant=tenant)
# #         product.stock = F("stock") + quantity
# #         product.save(update_fields=["stock", "updated_at"])
# #         product.refresh_from_db(fields=["stock"])

# #         cost = unit_cost if unit_cost is not None else (product.cost_price if product.cost_price > 0 else product.price)
# #         total_cost = cost * quantity

# #         if paid_amount is not None:
# #             paid = paid_amount
# #         elif supplier_name:
# #             paid = Decimal("0.00")
# #         else:
# #             paid = total_cost

# #         AccountingIntegrationService.record_transaction(
# #             tenant=product.tenant, user=user, transaction_type="PURCHASE",
# #             amount=total_cost, paid_amount=paid, payment_method=payment_method,
# #             supplier_name=supplier_name,
# #             description=f"Restock: {product.name} x {quantity}",
# #         )
# #         return product

# # def create_product_with_purchase(validated_data, tenant, user):
# #     payment_method = validated_data.pop("payment_method", "CASH")
# #     is_opening_stock = validated_data.pop("is_opening_stock", False)
# #     supplier_name = validated_data.pop("supplier_name", None)
# #     paid_amount = validated_data.pop("paid_amount", None)

# #     with transaction.atomic():
# #         product = Product.objects.create(tenant=tenant, **validated_data)
# #         if product.stock > 0:
# #             unit_cost = product.cost_price if product.cost_price > 0 else product.price
# #             total_cost = unit_cost * product.stock
# #             if paid_amount is not None:
# #                 paid = paid_amount
# #             elif supplier_name:
# #                 paid = Decimal("0.00")  
# #             else:
# #                 paid = total_cost  
# #             transaction_type = "OPENING_STOCK" if is_opening_stock else "PURCHASE"
# #             kwargs = dict(
# #                 tenant=tenant, user=user, transaction_type=transaction_type,
# #                 amount=total_cost, payment_method=payment_method,
# #                 description=f"{'Opening stock' if is_opening_stock else 'Initial stock purchase'}: {product.name} x {product.stock}",
# #             )
# #             if transaction_type == "PURCHASE":
# #                 kwargs["paid_amount"] = paid
# #                 kwargs["supplier_name"] = supplier_name

# #             AccountingIntegrationService.record_transaction(**kwargs)
# #         return product

# import csv
# import io
# from django.db import transaction, IntegrityError
# from django.db.models import F
# from decimal import Decimal
# from .repositories import ProductRepository, ProductStockRepository
# from accounting.services import AccountingIntegrationService
# from .models import Product, Category

# def low_stock_products(tenant):
#     return ProductRepository.get_low_stock(tenant)

# def out_of_stock_products(tenant):
#     return ProductRepository.get_out_of_stock(tenant)

# def restock_product(product_id, quantity, user, tenant, unit_cost=None,
#                     payment_method="CASH", supplier_name=None, paid_amount=None):
#     with transaction.atomic():
#         # Row-level lock via select_for_update and atomic DB math with F() to eliminate race conditions
#         product = ProductStockRepository.get_locked_by_id(product_id, tenant=tenant)
#         product.stock = F("stock") + quantity
#         product.save(update_fields=["stock", "updated_at"])
#         product.refresh_from_db(fields=["stock"])

#         cost = unit_cost if unit_cost is not None else (product.cost_price if product.cost_price > 0 else product.price)
#         total_cost = cost * quantity

#         if paid_amount is not None:
#             paid = paid_amount
#         elif supplier_name:
#             paid = Decimal("0.00")
#         else:
#             paid = total_cost

#         AccountingIntegrationService.record_transaction(
#             tenant=product.tenant, user=user, transaction_type="PURCHASE",
#             amount=total_cost, paid_amount=paid, payment_method=payment_method,
#             supplier_name=supplier_name,
#             description=f"Restock: {product.name} x {quantity}",
#         )
#         return product

# def create_product_with_purchase(validated_data, tenant, user):
#     payment_method = validated_data.pop("payment_method", "CASH")
#     is_opening_stock = validated_data.pop("is_opening_stock", False)
#     supplier_name = validated_data.pop("supplier_name", None)
#     paid_amount = validated_data.pop("paid_amount", None)

#     with transaction.atomic():
#         product = Product.objects.create(tenant=tenant, **validated_data)
#         if product.stock > 0:
#             unit_cost = product.cost_price if product.cost_price > 0 else product.price
#             total_cost = unit_cost * product.stock

#             if paid_amount is not None:
#                 paid = paid_amount
#             elif supplier_name:
#                 paid = Decimal("0.00")
#             else:
#                 paid = total_cost

#             transaction_type = "OPENING_STOCK" if is_opening_stock else "PURCHASE"
#             kwargs = dict(
#                 tenant=tenant, user=user, transaction_type=transaction_type,
#                 amount=total_cost, payment_method=payment_method,
#                 description=f"{'Opening stock' if is_opening_stock else 'Initial stock purchase'}: {product.name} x {product.stock}",
#             )

#             if transaction_type == "PURCHASE":
#                 kwargs["paid_amount"] = paid
#                 kwargs["supplier_name"] = supplier_name

#             AccountingIntegrationService.record_transaction(**kwargs)

#         return product

# # NEW: CSV bulk product import
# def bulk_import_products(csv_file, tenant):
#     from .serializers import BulkProductRowSerializer

#     try:
#         csv_file.seek(0)
#         content = csv_file.read().decode("utf-8-sig")
#     except UnicodeDecodeError:
#         return {
#             "success": False,
#             "error": "CSV file encoding is invalid. Please save file as UTF-8 CSV."
#         }

#     reader = csv.DictReader(io.StringIO(content))

#     if not reader.fieldnames:
#         return {
#             "success": False,
#             "error": "CSV file is empty or header is missing."
#         }

#     # Normalize header names
#     reader.fieldnames = [str(header).strip().lower() for header in reader.fieldnames]

#     required_headers = {"name", "category"}
#     missing_headers = required_headers - set(reader.fieldnames)

#     if missing_headers:
#         return {
#             "success": False,
#             "error": f"Missing required column(s): {', '.join(sorted(missing_headers))}"
#         }

#     created = []
#     duplicates = []
#     invalid = []
#     seen_names = set()
#     total_rows = 0

#     for row_number, row in enumerate(reader, start=2):
#         # Ignore completely empty rows
#         if not any(str(value or "").strip() for value in row.values()):
#             continue

#         total_rows += 1

#         row_data = {
#             "name": str(row.get("name", "") or "").strip(),
#             "category": str(row.get("category", "") or "").strip(),
#             "description": str(row.get("description", "") or "").strip(),
#         }

#         # Validate CSV row
#         serializer = BulkProductRowSerializer(data=row_data)

#         if not serializer.is_valid():
#             errors = []
#             for field, field_errors in serializer.errors.items():
#                 for error in field_errors:
#                     errors.append(f"{field}: {error}")

#             invalid.append({
#                 "row": row_number,
#                 "name": row_data["name"] or "Unknown",
#                 "reason": " | ".join(errors)
#             })
#             continue

#         data = serializer.validated_data
#         product_name = data["name"].strip()
#         category_name = data["category"].strip()
#         description = data.get("description", "").strip()
#         normalized_name = product_name.casefold()

#         # Check duplicate product inside same CSV
#         if normalized_name in seen_names:
#             duplicates.append({
#                 "row": row_number,
#                 "name": product_name,
#                 "reason": "Duplicate product name inside CSV file."
#             })
#             continue

#         seen_names.add(normalized_name)

#         # Check product already exists in this tenant
#         if Product.objects.filter(tenant=tenant, name__iexact=product_name).exists():
#             duplicates.append({
#                 "row": row_number,
#                 "name": product_name,
#                 "reason": "Product already exists in this store."
#             })
#             continue

#         # Category must already exist
#         category = Category.objects.filter(
#             tenant=tenant,
#             name__iexact=category_name
#         ).first()

#         if not category:
#             invalid.append({
#                 "row": row_number,
#                 "name": product_name,
#                 "reason": f"Category '{category_name}' does not exist."
#             })
#             continue

#         product = None

#         # Product model automatically generates barcode and SKU
#         # Retry only in extremely rare unique barcode/SKU collision
#         for attempt in range(5):
#             try:
#                 with transaction.atomic():
#                     product = Product.objects.create(
#                         tenant=tenant,
#                         category=category,
#                         name=product_name,
#                         price=Decimal("0.00"),
#                         cost_price=Decimal("0.00"),
#                         stock=0,
#                         description=description,
#                         is_active=True,
#                     )
#                 break
#             except IntegrityError:
#                 # Product may have been created by another request at same time
#                 if Product.objects.filter(tenant=tenant, name__iexact=product_name).exists():
#                     duplicates.append({
#                         "row": row_number,
#                         "name": product_name,
#                         "reason": "Product already exists in this store."
#                     })
#                     break

#         if product is None:
#             already_duplicate = any(
#                 item["row"] == row_number
#                 for item in duplicates
#             )

#             if not already_duplicate:
#                 invalid.append({
#                     "row": row_number,
#                     "name": product_name,
#                     "reason": "Product could not be created."
#                 })
#             continue

#         created.append({
#             "row": row_number,
#             "id": product.id,
#             "name": product.name,
#             "category": category.name,
#             "description": product.description,
#             "barcode": product.barcode,
#             "sku": product.sku,
#             "stock": product.stock,
#             "price": str(product.price),
#             "cost_price": str(product.cost_price),
#         })

#     return {
#         "success": True,
#         "total_rows": total_rows,
#         "created_count": len(created),
#         "duplicate_count": len(duplicates),
#         "invalid_count": len(invalid),
#         "created": created,
#         "duplicates": duplicates,
#         "invalid": invalid,
#     }

# from django.db import transaction
# from django.db.models import F
# from decimal import Decimal
# from .repositories import ProductRepository, ProductStockRepository
# from accounting.services import AccountingIntegrationService
# from .models import Product

# def low_stock_products(tenant):
#     return ProductRepository.get_low_stock(tenant)

# def out_of_stock_products(tenant):
#     return ProductRepository.get_out_of_stock(tenant)

# def restock_product(product_id, quantity, user, tenant, unit_cost=None,
#                     payment_method="CASH", supplier_name=None, paid_amount=None):
#     with transaction.atomic():
#         # Row-level lock via select_for_update and atomic DB math with F() to eliminate race conditions
#         product = ProductStockRepository.get_locked_by_id(product_id, tenant=tenant)
#         product.stock = F("stock") + quantity
#         product.save(update_fields=["stock", "updated_at"])
#         product.refresh_from_db(fields=["stock"])

#         cost = unit_cost if unit_cost is not None else (product.cost_price if product.cost_price > 0 else product.price)
#         total_cost = cost * quantity

#         if paid_amount is not None:
#             paid = paid_amount
#         elif supplier_name:
#             paid = Decimal("0.00")
#         else:
#             paid = total_cost

#         AccountingIntegrationService.record_transaction(
#             tenant=product.tenant, user=user, transaction_type="PURCHASE",
#             amount=total_cost, paid_amount=paid, payment_method=payment_method,
#             supplier_name=supplier_name,
#             description=f"Restock: {product.name} x {quantity}",
#         )
#         return product

# def create_product_with_purchase(validated_data, tenant, user):
#     payment_method = validated_data.pop("payment_method", "CASH")
#     is_opening_stock = validated_data.pop("is_opening_stock", False)
#     supplier_name = validated_data.pop("supplier_name", None)
#     paid_amount = validated_data.pop("paid_amount", None)

#     with transaction.atomic():
#         product = Product.objects.create(tenant=tenant, **validated_data)
#         if product.stock > 0:
#             unit_cost = product.cost_price if product.cost_price > 0 else product.price
#             total_cost = unit_cost * product.stock
#             if paid_amount is not None:
#                 paid = paid_amount
#             elif supplier_name:
#                 paid = Decimal("0.00")  
#             else:
#                 paid = total_cost  
#             transaction_type = "OPENING_STOCK" if is_opening_stock else "PURCHASE"
#             kwargs = dict(
#                 tenant=tenant, user=user, transaction_type=transaction_type,
#                 amount=total_cost, payment_method=payment_method,
#                 description=f"{'Opening stock' if is_opening_stock else 'Initial stock purchase'}: {product.name} x {product.stock}",
#             )
#             if transaction_type == "PURCHASE":
#                 kwargs["paid_amount"] = paid
#                 kwargs["supplier_name"] = supplier_name

#             AccountingIntegrationService.record_transaction(**kwargs)
#         return product

import csv
import io
from django.db import transaction, IntegrityError
from django.db.models import F
from decimal import Decimal
from .repositories import ProductRepository, ProductStockRepository
from accounting.services import AccountingIntegrationService
from .models import Product, Category
from .notification_handlers import ProductNotificationService

def low_stock_products(tenant):
    return ProductRepository.get_low_stock(tenant)

def out_of_stock_products(tenant):
    return ProductRepository.get_out_of_stock(tenant)

def restock_product(product_id, quantity, user, tenant, unit_cost=None,
                    payment_method="CASH", supplier_name=None, paid_amount=None):
    with transaction.atomic():
        # Row-level lock via select_for_update and atomic DB math with F() to eliminate race conditions
        product = ProductStockRepository.get_locked_by_id(product_id, tenant=tenant)
        old_stock = product.stock

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

        # Runs only after this transaction commits successfully.
        ProductNotificationService.schedule_product_restocked(
            product=product,
            actor=user,
            quantity=quantity,
            old_stock=old_stock,
            new_stock=product.stock,
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

        # Creating a product does not trigger LOW/OUT stock alerts.
        # Those alerts are transition-based, not initial-state alerts.
        ProductNotificationService.schedule_product_created(
            product=product,
            actor=user,
        )

        return product

# NEW: CSV bulk product import
def bulk_import_products(csv_file, tenant):
    from .serializers import BulkProductRowSerializer

    try:
        csv_file.seek(0)
        content = csv_file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return {
            "success": False,
            "error": "CSV file encoding is invalid. Please save file as UTF-8 CSV."
        }

    reader = csv.DictReader(io.StringIO(content))

    if not reader.fieldnames:
        return {
            "success": False,
            "error": "CSV file is empty or header is missing."
        }

    # Normalize header names
    reader.fieldnames = [str(header).strip().lower() for header in reader.fieldnames]

    required_headers = {"name", "category"}
    missing_headers = required_headers - set(reader.fieldnames)

    if missing_headers:
        return {
            "success": False,
            "error": f"Missing required column(s): {', '.join(sorted(missing_headers))}"
        }

    created = []
    duplicates = []
    invalid = []
    seen_names = set()
    total_rows = 0

    for row_number, row in enumerate(reader, start=2):
        # Ignore completely empty rows
        if not any(str(value or "").strip() for value in row.values()):
            continue

        total_rows += 1

        row_data = {
            "name": str(row.get("name", "") or "").strip(),
            "category": str(row.get("category", "") or "").strip(),
            "description": str(row.get("description", "") or "").strip(),
        }

        # Validate CSV row
        serializer = BulkProductRowSerializer(data=row_data)

        if not serializer.is_valid():
            errors = []
            for field, field_errors in serializer.errors.items():
                for error in field_errors:
                    errors.append(f"{field}: {error}")

            invalid.append({
                "row": row_number,
                "name": row_data["name"] or "Unknown",
                "reason": " | ".join(errors)
            })
            continue

        data = serializer.validated_data
        product_name = data["name"].strip()
        category_name = data["category"].strip()
        description = data.get("description", "").strip()
        normalized_name = product_name.casefold()

        # Check duplicate product inside same CSV
        if normalized_name in seen_names:
            duplicates.append({
                "row": row_number,
                "name": product_name,
                "reason": "Duplicate product name inside CSV file."
            })
            continue

        seen_names.add(normalized_name)

        # Check product already exists in this tenant
        if Product.objects.filter(tenant=tenant, name__iexact=product_name).exists():
            duplicates.append({
                "row": row_number,
                "name": product_name,
                "reason": "Product already exists in this store."
            })
            continue

        # Category must already exist
        category = Category.objects.filter(
            tenant=tenant,
            name__iexact=category_name
        ).first()

        if not category:
            invalid.append({
                "row": row_number,
                "name": product_name,
                "reason": f"Category '{category_name}' does not exist."
            })
            continue

        product = None

        # Product model automatically generates barcode and SKU
        # Retry only in extremely rare unique barcode/SKU collision
        for attempt in range(5):
            try:
                with transaction.atomic():
                    product = Product.objects.create(
                        tenant=tenant,
                        category=category,
                        name=product_name,
                        price=Decimal("0.00"),
                        cost_price=Decimal("0.00"),
                        stock=0,
                        description=description,
                        is_active=True,
                    )
                break
            except IntegrityError:
                # Product may have been created by another request at same time
                if Product.objects.filter(tenant=tenant, name__iexact=product_name).exists():
                    duplicates.append({
                        "row": row_number,
                        "name": product_name,
                        "reason": "Product already exists in this store."
                    })
                    break

        if product is None:
            already_duplicate = any(
                item["row"] == row_number
                for item in duplicates
            )

            if not already_duplicate:
                invalid.append({
                    "row": row_number,
                    "name": product_name,
                    "reason": "Product could not be created."
                })
            continue

        created.append({
            "row": row_number,
            "id": product.id,
            "name": product.name,
            "category": category.name,
            "description": product.description,
            "barcode": product.barcode,
            "sku": product.sku,
            "stock": product.stock,
            "price": str(product.price),
            "cost_price": str(product.cost_price),
        })

    return {
        "success": True,
        "total_rows": total_rows,
        "created_count": len(created),
        "duplicate_count": len(duplicates),
        "invalid_count": len(invalid),
        "created": created,
        "duplicates": duplicates,
        "invalid": invalid,
    }