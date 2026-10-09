# from rest_framework import viewsets, status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.decorators import action
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.filters import SearchFilter, OrderingFilter
# from rest_framework.pagination import PageNumberPagination
# from django.db import transaction
# from django.db.models import Count, Q
# import django_filters
# from subscriptions.permissions import IsSubscriptionActive
# from users.permissions import HasModuleAccess
# from .models import Category, Product
# from .serializers import CategorySerializer, ProductSerializer, RestockProductSerializer, BulkProductImportSerializer
# from .permissions import IsAdminOrShopkeeper, IsAdminForDelete
# from .services import restock_product, low_stock_products, out_of_stock_products, create_product_with_purchase, bulk_import_products
# from .notification_handlers import ProductNotificationService, CategoryNotificationService


# class CategoryPagination(PageNumberPagination):
#     """
#     Server-side pagination for category management.

#     The Categories page requests 20 rows at a time. page_size stays configurable
#     (with a safe cap) so existing category consumers keep working unchanged.
#     """
#     page_size = 20
#     page_size_query_param = "page_size"
#     max_page_size = 100
#     page_query_param = "page"


# class CategoryFilter(django_filters.FilterSet):
#     # Preserve the existing ?name= exact filter.
#     name = django_filters.CharFilter(field_name="name")
#     is_active = django_filters.BooleanFilter(field_name="is_active")
#     product_count_filter = django_filters.CharFilter(
#         method="filter_product_count"
#     )

#     def filter_product_count(self, queryset, name, value):
#         value = (value or "").upper()

#         if value == "HAS_PRODUCTS":
#             return queryset.filter(product_count__gt=0)

#         if value == "EMPTY":
#             return queryset.filter(product_count=0)

#         return queryset

#     class Meta:
#         model = Category
#         fields = ["name", "is_active"]


# class CategoryViewSet(viewsets.ModelViewSet):
#     serializer_class = CategorySerializer
#     required_module = "products"
#     permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_class = CategoryFilter
#     pagination_class = CategoryPagination
#     search_fields = ["name", "description"]
#     ordering_fields = ["name", "id"]

#     def get_queryset(self):
#         # product_count is calculated in SQL before pagination. This avoids
#         # loading all products in the frontend just to count each category.
#         return (
#             Category.objects
#             .filter(tenant=self.request.user.tenant)
#             .annotate(product_count=Count("products"))
#             .order_by("-id")
#         )

#     def perform_create(self, serializer):
#         try:
#             with transaction.atomic():
#                 category = serializer.save(
#                     tenant=self.request.user.tenant
#                 )

#                 CategoryNotificationService.schedule_category_created(
#                     category=category,
#                     actor=self.request.user,
#                 )
#         except Exception as exc:
#             CategoryNotificationService.schedule_failure(
#                 tenant=self.request.user.tenant,
#                 actor=self.request.user,
#                 operation="CREATE",
#                 error=exc,
#             )
#             raise

#     def perform_update(self, serializer):
#         category_before = serializer.instance
#         old_status = category_before.is_active
#         changed_fields = list(serializer.validated_data.keys())

#         try:
#             with transaction.atomic():
#                 category = serializer.save()
#                 new_status = category.is_active

#                 if old_status != new_status:
#                     CategoryNotificationService.schedule_status_changed(
#                         category=category,
#                         actor=self.request.user,
#                         old_status=old_status,
#                         new_status=new_status,
#                     )

#                 # Avoid duplicate "updated" notification when the user only
#                 # toggles Active/Inactive. If other fields changed too, keep
#                 # the normal Category Updated event as well.
#                 non_status_fields = [
#                     field
#                     for field in changed_fields
#                     if field != "is_active"
#                 ]

#                 if non_status_fields:
#                     CategoryNotificationService.schedule_category_updated(
#                         category=category,
#                         actor=self.request.user,
#                         changed_fields=non_status_fields,
#                     )

#         except Exception as exc:
#             CategoryNotificationService.schedule_failure(
#                 tenant=self.request.user.tenant,
#                 actor=self.request.user,
#                 operation="UPDATE",
#                 error=exc,
#                 category=category_before,
#             )
#             raise


# class ProductPagination(PageNumberPagination):
#     """
#     Server-side product pagination.

