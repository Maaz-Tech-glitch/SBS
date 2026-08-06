from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend


from .models import Invoice
from .serializers import (
    InvoiceSerializer,
    InvoiceDetailSerializer,
    InvoiceListSerializer,
    CompleteSaleSerializer,
    AddItemSerializer,
)
from .services import (
    complete_sale,
    cancel_invoice,
    generate_invoice_pdf,
    generate_thermal_receipt,
    AddItem,
    list_pending_invoices,
)


class AddItemAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        invoice = AddItem(
            invoice_id=data.get("invoice_id"),
            customer_name=data.get("customer_name"),
            product_id=data.get("product_id"),
            quantity=data.get("quantity", 1),
            discount=data.get("discount"),
            discount_type=data.get("discount_type"),
            invoice_discount=data.get("invoice_discount"),
            invoice_discount_type=data.get("invoice_discount_type"),
            shopkeeper=request.user,
        )
        return Response(InvoiceDetailSerializer(invoice).data)


class PendingInvoicesAPIView(ListAPIView):
    serializer_class = InvoiceListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter, SearchFilter, DjangoFilterBackend,]
    ordering_fields = ['created_at', 'total']  
    filterset_fields = ["status"]
    ordering = ['-created_at']  
    search_fields = ['customer_name', 'id'] 
    def get_queryset(self):
        queryset = list_pending_invoices(self.request.user)
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        return queryset


class CompleteSaleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        serializer = CompleteSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = complete_sale(
            invoice_id=pk,
            payment_method=serializer.validated_data["payment_method"],
            user=request.user,
        )
        return Response(InvoiceSerializer(invoice).data)


class CancelInvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        invoice = cancel_invoice(
            invoice_id=pk,
            user=request.user,
        )
        return Response(InvoiceSerializer(invoice).data)


class GenerateInvoicePDF(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        invoice = Invoice.objects.get(id=pk)   
        if invoice.shopkeeper != request.user:
            return Response({"error": "Unauthorized."}, status=403)
        file_name = generate_invoice_pdf(invoice)
        return Response(
            {"message": "PDF generated successfully.", "file": file_name},
            status=status.HTTP_201_CREATED
        )


class GenerateThermalReceipt(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        invoice = Invoice.objects.get(id=pk)  
        if invoice.shopkeeper != request.user:
            return Response({"error": "Unauthorized"}, status=403)
        receipt = generate_thermal_receipt(invoice)
        return Response({"receipt": receipt})