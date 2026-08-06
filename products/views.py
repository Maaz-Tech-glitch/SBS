from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter 
import django_filters

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer, RestockProductSerializer
from .permissions import IsAdminOrShopkeeper, IsAdminForDelete
from .services import restock_product, low_stock_products, out_of_stock_products


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("-id")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrShopkeeper]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["name"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "id"]


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__name", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Product
        fields = ["barcode", "category", "name"]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "category__name", "barcode", "description"]
    ordering_fields = ["name", "id", "price"]

    def get_queryset(self):
        queryset = Product.objects.all().order_by("-id")
        stock_status = self.request.query_params.get("stock_status", None)

        if stock_status == "low":
            return low_stock_products()
        elif stock_status == "out":
            return out_of_stock_products()
        return queryset
    def get_permissions(self):
        permissions = [IsAuthenticated(), IsAdminOrShopkeeper()]
        if self.request.method == "DELETE":
            permissions.append(IsAdminForDelete())
        return permissions

    @action(detail=True, methods=["post"], url_path="restock")
    def restock(self, request, pk=None):
        serializer = RestockProductSerializer(data=request.data)
        if serializer.is_valid():
            updated_product = restock_product(
                pk,
                serializer.validated_data["quantity"],
            )
            return Response(ProductSerializer(updated_product).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)