#     Products page uses 20 rows per request. page_size remains configurable
#     (capped at 100) so existing POS/search consumers can keep their current
#     behavior without loading the complete catalogue automatically.
#     """
#     page_size = 20
#     page_size_query_param = "page_size"
#     max_page_size = 100
#     page_query_param = "page"


# class ProductFilter(django_filters.FilterSet):
#     # Existing filters are preserved for backward compatibility.
#     category = django_filters.CharFilter(
#         field_name="category__name",
#         lookup_expr="icontains",
#     )
#     name = django_filters.CharFilter(
#         field_name="name",
#         lookup_expr="icontains",
#     )

#     # Products-page filters. These run in PostgreSQL before pagination.
#     product_search = django_filters.CharFilter(method="filter_product_search")
#     category_id = django_filters.NumberFilter(field_name="category_id")
#     price_range = django_filters.CharFilter(method="filter_price_range")
#     stock_filter = django_filters.CharFilter(method="filter_stock")
#     is_active = django_filters.BooleanFilter(field_name="is_active")

#     def filter_product_search(self, queryset, name, value):
#         value = (value or "").strip()

#         if not value:
#             return queryset

#         return queryset.filter(
#             Q(name__icontains=value)
#             | Q(barcode__icontains=value)
#             | Q(sku__icontains=value)
#             | Q(category__name__icontains=value)
#         )

#     def filter_price_range(self, queryset, name, value):
#         value = (value or "").upper()

#         if value == "UNDER_1000":
#             return queryset.filter(price__lt=1000)

#         if value == "1000_5000":
#             return queryset.filter(price__gte=1000, price__lte=5000)

#         if value == "5000_10000":
#             return queryset.filter(price__gt=5000, price__lte=10000)

#         if value == "ABOVE_10000":
#             return queryset.filter(price__gt=10000)

#         return queryset

#     def filter_stock(self, queryset, name, value):
#         value = (value or "").upper()

#         if value == "IN_STOCK":
#             return queryset.filter(stock__gt=5)

#         if value == "LOW_STOCK":
#             return queryset.filter(stock__gt=0, stock__lte=5)

#         if value == "OUT_OF_STOCK":
#             return queryset.filter(stock=0)

#         return queryset

#     class Meta:
#         model = Product
#         fields = ["barcode", "category", "name", "is_active"]


# class ProductViewSet(viewsets.ModelViewSet):
#     serializer_class = ProductSerializer
#     required_module = "products"
#     permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_class = ProductFilter
#     pagination_class = ProductPagination
#     search_fields = ["name", "category__name", "barcode", "description"]
#     ordering_fields = ["name", "id", "price"]

#     def get_queryset(self):
#         tenant = self.request.user.tenant
#         stock_status = self.request.query_params.get("stock_status", None)

#         # Keep the old stock_status behavior for existing clients.
#         if stock_status == "low":
#             return (
#                 low_stock_products(tenant)
#                 .select_related("category")
#                 .order_by("-id")
#             )

#         if stock_status == "out":
#             return (
#                 out_of_stock_products(tenant)
#                 .select_related("category")
#                 .order_by("-id")
#             )

#         # Category name is serialized for every row, so fetch it in the same
#         # query instead of causing one extra category query per product.
#         return (
#             Product.objects
#             .filter(tenant=tenant)
#             .select_related("category")
#             .order_by("-id")
#         )

#     def get_permissions(self):
#         permissions = [IsAuthenticated(), IsAdminOrShopkeeper(), IsSubscriptionActive()]
#         if self.request.method == "DELETE":
#             permissions.append(IsAdminForDelete())
#         return permissions

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context["request"] = self.request
#         return context

#     def perform_create(self, serializer):
#         serializer.is_valid(raise_exception=True)

#         try:
#             product = create_product_with_purchase(
#                 serializer.validated_data,
#                 tenant=self.request.user.tenant,
#                 user=self.request.user
#             )
#         except Exception as exc:
#             # Serializer validation errors happen before this point, so simple
#             # frontend/form validation does not create admin notifications.
#             ProductNotificationService.schedule_failure(
#                 tenant=self.request.user.tenant,
#                 actor=self.request.user,
#                 operation="CREATE",
#                 error=exc,
#             )
#             raise

