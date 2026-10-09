from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from subscriptions.permissions import IsSubscriptionActive
from users.permissions import HasModuleAccess
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .constants import SystemAccountCodes
from .serializers import (
    AccountSerializer, JournalEntryCreateSerializer,
    JournalEntryDetailSerializer, JournalEntryListSerializer,
    TransactionSerializer,
)
from .services import JournalEntryService, LedgerService, AccountingIntegrationService
from .exceptions import AccountingException
from .notification_handlers import AccountingNotificationService
from .repositories import (
    AccountRepository, JournalEntryRepository,
    JournalEntryLineRepository, AccountTypeRepository,
)


class AccountListAPIView(ListAPIView):
    serializer_class = AccountSerializer
    required_module = "accounting"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def get_queryset(self):
        return AccountRepository.list_by_tenant(self.request.user.tenant)


class JournalEntryListAPIView(ListCreateAPIView):
    required_module = "accounting"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
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

        try:
            entry = JournalEntryService.create_entry(
                tenant=request.user.tenant,
                date=data["date"],
                description=data.get("description", ""),
                lines=data["lines"],
                created_by=request.user,
                auto_post=data.get("auto_post", False),
            )

        except AccountingException as exc:
            AccountingNotificationService.journal_failure(
                tenant=request.user.tenant,
                actor=request.user,
                operation="CREATE",
                error=exc,
            )
            raise

        AccountingNotificationService.schedule_journal_created(
            entry=entry,
            actor=request.user,
            line_count=len(data["lines"]),
            auto_post=data.get("auto_post", False),
        )

        return Response(
            JournalEntryDetailSerializer(entry).data,
            status=status.HTTP_201_CREATED,
        )
class JournalEntryDetailAPIView(APIView):
    required_module = "accounting"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def get(self, request, pk):
        entry = JournalEntryRepository.get_by_id(pk, request.user.tenant)
        return Response(JournalEntryDetailSerializer(entry).data)

class JournalEntryPostAPIView(APIView):
    required_module = "accounting"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def post(self, request, pk):
        try:
            entry = JournalEntryService.post_entry(
                pk,
                request.user.tenant,
            )

        except AccountingException as exc:
            AccountingNotificationService.journal_failure(
                tenant=request.user.tenant,
                actor=request.user,
                operation="POST",
                error=exc,
                entry_id=pk,
            )
            raise

        AccountingNotificationService.schedule_journal_posted(
            entry=entry,
            actor=request.user,
        )

        return Response(
            JournalEntryDetailSerializer(entry).data
        )


class JournalEntryVoidAPIView(APIView):
    required_module = "accounting"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def post(self, request, pk):
        try:
            entry = JournalEntryService.void_entry(
                pk,
                request.user.tenant,
            )

        except AccountingException as exc:
            AccountingNotificationService.journal_failure(
                tenant=request.user.tenant,
                actor=request.user,
                operation="VOID",
                error=exc,
                entry_id=pk,
            )
            raise

        AccountingNotificationService.schedule_journal_voided(
            entry=entry,
            actor=request.user,
        )

        return Response(
            JournalEntryDetailSerializer(entry).data
        )

class TrialBalanceAPIView(APIView):
    required_module = "accounting"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def get(self, request):
        data = LedgerService.trial_balance(request.user.tenant)
        return Response(data)


class TransactionAPIView(APIView):
    required_module = "accounting"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = dict(serializer.validated_data)
        transaction_type = data.pop("transaction_type")

        try:
            entry = AccountingIntegrationService.record_transaction(
                tenant=request.user.tenant,
                user=request.user,
                transaction_type=transaction_type,
                **data,
            )

        except AccountingException as exc:
            AccountingNotificationService.manual_transaction_failure(
                tenant=request.user.tenant,
                actor=request.user,
                transaction_type=transaction_type,
                error=exc,
                amount=data.get("amount"),
                payment_method=data.get("payment_method"),
            )
            raise

        AccountingNotificationService.schedule_manual_transaction_recorded(
            entry=entry,
            actor=request.user,
            transaction_type=transaction_type,
            amount=data.get("amount"),
            payment_method=data.get("payment_method"),
        )

        return Response(
            JournalEntryDetailSerializer(entry).data,
            status=status.HTTP_201_CREATED,
        )


class LedgerAPIView(ListAPIView):
    required_module = "accounting"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]
    def get(self, request):
        tenant = request.user.tenant
        account_id = request.query_params.get("account")
        account_type = request.query_params.get("account_type")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        supplier = request.query_params.get("supplier")
        accounts = AccountRepository.list_by_tenant(tenant).select_related("parent", "account_type")
        if account_id:
            accounts = accounts.filter(id=account_id)
        if account_type:
            accounts = accounts.filter(account_type__name=account_type.upper())

        if supplier:
            accounts = accounts.filter(
                parent__code=SystemAccountCodes.ACCOUNTS_PAYABLE,
                name__icontains=supplier,
            )
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

        grouped = {}
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
            if not transactions:
                continue

            target = account.parent if account.parent_id else account

            if target.id not in grouped:
                grouped[target.id] = {"account": target, "transactions": []}
            grouped[target.id]["transactions"].extend(transactions)

        result = []
        for entry in grouped.values():
            account = entry["account"]
            txns = sorted(entry["transactions"], key=lambda t: (t["date"], t["reference"]))
            result.append({
                "account": account.name,
                "code": account.code,
                "account_type": account.account_type.name,
                "transactions": txns,
            })
        result.sort(key=lambda r: r["code"])
        return Response(result)
    
class SupplierPayableListAPIView(APIView):
    required_module = "accounting"
    permission_classes = [IsAuthenticated, IsSubscriptionActive, HasModuleAccess]

    def get(self, request):
        tenant = request.user.tenant
        accounts = AccountRepository.list_supplier_payables(tenant)

        result = []
        for account in accounts:
            balance = LedgerService.account_balance(account)
            if balance > 0:
                result.append({
                    "id": account.id,
                    "name": account.name.replace("A/P - ", ""),
                    "code": account.code,
                    "balance": float(balance),
                })
        result.sort(key=lambda r: r["name"])
        return Response(result)