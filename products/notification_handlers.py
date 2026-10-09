from django.db import transaction

from notifications.models import Notification
from notifications.services import NotificationService


class ProductNotificationService:
    """
    Product-specific notification rules.

    Important:
    - Notification failures must never break the main POS operation.
    - Notifications are scheduled after the surrounding DB transaction commits.
    - Normal SALE completion itself does not create a notification here.
    """

    LOW_STOCK_THRESHOLD = 5
    PRODUCT_ACTION_URL = "/products"

    @staticmethod
    def _actor_label(actor):
        if actor is None:
            return "System"

        full_name = ""
        if hasattr(actor, "get_full_name"):
            full_name = (actor.get_full_name() or "").strip()

        return full_name or getattr(actor, "username", "User")

    @staticmethod
    def _schedule(callback):
        # robust=True means a notification failure is logged by Django but
        # does not turn an already-successful business operation into an error.
        transaction.on_commit(callback, robust=True)

    @classmethod
    def get_stock_event(cls, old_stock, new_stock):
        """
        Exact threshold rules:

        10 -> 4  = LOW_STOCK
        4  -> 3  = no notification
        8  -> 0  = OUT_OF_STOCK only
        1  -> 0  = OUT_OF_STOCK
        0  -> 10 = no stock alert (restock is a separate event)
        4  -> 10 = no stock alert; future >5 -> <=5 can notify again
        """
        old_stock = int(old_stock)
        new_stock = int(new_stock)

        # Check OUT first so 8 -> 0 never also creates LOW_STOCK.
        if old_stock > 0 and new_stock == 0:
            return "OUT_OF_STOCK"

        if (
            old_stock > cls.LOW_STOCK_THRESHOLD
            and 1 <= new_stock <= cls.LOW_STOCK_THRESHOLD
        ):
            return "LOW_STOCK"

        return None

    @classmethod
    def schedule_product_created(cls, *, product, actor):
        product_id = product.pk
        tenant = product.tenant
        name = product.name
        stock = product.stock
        actor_label = cls._actor_label(actor)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Product Created",
                message=f"{name} was created successfully.",
                event_type="PRODUCT_CREATED",
                level=Notification.Level.SUCCESS,
                entity_type="PRODUCT",
                entity_id=product_id,
                action_url=cls.PRODUCT_ACTION_URL,
                metadata={
                    "product_name": name,
                    "stock": stock,
                    "actor": actor_label,
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_product_updated(
        cls,
        *,
        product,
        actor,
        changed_fields=None,
    ):
        product_id = product.pk
        tenant = product.tenant
        name = product.name
        fields = sorted(set(changed_fields or []))
        actor_label = cls._actor_label(actor)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Product Updated",
                message=f"{name} was updated successfully.",
                event_type="PRODUCT_UPDATED",
                level=Notification.Level.INFO,
                entity_type="PRODUCT",
                entity_id=product_id,
                action_url=cls.PRODUCT_ACTION_URL,
                metadata={
                    "product_name": name,
                    "changed_fields": fields,
                    "actor": actor_label,
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_product_restocked(
        cls,
        *,
        product,
        actor,
        quantity,
        old_stock,
        new_stock,
    ):
        product_id = product.pk
        tenant = product.tenant
        name = product.name
        actor_label = cls._actor_label(actor)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Product Restocked",
                message=(
                    f"{name} was restocked by {quantity}. "
                    f"Stock is now {new_stock}."
                ),
                event_type="PRODUCT_RESTOCKED",
                level=Notification.Level.SUCCESS,
                entity_type="PRODUCT",
                entity_id=product_id,
                action_url=cls.PRODUCT_ACTION_URL,
                metadata={
                    "product_name": name,
                    "quantity_added": int(quantity),
                    "old_stock": int(old_stock),
                    "new_stock": int(new_stock),
                    "actor": actor_label,
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_stock_transition(
        cls,
        *,
        product,
        old_stock,
        new_stock,
        actor=None,
        source="",
    ):
        event = cls.get_stock_event(
            old_stock,
            new_stock,
        )

        if event is None:
            return

        product_id = product.pk
        tenant = product.tenant
        name = product.name
        actor_label = cls._actor_label(actor)

        if event == "OUT_OF_STOCK":
            title = "Product Out of Stock"
            message = f"{name} is now out of stock."
            level = Notification.Level.WARNING
        else:
            title = "Low Stock"
            message = (
                f"{name} is running low. "
                f"Only {new_stock} item(s) remain."
            )
            level = Notification.Level.WARNING

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title=title,
                message=message,
                event_type=event,
                level=level,
                entity_type="PRODUCT",
                entity_id=product_id,
                action_url=cls.PRODUCT_ACTION_URL,
                metadata={
                    "product_name": name,
                    "old_stock": int(old_stock),
                    "new_stock": int(new_stock),
                    "source": str(source or "").upper(),
                    "actor": actor_label,
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_bulk_import_result(
        cls,
        *,
        tenant,
        actor,
        result,
    ):
        success = bool(result.get("success"))
        created = int(result.get("created_count", 0) or 0)
        duplicates = int(result.get("duplicate_count", 0) or 0)
        invalid = int(result.get("invalid_count", 0) or 0)

        if not success:
            title = "Product Import Failed"
            message = (
                result.get("error")
                or "Product CSV import failed."
            )
            event_type = "PRODUCT_BULK_IMPORT_FAILED"
            level = Notification.Level.ERROR
        else:
            title = "Product Import Completed"
            message = (
                f"{created} created, "
                f"{duplicates} duplicate, "
                f"{invalid} invalid."
            )
            event_type = "PRODUCT_BULK_IMPORT_COMPLETED"
            level = (
                Notification.Level.SUCCESS
                if duplicates == 0 and invalid == 0
                else Notification.Level.WARNING
            )

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title=title,
                message=message,
                event_type=event_type,
                level=level,
                entity_type="PRODUCT",
                action_url=cls.PRODUCT_ACTION_URL,
                metadata={
                    "created_count": created,
                    "duplicate_count": duplicates,
                    "invalid_count": invalid,
                },
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
        product=None,
    ):
        operation = str(operation or "PRODUCT").upper()
        product_id = getattr(product, "pk", "")
        product_name = getattr(product, "name", "")
        safe_error = str(error)[:300]

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Product Operation Failed",
                message=(
                    f"{operation.replace('_', ' ').title()} failed"
                    + (
                        f" for {product_name}."
                        if product_name
                        else "."
                    )
                ),
                event_type=f"PRODUCT_{operation}_FAILED",
                level=Notification.Level.ERROR,
                entity_type="PRODUCT",
                entity_id=product_id,
                action_url=cls.PRODUCT_ACTION_URL,
                metadata={
                    "product_name": product_name,
                    "error": safe_error,
                },
            )

        cls._schedule(create_notification)
class CategoryNotificationService:
    """
    Category-specific notification rules.

    Simple serializer validation errors are not notified because DRF validates
    before perform_create/perform_update is called.
    """

    CATEGORY_ACTION_URL = "/categories"

    @staticmethod
    def _actor_label(actor):
        if actor is None:
            return "System"

        full_name = ""
        if hasattr(actor, "get_full_name"):
            full_name = (actor.get_full_name() or "").strip()

        return full_name or getattr(actor, "username", "User")

    @staticmethod
    def _schedule(callback):
        transaction.on_commit(callback, robust=True)

    @classmethod
    def schedule_category_created(cls, *, category, actor):
        category_id = category.pk
        tenant = category.tenant
        name = category.name
        actor_label = cls._actor_label(actor)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Category Created",
                message=f"{name} category was created successfully.",
                event_type="CATEGORY_CREATED",
                level=Notification.Level.SUCCESS,
                entity_type="CATEGORY",
                entity_id=category_id,
                action_url=cls.CATEGORY_ACTION_URL,
                metadata={
                    "category_name": name,
                    "actor": actor_label,
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_category_updated(
        cls,
        *,
        category,
        actor,
        changed_fields=None,
    ):
        category_id = category.pk
        tenant = category.tenant
        name = category.name
        fields = sorted(set(changed_fields or []))
        actor_label = cls._actor_label(actor)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Category Updated",
                message=f"{name} category was updated successfully.",
                event_type="CATEGORY_UPDATED",
                level=Notification.Level.INFO,
                entity_type="CATEGORY",
                entity_id=category_id,
                action_url=cls.CATEGORY_ACTION_URL,
                metadata={
                    "category_name": name,
                    "changed_fields": fields,
                    "actor": actor_label,
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_status_changed(
        cls,
        *,
        category,
        actor,
        old_status,
        new_status,
    ):
        category_id = category.pk
        tenant = category.tenant
        name = category.name
        actor_label = cls._actor_label(actor)

        new_label = "active" if new_status else "inactive"

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Category Status Changed",
                message=f"{name} category is now {new_label}.",
                event_type="CATEGORY_STATUS_CHANGED",
                level=Notification.Level.INFO,
                entity_type="CATEGORY",
                entity_id=category_id,
                action_url=cls.CATEGORY_ACTION_URL,
                metadata={
                    "category_name": name,
                    "old_status": bool(old_status),
                    "new_status": bool(new_status),
                    "actor": actor_label,
                },
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
        category=None,
    ):
        operation = str(operation or "CATEGORY").upper()
        category_id = getattr(category, "pk", "")
        category_name = getattr(category, "name", "")
        safe_error = str(error)[:300]

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="Category Operation Failed",
                message=(
                    f"{operation.replace('_', ' ').title()} failed"
                    + (
                        f" for {category_name}."
                        if category_name
                        else "."
                    )
                ),
                event_type=f"CATEGORY_{operation}_FAILED",
                level=Notification.Level.ERROR,
                entity_type="CATEGORY",
                entity_id=category_id,
                action_url=cls.CATEGORY_ACTION_URL,
                metadata={
                    "category_name": category_name,
                    "error": safe_error,
                },
            )

        cls._schedule(create_notification)