#         serializer.instance = product

#     def perform_update(self, serializer):
#         old_stock = serializer.instance.stock
#         changed_fields = list(serializer.validated_data.keys())

#         try:
#             with transaction.atomic():
#                 product = serializer.save()

#                 ProductNotificationService.schedule_product_updated(
#                     product=product,
#                     actor=self.request.user,
#                     changed_fields=changed_fields,
#                 )

#                 if old_stock != product.stock:
#                     ProductNotificationService.schedule_stock_transition(
#                         product=product,
#                         old_stock=old_stock,
#                         new_stock=product.stock,
#                         actor=self.request.user,
#                         source="PRODUCT_UPDATE",
#                     )
#         except Exception as exc:
#             ProductNotificationService.schedule_failure(
#                 tenant=self.request.user.tenant,
#                 actor=self.request.user,
#                 operation="UPDATE",
#                 error=exc,
#                 product=serializer.instance,
#             )
#             raise

#     @action(detail=True, methods=["post"], url_path="restock")
#     def restock(self, request, pk=None):
#         from .exceptions import ProductNotFoundException

#         serializer = RestockProductSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         data = serializer.validated_data

#         product = Product.objects.filter(pk=pk, tenant=request.user.tenant).first()

#         if not product:
#             raise ProductNotFoundException()

#         try:
#             updated_product = restock_product(
#                 product.id,
#                 data["quantity"],
#                 user=request.user,
#                 tenant=request.user.tenant,
#                 unit_cost=data.get("unit_cost"),
#                 payment_method=data.get("payment_method", "CASH"),
#                 supplier_name=data.get("supplier_name"),
#                 paid_amount=data.get("paid_amount"),
#             )
#         except Exception as exc:
#             ProductNotificationService.schedule_failure(
#                 tenant=request.user.tenant,
#                 actor=request.user,
#                 operation="RESTOCK",
#                 error=exc,
#                 product=product,
#             )
#             raise

#         return Response(
#             ProductSerializer(updated_product).data,
#             status=status.HTTP_200_OK
#         )

#     # NEW: Bulk products import from CSV
#     @action(detail=False, methods=["post"], url_path="bulk-import")
#     def bulk_import(self, request):
#         serializer = BulkProductImportSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         result = bulk_import_products(
#             csv_file=serializer.validated_data["file"],
#             tenant=request.user.tenant
#         )

#         # One summary notification only; never one notification per CSV row.
#         ProductNotificationService.schedule_bulk_import_result(
#             tenant=request.user.tenant,
#             actor=request.user,
#             result=result,
#         )

