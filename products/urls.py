from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet,   ProductViewSet,RestockProductAPIView,LowStockAPIView,OutOfStockAPIView 

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="categories")
router.register("products", ProductViewSet, basename="products")

urlpatterns = [
    path("restock-product/", RestockProductAPIView.as_view()),
    path("low-stock-product/", LowStockAPIView.as_view()),
    path("out-of-stock-product/", OutOfStockAPIView.as_view()),
    path("", include(router.urls)),
]