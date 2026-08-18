# from django.urls import path
# from .views import (
#     AddItemAPIView,
#     PendingInvoicesAPIView,
#     CompleteSaleAPIView,
#     CancelInvoiceAPIView,
#     GenerateInvoicePDF,
#     GenerateThermalReceipt,
# )

# urlpatterns = [
#     path("Add-Item/", AddItemAPIView.as_view(), name="manage-item"),
#     path("invoices/", PendingInvoicesAPIView.as_view(), name="invoice-list"),
#     path("invoices/<int:pk>/complete/", CompleteSaleAPIView.as_view(), name="complete-sale"),
#     path("invoices/<int:pk>/cancel/", CancelInvoiceAPIView.as_view(), name="cancel-invoice"),
#     path("invoices/<int:pk>/pdf/", GenerateInvoicePDF.as_view(), name="invoice-pdf"),
#     path("invoices/<int:pk>/receipt/", GenerateThermalReceipt.as_view(), name="thermal-receipt"),
# ]

from django.urls import path
from .views import (
    AddItemAPIView,
    PendingInvoicesAPIView,
    CompleteSaleAPIView,
    CancelInvoiceAPIView,
    GenerateInvoicePDFAPIView,
    GenerateThermalReceiptAPIView,
)

urlpatterns = [
    path("add-item/", AddItemAPIView.as_view(), name="manage-item"),
    path("invoices/", PendingInvoicesAPIView.as_view(), name="invoice-list"),
    path("invoices/<int:pk>/complete/", CompleteSaleAPIView.as_view(), name="complete-sale"),
    path("invoices/<int:pk>/cancel/", CancelInvoiceAPIView.as_view(), name="cancel-invoice"),
    path("invoices/<int:pk>/pdf/", GenerateInvoicePDFAPIView.as_view(), name="invoice-pdf"),
    path("invoices/<int:pk>/receipt/", GenerateThermalReceiptAPIView.as_view(), name="thermal-receipt"),
]