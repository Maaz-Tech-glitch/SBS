from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from subscriptions.permissions import IsSubscriptionActive
from accounting.exceptions import AccountingException
from accounting.notification_handlers import AccountingNotificationService

from .serializers import (
    InvoiceSerializer, InvoiceDetailSerializer, InvoiceListSerializer,
    CompleteSaleSerializer, AddItemSerializer,
)
from .services import InvoiceService, ReceiptService
from .repositories import InvoiceRepository
from .services import InvoiceOwnershipService


class AddItemAPIView(APIView):
    permission_classes = [IsAuthenticated , IsSubscriptionActive]

    def post(self, request):
        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        invoice = InvoiceService.add_item(
            invoice_id=data.get("invoice_id"),
            customer_name=data.get("customer_name"),
            product_id=data.get("product_id"),
            quantity=data.get("quantity", 1),
            discount=data.get("discount"),
            discount_type=data.get("discount_type"),
            invoice_discount=data.get("invoice_discount"),
            invoice_discount_type=data.get("invoice_discount_type"),
            user=request.user, 
        )
        return Response(InvoiceDetailSerializer(invoice).data)


class PendingInvoicesAPIView(ListAPIView):
    serializer_class = InvoiceListSerializer
    permission_classes = [IsAuthenticated , IsSubscriptionActive]
    filter_backends = [OrderingFilter, SearchFilter, DjangoFilterBackend]
    ordering_fields = ["created_at", "total_amount"]
    filterset_fields = ["status"]
    ordering = ["-created_at"]
    search_fields = ["customer_name", "id"]

    def get_queryset(self):
        return InvoiceService.list_pending(self.request.user)


class CompleteSaleAPIView(APIView):
    permission_classes = [IsAuthenticated , IsSubscriptionActive]

    def post(self, request, pk):
        serializer = CompleteSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invoice = InvoiceService.complete_sale(
                invoice_id=pk,
                payment_method=serializer.validated_data["payment_method"],
                user=request.user,
            )

        except AccountingException as exc:
            # InvoiceService.complete_sale() uses transaction.atomic().
            # By the time execution reaches here, sale + stock changes have
            # rolled back, so the failure alert can safely survive.
            AccountingNotificationService.sync_failure(
                tenant=request.user.tenant,
                actor=request.user,
                source="SALE",
                error=exc,
                entity_type="INVOICE",
                entity_id=pk,
            )
            raise

        # Normal successful sale intentionally creates NO accounting
        # notification. Product LOW/OUT stock alerts remain separate.
        return Response(
            InvoiceSerializer(invoice).data
        )


class CancelInvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated , IsSubscriptionActive]

    def post(self, request, pk):
        invoice = InvoiceService.cancel(invoice_id=pk, user=request.user)
        return Response(InvoiceSerializer(invoice).data)


class GenerateInvoicePDFAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def post(self, request, pk):
        invoice = InvoiceRepository.get_by_id(pk, tenant=request.user.tenant)
        file_name = ReceiptService.generate_pdf(invoice)
        return Response(
            {"message": "PDF generated successfully.", "file": file_name},
            status=status.HTTP_201_CREATED,
        )


class GenerateThermalReceiptAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def get(self, request, pk):
        invoice = InvoiceRepository.get_by_id(pk, tenant=request.user.tenant)
        receipt = ReceiptService.generate_thermal_receipt(invoice)
        return Response({"receipt": receipt})


class InvoiceDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def get(self, request, pk):
        invoice = InvoiceService.get_detail(
            invoice_id=pk,
            tenant=request.user.tenant
        )

        return Response(
            InvoiceDetailSerializer(invoice).data,
            status=status.HTTP_200_OK
        )
