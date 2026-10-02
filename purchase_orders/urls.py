from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PurchaseOrderProductListView, PurchaseOrderViewSet, SupplierListCreateView

router = DefaultRouter()
router.register("purchase-orders", PurchaseOrderViewSet, basename="purchase-orders")

urlpatterns = [
    path("purchase-orders/products/", PurchaseOrderProductListView.as_view(), name="purchase-order-products"),
    path("suppliers/", SupplierListCreateView.as_view(), name="supplier-list-create"),
    path("", include(router.urls)),
]