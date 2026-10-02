from io import BytesIO
from xml.sax.saxutils import escape

from django.db.models import Count
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from products.models import Product

from subscriptions.permissions import IsSubscriptionActive
from users.permissions import HasModuleAccess

from .models import PurchaseOrder, Supplier
from .serializers import (
    PurchaseOrderListSerializer,
    PurchaseOrderProductSerializer,
    PurchaseOrderSerializer,
    SupplierSerializer,
)
from .services import PurchaseOrderService


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    required_module = "inventory.purchase_orders"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    http_method_names = ["get", "post", "patch", "head", "options"]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["po_number", "supplier__name", "created_by__username", "created_by__first_name", "created_by__last_name"]
    ordering_fields = ["created_at", "po_number", "status"]

    def get_queryset(self):
        return (
            PurchaseOrder.objects.filter(tenant=self.request.user.tenant)
            .select_related("supplier", "created_by", "tenant")
            .prefetch_related("items__product")
            .annotate(item_count=Count("items", distinct=True))
        )

    def get_serializer_class(self):
        if self.action == "list":
            return PurchaseOrderListSerializer
        return PurchaseOrderSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_object(self):
        try:
            return self.get_queryset().get(pk=self.kwargs["pk"])
        except (PurchaseOrder.DoesNotExist, ValueError):
            raise NotFound("Purchase order not found.")

    @action(detail=False, methods=["post"], url_path="create-final")
    def create_final(self, request):
        serializer = PurchaseOrderSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            order = serializer.save()
            order = PurchaseOrderService.finalize(order.pk, request.user.tenant)
        order = self.get_queryset().get(pk=order.pk)
        return Response(
            PurchaseOrderSerializer(order, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def discard(self, request, pk=None):
        discarded = PurchaseOrderService.discard(pk, request.user.tenant)
        if discarded is None:
            raise NotFound("Purchase order not found.")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize(self, request, pk=None):
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            order = serializer.save()
            order = PurchaseOrderService.finalize(order.pk, request.user.tenant)
        order = self.get_queryset().get(pk=order.pk)
        return Response(PurchaseOrderSerializer(order, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        order = self.get_object()
        if order.status == PurchaseOrder.Status.DRAFT:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Drafts cannot be downloaded as purchase orders.")
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
            pageCompression=0,
            title=f"Purchase Order {order.po_number}",
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "PurchaseOrderTitle", parent=styles["Title"], alignment=TA_CENTER,
            textColor=colors.HexColor("#17263B"), spaceAfter=14,
        )
        body_style = styles["BodyText"]
        elements = [
            Paragraph(escape(order.tenant.name), styles["Heading2"]),
            Paragraph("PURCHASE ORDER", title_style),
            Paragraph(
                f"<b>PO Number:</b> {escape(order.po_number or 'DRAFT - NOT NUMBERED')}",
                body_style,
            ),
            Paragraph(
                f"<b>Date:</b> {timezone.localtime(order.finalized_at or order.updated_at).strftime('%B %d, %Y')}",
                body_style,
            ),
            Spacer(1, 16),
            Paragraph("<b>Supplier</b>", styles["Heading3"]),
            Paragraph(escape(order.supplier.name), body_style),
        ]
        for value in (order.supplier.address, order.supplier.phone, order.supplier.email):
            if value:
                elements.append(Paragraph(escape(value).replace("\n", "<br/>"), body_style))

        elements.extend([Spacer(1, 18), Paragraph("<b>Required Products</b>", styles["Heading3"])])
        rows = [["#", "Product", "Required Quantity"]]
        rows.extend([
            [str(index), Paragraph(escape(item.product.name), body_style), str(item.quantity)]
            for index, item in enumerate(order.items.select_related("product").all(), start=1)
        ])
        table = Table(rows, colWidths=[0.45 * inch, 4.6 * inch, 1.8 * inch], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEBFA")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17263B")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B7C8D9")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F8FC")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elements.extend([table, Spacer(1, 18)])
        if order.notes:
            elements.extend([
                Paragraph("<b>Notes</b>", styles["Heading3"]),
                Paragraph(escape(order.notes).replace("\n", "<br/>"), body_style),
                Spacer(1, 14),
            ])
        requested_by = order.created_by.get_full_name() or order.created_by.username if order.created_by else ""
        elements.extend([
            Paragraph(f"<b>Requested By:</b> {escape(requested_by)}", body_style),
            Spacer(1, 24),
            Paragraph("Please confirm product availability and current rates.", body_style),
        ])
        document.build(elements)
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"{order.po_number}.pdf",
            content_type="application/pdf",
        )


class SupplierListCreateView(generics.ListCreateAPIView):
    required_module = "inventory.purchase_orders"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    serializer_class = SupplierSerializer
    search_fields = ["name", "phone", "email"]

    def get_queryset(self):
        return Supplier.objects.filter(tenant=self.request.user.tenant, is_active=True)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)


class PurchaseOrderProductListView(generics.ListAPIView):
    required_module = "inventory.purchase_orders"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    serializer_class = PurchaseOrderProductSerializer

    def get_queryset(self):
        return Product.objects.filter(
            tenant=self.request.user.tenant,
            is_active=True,
        ).order_by("name", "id")