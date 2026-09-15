from django.urls import path
from .views import (
    AccountListAPIView, JournalEntryListAPIView,
    JournalEntryDetailAPIView, JournalEntryPostAPIView, JournalEntryVoidAPIView,
    TrialBalanceAPIView, TransactionAPIView, LedgerAPIView , SupplierPayableListAPIView,
)

urlpatterns = [
    path("accounts/", AccountListAPIView.as_view(), name="account-list"),
    path("journal-entries/", JournalEntryListAPIView.as_view(), name="journal-entry-list-create"),
    path("journal-entries/<int:pk>/", JournalEntryDetailAPIView.as_view(), name="journal-entry-detail"),
    path("journal-entries/<int:pk>/post/", JournalEntryPostAPIView.as_view(), name="journal-entry-post"),
    path("journal-entries/<int:pk>/void/", JournalEntryVoidAPIView.as_view(), name="journal-entry-void"),
    path("trial-balance/", TrialBalanceAPIView.as_view(), name="trial-balance"),
    path("transactions/", TransactionAPIView.as_view(), name="record-transaction"),
    path("ledger/", LedgerAPIView.as_view(), name="ledger"),
    path("supplier-payable/", SupplierPayableListAPIView.as_view(), name="supplier-payable"),
]