# from rest_framework import viewsets, status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.decorators import action
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.filters import SearchFilter, OrderingFilter 
# import django_filters
# from subscriptions.permissions import IsSubscriptionActive
# from .models import Category, Product
# from .serializers import CategorySerializer, ProductSerializer, RestockProductSerializer
# from .permissions import IsAdminOrShopkeeper, IsAdminForDelete
# from .services import restock_product, low_stock_products, out_of_stock_products , create_product_with_purchase

# class CategoryViewSet(viewsets.ModelViewSet):
#     serializer_class = CategorySerializer
#     permission_classes = [IsAuthenticated, IsAdminOrShopkeeper, IsSubscriptionActive]
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_fields = ["name"]
#     search_fields = ["name", "description"]
#     ordering_fields = ["name", "id"]

#     def get_queryset(self):
#         return Category.objects.filter(tenant=self.request.user.tenant).order_by("-id")

#     def perform_create(self, serializer):
#         serializer.save(tenant=self.request.user.tenant)


# class ProductFilter(django_filters.FilterSet):
#     category = django_filters.CharFilter(field_name="category__name", lookup_expr="icontains")
#     name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

#     class Meta:
#         model = Product
#         fields = ["barcode", "category", "name"]


# class ProductViewSet(viewsets.ModelViewSet):
#     serializer_class = ProductSerializer
#     permission_classes = [IsAuthenticated, IsSubscriptionActive]
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_class = ProductFilter
#     search_fields = ["name", "category__name", "barcode", "description"]
#     ordering_fields = ["name", "id", "price"]

#     def get_queryset(self):
#         tenant = self.request.user.tenant
#         stock_status = self.request.query_params.get("stock_status", None)

#         if stock_status == "low":
#             return low_stock_products(tenant)
#         elif stock_status == "out":
#             return out_of_stock_products(tenant)
#         return Product.objects.filter(tenant=tenant).order_by("-id")

#     def perform_create(self, serializer):
#         serializer.save(tenant=self.request.user.tenant)

#     def get_permissions(self):
#         permissions = [IsAuthenticated(), IsAdminOrShopkeeper(), IsSubscriptionActive()]
#         if self.request.method == "DELETE":
#             permissions.append(IsAdminForDelete())
#         return permissions
#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context['request'] = self.request
#         return context
#     def perform_create(self, serializer):
#         serializer.is_valid(raise_exception=True)
#         product = create_product_with_purchase(
#             serializer.validated_data, tenant=self.request.user.tenant, user=self.request.user
#         )
#         serializer.instance = product   # response mein product data return karne ke liye
#     @action(detail=True, methods=["post"], url_path="restock")
#     def restock(self, request, pk=None):
#         from .exceptions import ProductNotFoundException
#         serializer = RestockProductSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         data = serializer.validated_data

#         product = Product.objects.filter(pk=pk, tenant=request.user.tenant).first()
#         if not product:
#             raise ProductNotFoundException()

#         updated_product = restock_product(
#             product.id,
#             data["quantity"],
#             user=request.user,
#             unit_cost=data.get("unit_cost"),
#             payment_method=data.get("payment_method", "CASH"),
#         )
#         return Response(ProductSerializer(updated_product).data, status=status.HTTP_200_OK)

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import django_filters
from subscriptions.permissions import IsSubscriptionActive
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer, RestockProductSerializer
from .permissions import IsAdminOrShopkeeper, IsAdminForDelete
from .services import restock_product, low_stock_products, out_of_stock_products, create_product_with_purchase


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrShopkeeper, IsSubscriptionActive]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["name"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "id"]

    def get_queryset(self):
        return Category.objects.filter(tenant=self.request.user.tenant).order_by("-id")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__name", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Product
        fields = ["barcode", "category", "name"]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsSubscriptionActive]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "category__name", "barcode", "description"]
    ordering_fields = ["name", "id", "price"]

    def get_queryset(self):
        tenant = self.request.user.tenant
        stock_status = self.request.query_params.get("stock_status", None)

        if stock_status == "low":
            return low_stock_products(tenant)
        elif stock_status == "out":
            return out_of_stock_products(tenant)
        return Product.objects.filter(tenant=tenant).order_by("-id")

    def get_permissions(self):
        permissions = [IsAuthenticated(), IsAdminOrShopkeeper(), IsSubscriptionActive()]
        if self.request.method == "DELETE":
            permissions.append(IsAdminForDelete())
        return permissions

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        product = create_product_with_purchase(
            serializer.validated_data, tenant=self.request.user.tenant, user=self.request.user
        )
        serializer.instance = product

    @action(detail=True, methods=["post"], url_path="restock")
    def restock(self, request, pk=None):
        from .exceptions import ProductNotFoundException
        serializer = RestockProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = Product.objects.filter(pk=pk, tenant=request.user.tenant).first()
        if not product:
            raise ProductNotFoundException()

        updated_product = restock_product(
            product.id,
            data["quantity"],
            user=request.user,
            tenant=request.user.tenant,
            unit_cost=data.get("unit_cost"),
            payment_method=data.get("payment_method", "CASH"),
        )
        return Response(ProductSerializer(updated_product).data, status=status.HTTP_200_OK)