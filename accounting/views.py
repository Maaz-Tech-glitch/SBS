from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from subscriptions.permissions import IsSubscriptionActive
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .serializers import (
    AccountSerializer, JournalEntryCreateSerializer,
    JournalEntryDetailSerializer, JournalEntryListSerializer,
    TransactionSerializer,
)
from .services import JournalEntryService, LedgerService, AccountingIntegrationService
from .repositories import (
    AccountRepository, JournalEntryRepository,
    JournalEntryLineRepository, AccountTypeRepository,
)


class AccountListAPIView(ListAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def get_queryset(self):
        return AccountRepository.list_by_tenant(self.request.user.tenant)


class JournalEntryListAPIView(ListCreateAPIView):
    """
    GET  -> saari journal entries (filterable)
    POST -> nayi raw journal entry create karta hai (rare/custom cases ke liye)
    """
    permission_classes = [IsAuthenticated, IsSubscriptionActive]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "status": ["exact"],
        "date": ["gte", "lte"],
    }
    search_fields = ["reference", "description"]
    ordering_fields = ["date", "id"]
    ordering = ["-date"]

    def get_serializer_class(self):
        return JournalEntryCreateSerializer if self.request.method == "POST" else JournalEntryListSerializer

    def get_queryset(self):
        return JournalEntryRepository.list_by_tenant(self.request.user.tenant)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        entry = JournalEntryService.create_entry(
            tenant=request.user.tenant,
            date=data["date"],
            description=data.get("description", ""),
            lines=data["lines"],
            created_by=request.user,
            auto_post=data.get("auto_post", False),
        )
        return Response(JournalEntryDetailSerializer(entry).data, status=status.HTTP_201_CREATED)


class JournalEntryDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def get(self, request, pk):
        entry = JournalEntryRepository.get_by_id(pk, request.user.tenant)
        return Response(JournalEntryDetailSerializer(entry).data)


class JournalEntryPostAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def post(self, request, pk):
        entry = JournalEntryService.post_entry(pk, request.user.tenant)
        return Response(JournalEntryDetailSerializer(entry).data)


class JournalEntryVoidAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def post(self, request, pk):
        entry = JournalEntryService.void_entry(pk, request.user.tenant)
        return Response(JournalEntryDetailSerializer(entry).data)


class TrialBalanceAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def get(self, request):
        data = LedgerService.trial_balance(request.user.tenant)
        return Response(data)


class TransactionAPIView(APIView):
    """
    Single RESTful endpoint for common day-to-day accounting transactions
    (Owner Investment, Owner Drawings, Expense Payment, Purchase, Sale...) — Strategy pattern.
    """
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        transaction_type = data.pop("transaction_type")

        entry = AccountingIntegrationService.record_transaction(
            tenant=request.user.tenant, user=request.user,
            transaction_type=transaction_type, **data,
        )
        return Response(JournalEntryDetailSerializer(entry).data, status=status.HTTP_201_CREATED)


class LedgerAPIView(ListAPIView):
    """
    Sab transactions dikhata hai, filters se kisi bhi account/category tak narrow kar sakte hain.
    ?account=<id>  ?account_type=ASSET|LIABILITY|EQUITY|REVENUE|EXPENSE
    ?start_date=YYYY-MM-DD  ?end_date=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def get(self, request):
        tenant = request.user.tenant
        account_id = request.query_params.get("account")
        account_type = request.query_params.get("account_type")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        accounts = AccountRepository.list_by_tenant(tenant)
        if account_id:
            accounts = accounts.filter(id=account_id)
        if account_type:
            accounts = accounts.filter(account_type__name=account_type.upper())

        result = []
        for account in accounts:
            lines = JournalEntryLineRepository.get_ledger_for_account(account, start_date, end_date)
            transactions = [
                {
                    "date": l.entry.date, "reference": l.entry.reference,
                    "description": l.entry.description,
                    "debit": l.debit, "credit": l.credit, "narration": l.narration,
                }
                for l in lines
            ]
            if transactions:
                result.append({
                    "account": account.name,
                    "code": account.code,
                    "account_type": account.account_type.name,
                    "transactions": transactions,
                })
        return Response(result)