#         if not result.get("success"):
#             return Response(
#                 result,
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         return Response(
#             result,
#             status=status.HTTP_200_OK
#         )


from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.db.models import Count, Q
import django_filters
from subscriptions.permissions import IsSubscriptionActive
from users.permissions import HasModuleAccess
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer, RestockProductSerializer, BulkProductImportSerializer
from .permissions import IsAdminOrShopkeeper, IsAdminForDelete
from .services import restock_product, low_stock_products, out_of_stock_products, create_product_with_purchase, bulk_import_products
from .notification_handlers import ProductNotificationService, CategoryNotificationService
from accounting.exceptions import AccountingException
from accounting.notification_handlers import AccountingNotificationService


class CategoryPagination(PageNumberPagination):
    """
    Server-side pagination for category management.

    The Categories page requests 20 rows at a time. page_size stays configurable
    (with a safe cap) so existing category consumers keep working unchanged.
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"


class CategoryFilter(django_filters.FilterSet):
    # Preserve the existing ?name= exact filter.
    name = django_filters.CharFilter(field_name="name")
    is_active = django_filters.BooleanFilter(field_name="is_active")
    product_count_filter = django_filters.CharFilter(
        method="filter_product_count"
    )

    def filter_product_count(self, queryset, name, value):
        value = (value or "").upper()

        if value == "HAS_PRODUCTS":
            return queryset.filter(product_count__gt=0)

        if value == "EMPTY":
            return queryset.filter(product_count=0)

        return queryset

    class Meta:
        model = Category
        fields = ["name", "is_active"]


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    required_module = "products"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CategoryFilter
    pagination_class = CategoryPagination
    search_fields = ["name", "description"]
    ordering_fields = ["name", "id"]

    def get_queryset(self):
        # product_count is calculated in SQL before pagination. This avoids
        # loading all products in the frontend just to count each category.
        return (
            Category.objects
            .filter(tenant=self.request.user.tenant)
            .annotate(product_count=Count("products"))
            .order_by("-id")
        )

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                category = serializer.save(
                    tenant=self.request.user.tenant
                )

                CategoryNotificationService.schedule_category_created(
                    category=category,
                    actor=self.request.user,
                )
        except Exception as exc:
            CategoryNotificationService.schedule_failure(
                tenant=self.request.user.tenant,
                actor=self.request.user,
                operation="CREATE",
                error=exc,
            )
            raise

    def perform_update(self, serializer):
        category_before = serializer.instance
        old_status = category_before.is_active
        changed_fields = list(serializer.validated_data.keys())

        try:
            with transaction.atomic():
                category = serializer.save()
                new_status = category.is_active

                if old_status != new_status:
                    CategoryNotificationService.schedule_status_changed(
                        category=category,
                        actor=self.request.user,
                        old_status=old_status,
                        new_status=new_status,
                    )

                # Avoid duplicate "updated" notification when the user only
                # toggles Active/Inactive. If other fields changed too, keep
                # the normal Category Updated event as well.
                non_status_fields = [
                    field
                    for field in changed_fields
                    if field != "is_active"
                ]

                if non_status_fields:
                    CategoryNotificationService.schedule_category_updated(
                        category=category,
                        actor=self.request.user,
                        changed_fields=non_status_fields,
                    )

        except Exception as exc:
            CategoryNotificationService.schedule_failure(
                tenant=self.request.user.tenant,
                actor=self.request.user,
                operation="UPDATE",
                error=exc,
                category=category_before,
            )
            raise


class ProductPagination(PageNumberPagination):
    """
    Server-side product pagination.

    Products page uses 20 rows per request. page_size remains configurable
    (capped at 100) so existing POS/search consumers can keep their current
    behavior without loading the complete catalogue automatically.
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"


class ProductFilter(django_filters.FilterSet):
    # Existing filters are preserved for backward compatibility.
    category = django_filters.CharFilter(
        field_name="category__name",
        lookup_expr="icontains",
    )
    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
    )

    # Products-page filters. These run in PostgreSQL before pagination.
    product_search = django_filters.CharFilter(method="filter_product_search")
    category_id = django_filters.NumberFilter(field_name="category_id")
    price_range = django_filters.CharFilter(method="filter_price_range")
    stock_filter = django_filters.CharFilter(method="filter_stock")
    is_active = django_filters.BooleanFilter(field_name="is_active")

    def filter_product_search(self, queryset, name, value):
        value = (value or "").strip()

        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value)
            | Q(barcode__icontains=value)
            | Q(sku__icontains=value)
            | Q(category__name__icontains=value)
        )

    def filter_price_range(self, queryset, name, value):
        value = (value or "").upper()

        if value == "UNDER_1000":
            return queryset.filter(price__lt=1000)

        if value == "1000_5000":
            return queryset.filter(price__gte=1000, price__lte=5000)

        if value == "5000_10000":
            return queryset.filter(price__gt=5000, price__lte=10000)

        if value == "ABOVE_10000":
            return queryset.filter(price__gt=10000)

        return queryset

    def filter_stock(self, queryset, name, value):
        value = (value or "").upper()

        if value == "IN_STOCK":
            return queryset.filter(stock__gt=5)

        if value == "LOW_STOCK":
            return queryset.filter(stock__gt=0, stock__lte=5)

        if value == "OUT_OF_STOCK":
            return queryset.filter(stock=0)

        return queryset

    class Meta:
        model = Product
        fields = ["barcode", "category", "name", "is_active"]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    required_module = "products"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = ProductPagination
    search_fields = ["name", "category__name", "barcode", "description"]
    ordering_fields = ["name", "id", "price"]

    def get_queryset(self):
        tenant = self.request.user.tenant
        stock_status = self.request.query_params.get("stock_status", None)

        # Keep the old stock_status behavior for existing clients.
        if stock_status == "low":
            return (
                low_stock_products(tenant)
                .select_related("category")
                .order_by("-id")
            )

        if stock_status == "out":
            return (
                out_of_stock_products(tenant)
                .select_related("category")
                .order_by("-id")
            )

        # Category name is serialized for every row, so fetch it in the same
        # query instead of causing one extra category query per product.
        return (
            Product.objects
            .filter(tenant=tenant)
            .select_related("category")
            .order_by("-id")
        )

    def get_permissions(self):
        permissions = [IsAuthenticated(), IsAdminOrShopkeeper(), IsSubscriptionActive()]
        if self.request.method == "DELETE":
            permissions.append(IsAdminForDelete())
        return permissions

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)

        accounting_source = (
            "OPENING_STOCK"
            if serializer.validated_data.get(
                "is_opening_stock"
            )
            else "INITIAL_STOCK_PURCHASE"
        )

        try:
            product = create_product_with_purchase(
                serializer.validated_data,
                tenant=self.request.user.tenant,
                user=self.request.user
            )
        except Exception as exc:
            # Serializer validation errors happen before this point, so simple
            # frontend/form validation does not create admin notifications.
            ProductNotificationService.schedule_failure(
                tenant=self.request.user.tenant,
                actor=self.request.user,
                operation="CREATE",
                error=exc,
            )

            if isinstance(exc, AccountingException):
                AccountingNotificationService.sync_failure(
                    tenant=self.request.user.tenant,
                    actor=self.request.user,
                    source=accounting_source,
                    error=exc,
                    entity_type="PRODUCT",
                )

            raise

        serializer.instance = product

    def perform_update(self, serializer):
        old_stock = serializer.instance.stock
        changed_fields = list(serializer.validated_data.keys())

        try:
            with transaction.atomic():
                product = serializer.save()

                ProductNotificationService.schedule_product_updated(
                    product=product,
                    actor=self.request.user,
                    changed_fields=changed_fields,
                )

                if old_stock != product.stock:
                    ProductNotificationService.schedule_stock_transition(
                        product=product,
                        old_stock=old_stock,
                        new_stock=product.stock,
                        actor=self.request.user,
                        source="PRODUCT_UPDATE",
                    )
        except Exception as exc:
            ProductNotificationService.schedule_failure(
                tenant=self.request.user.tenant,
                actor=self.request.user,
                operation="UPDATE",
                error=exc,
                product=serializer.instance,
            )
            raise

    @action(detail=True, methods=["post"], url_path="restock")
    def restock(self, request, pk=None):
        from .exceptions import ProductNotFoundException

        serializer = RestockProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = Product.objects.filter(pk=pk, tenant=request.user.tenant).first()

        if not product:
            raise ProductNotFoundException()

        try:
            updated_product = restock_product(
                product.id,
                data["quantity"],
                user=request.user,
                tenant=request.user.tenant,
                unit_cost=data.get("unit_cost"),
                payment_method=data.get("payment_method", "CASH"),
                supplier_name=data.get("supplier_name"),
                paid_amount=data.get("paid_amount"),
            )
        except Exception as exc:
            ProductNotificationService.schedule_failure(
                tenant=request.user.tenant,
                actor=request.user,
                operation="RESTOCK",
                error=exc,
                product=product,
            )

            if isinstance(exc, AccountingException):
                AccountingNotificationService.sync_failure(
                    tenant=request.user.tenant,
                    actor=request.user,
                    source="RESTOCK_PURCHASE",
                    error=exc,
                    entity_type="PRODUCT",
                    entity_id=product.pk,
                )

            raise

        return Response(
            ProductSerializer(updated_product).data,
            status=status.HTTP_200_OK
        )

    # NEW: Bulk products import from CSV
    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        serializer = BulkProductImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = bulk_import_products(
            csv_file=serializer.validated_data["file"],
            tenant=request.user.tenant
        )

        # One summary notification only; never one notification per CSV row.
        ProductNotificationService.schedule_bulk_import_result(
            tenant=request.user.tenant,
            actor=request.user,
            result=result,
        )

        if not result.get("success"):
            return Response(
                result,
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            result,
            status=status.HTTP_200_OK
        )