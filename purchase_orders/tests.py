from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounting.models import JournalEntry
from products.models import Category, Product
from subscriptions.models import Plan, Subscription
from tenants.models import Tenant
from users.models import AccessModule, User, UserModulePermission

from .models import PurchaseOrder, PurchaseOrderItem, Supplier


class PurchaseOrderAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Shop One", address="One Road", business_type="Retail")
        self.other_tenant = Tenant.objects.create(name="Shop Two", address="Two Road", business_type="Retail")
        self.plan = Plan.objects.create(name="Test Plan", price="0.00", max_users=5)
        now = timezone.now()
        for tenant in (self.tenant, self.other_tenant):
            Subscription.objects.create(
                tenant=tenant,
                plan=self.plan,
                start_date=now,
                end_date=now + timedelta(days=30),
                status="ACTIVE",
            )
        self.user = User.objects.create_user(
            username="shop-one-user", email="one@example.com", password="password", tenant=self.tenant,
        )
        self.other_user = User.objects.create_user(
            username="shop-two-user", email="two@example.com", password="password", tenant=self.other_tenant,
        )
        self.module = AccessModule.objects.create(
            key="inventory.purchase_orders", name="Purchase Orders", category="Inventory", is_active=True,
        )
        UserModulePermission.objects.create(user=self.user, module=self.module, can_access=True)
        self.category = Category.objects.create(tenant=self.tenant, name="General")
        self.other_category = Category.objects.create(tenant=self.other_tenant, name="General")
        self.product = Product.objects.create(
            tenant=self.tenant, category=self.category, name="Notebook", price="12.00", cost_price="5.00", stock=17,
        )
        self.other_product = Product.objects.create(
            tenant=self.other_tenant, category=self.other_category, name="Pen", price="4.00", stock=8,
        )
        self.supplier = Supplier.objects.create(
            tenant=self.tenant, name="Local Supply", phone="555-0100", email="supply@example.com",
        )
        self.other_supplier = Supplier.objects.create(tenant=self.other_tenant, name="Other Supply")

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def payload(self, **overrides):
        data = {
            "supplier_id": self.supplier.id,
            "items": [{"product": self.product.id, "quantity": 3}],
            "notes": "Please deliver next week.",
        }
        data.update(overrides)
        return data

    def create_order(self, **overrides):
        self.authenticate()
        return self.client.post("/api/purchase-orders/", self.payload(**overrides), format="json")

    def test_draft_creation_has_no_po_number_and_does_not_change_stock_or_accounting(self):
        stock_before = self.product.stock
        entries_before = JournalEntry.objects.count()

        response = self.create_order()

        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNone(response.data["po_number"])
        self.assertEqual(response.data["status"], PurchaseOrder.Status.DRAFT)
        self.assertEqual(response.data["items"][0]["quantity"], 3)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_before)
        self.assertEqual(JournalEntry.objects.count(), entries_before)

    def test_at_least_one_item_is_required(self):
        response = self.create_order(items=[])
        self.assertEqual(response.status_code, 400)

    def test_quantity_must_be_positive_integer(self):
        response = self.create_order(items=[{"product": self.product.id, "quantity": 0}])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(PurchaseOrder.objects.count(), 0)

    def test_duplicate_products_are_rejected(self):
        response = self.create_order(items=[
            {"product": self.product.id, "quantity": 1},
            {"product": self.product.id, "quantity": 2},
        ])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(PurchaseOrder.objects.count(), 0)

    def test_foreign_tenant_supplier_and_product_are_rejected(self):
        supplier_response = self.create_order(supplier_id=self.other_supplier.id)
        self.assertEqual(supplier_response.status_code, 400)
        product_response = self.create_order(items=[{"product": self.other_product.id, "quantity": 1}])
        self.assertEqual(product_response.status_code, 400)
        self.assertEqual(PurchaseOrder.objects.count(), 0)

    def test_purchase_orders_are_tenant_isolated(self):
        created = self.create_order()
        self.authenticate(self.other_user)
        detail = self.client.get(f"/api/purchase-orders/{created.data['id']}/")
        listing = self.client.get("/api/purchase-orders/")
        self.assertEqual(detail.status_code, 404)
        self.assertEqual(listing.data["count"], 0)

    def test_draft_is_editable_and_created_order_is_not(self):
        created = self.create_order()
        detail_url = f"/api/purchase-orders/{created.data['id']}/"
        draft_update = self.client.patch(detail_url, {"notes": "Updated note"}, format="json")
        self.assertEqual(draft_update.status_code, 200, draft_update.data)

        self.client.post(f"{detail_url}finalize/", self.payload(), format="json")
        created_update = self.client.patch(detail_url, {"notes": "Must remain unchanged"}, format="json")
        self.assertEqual(created_update.status_code, 400)
        self.assertEqual(PurchaseOrder.objects.get(pk=created.data["id"]).notes, "Updated note")

    def test_draft_create_assigns_number_without_stock_or_accounting_changes(self):
        created = self.create_order()
        stock_before = self.product.stock
        entries_before = JournalEntry.objects.count()
        response = self.client.post(
            f"/api/purchase-orders/{created.data['id']}/finalize/",
            self.payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], PurchaseOrder.Status.CREATED)
        self.assertEqual(response.data["po_number"], "PO-000001")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_before)
        self.assertEqual(JournalEntry.objects.count(), entries_before)

    def test_discard_deletes_draft_without_consuming_a_po_number(self):
        created = self.create_order()
        detail_url = f"/api/purchase-orders/{created.data['id']}/"
        response = self.client.post(f"{detail_url}discard/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(PurchaseOrder.objects.filter(pk=created.data["id"]).exists())

        finalized = self.client.post(
            "/api/purchase-orders/create-final/",
            self.payload(),
            format="json",
        )
        self.assertEqual(finalized.status_code, 201, finalized.data)
        self.assertEqual(finalized.data["po_number"], "PO-000001")

    def test_created_order_cannot_be_discarded_or_edited(self):
        created = self.client.post(
            "/api/purchase-orders/create-final/",
            self.payload(),
            format="json",
        )
        detail_url = f"/api/purchase-orders/{created.data['id']}/"
        self.assertEqual(self.client.post(f"{detail_url}discard/").status_code, 400)
        self.assertEqual(self.client.patch(detail_url, {"notes": "No edit"}, format="json").status_code, 400)

    def test_creation_is_atomic_when_item_write_fails(self):
        self.authenticate()
        with patch.object(PurchaseOrderItem.objects, "bulk_create", side_effect=RuntimeError("write failed")):
            with self.assertRaises(RuntimeError):
                self.client.post("/api/purchase-orders/", self.payload(), format="json")
        self.assertEqual(PurchaseOrder.objects.count(), 0)
        self.assertEqual(PurchaseOrderItem.objects.count(), 0)

    def test_pdf_contains_requested_content_without_prices_and_is_tenant_scoped(self):
        created = self.create_order()
        self.client.post(
            f"/api/purchase-orders/{created.data['id']}/finalize/",
            self.payload(),
            format="json",
        )
        pdf_response = self.client.get(f"/api/purchase-orders/{created.data['id']}/pdf/")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        content = pdf_response.content.lower()
        for required in (b"shop one", b"purchase order", b"local supply", b"notebook", b"required quantity", b"confirm product availability"):
            self.assertIn(required, content)
        for forbidden in (b"price", b"cost", b"subtotal", b"tax", b"payment", b"total"):
            self.assertNotIn(forbidden, content)

        self.authenticate(self.other_user)
        self.assertEqual(
            self.client.get(f"/api/purchase-orders/{created.data['id']}/pdf/").status_code,
            404,
        )

    def test_purchase_order_list_is_paginated_twenty_per_page(self):
        self.authenticate()

        for index in range(25):
            PurchaseOrder.objects.create(
                tenant=self.tenant,
                supplier=self.supplier,
                created_by=self.user,
                notes=f"Order {index}",
            )

        response = self.client.get(
            "/api/purchase-orders/?page=1&page_size=20"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])


    def test_subscription_and_module_permissions_are_enforced(self):
        self.authenticate(self.other_user)
        denied_module = self.client.get("/api/purchase-orders/")
        self.assertEqual(denied_module.status_code, 403)

        self.authenticate()
        Subscription.objects.filter(tenant=self.tenant).update(status="EXPIRED")
        denied_subscription = self.client.get("/api/purchase-orders/")
        self.assertEqual(denied_subscription.status_code, 403)