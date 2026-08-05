from django.urls import path
from .views import (
    AddItemAPIView,
    PendingInvoicesAPIView,
    CompleteSaleAPIView,
    CancelInvoiceAPIView,
    GenerateInvoicePDF,
    GenerateThermalReceipt,
)

urlpatterns = [
    path("Add-Item/", AddItemAPIView.as_view(), name="manage-item"),
    path("Invoice-List/", PendingInvoicesAPIView.as_view()),
    path("complete-sale/", CompleteSaleAPIView.as_view(), name="complete-sale"),
    path("cancel-invoice/", CancelInvoiceAPIView.as_view(), name="cancel-invoice"),
    path("invoice-pdf/<int:invoice_id>/", GenerateInvoicePDF.as_view(), name="invoice-pdf"),
    path("thermal-receipt/<int:invoice_id>/", GenerateThermalReceipt.as_view(), name="thermal-receipt"),
]