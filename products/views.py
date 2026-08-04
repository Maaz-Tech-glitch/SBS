from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer,RestockProductSerializer
from .permissions import IsAdminOrShopkeeper, IsAdminForDelete
from .services import restock_product, low_stock_products, out_of_stock_products
from config.pagination import CustomPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter , OrderingFilter 
import django_filters

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("-id")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrShopkeeper]
    filter_backends = [DjangoFilterBackend, SearchFilter , OrderingFilter]
    filterset_fields = ["name"]
    search_fields = ["name", "description"]
    ordering_fields = ["name ", "id"]

class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__name", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Product
        fields = ["barcode", "category", "name"]
        
        
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("-id")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter , OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "category__name", "barcode" , "description"]
    ordering_fields=["name"  , "id " , "price"]
    def get_permissions(self):
        permissions = [IsAuthenticated(), IsAdminOrShopkeeper()]
        if self.request.method == "DELETE":
            permissions.append(IsAdminForDelete())
        return permissions

class RestockProductAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = RestockProductSerializer(data=request.data)
        if serializer.is_valid():
            product = restock_product(
                serializer.validated_data["product_id"],
                serializer.validated_data["quantity"],
            )
            response_serializer = ProductSerializer(product)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=400)


class LowStockAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        products = low_stock_products()
        paginator = CustomPagination()
        paginated_products = paginator.paginate_queryset(products, request)
        if paginated_products is not None:
            serializer = ProductSerializer(paginated_products, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class OutOfStockAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        products = out_of_stock_products()
        paginator = CustomPagination()
        paginated_products = paginator.paginate_queryset(products, request)
        if paginated_products is not None:
            serializer = ProductSerializer(paginated_products, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)