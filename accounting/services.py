from decimal import Decimal
from django.db import transaction
from .repositories import (JournalEntryRepository, JournalEntryLineRepository, AccountRepository)
from .exceptions import (
    UnbalancedJournalEntryException, EmptyJournalEntryException,
    JournalEntryAlreadyPostedException,InsufficientBalanceException,
)
from django.utils import timezone
from .constants import SystemAccountCodes
from .constants import DEFAULT_ACCOUNT_TYPES, DEFAULT_ACCOUNTS
from .models import AccountType, Account
from .strategies import TransactionStrategyFactory

class JournalEntryService:
    @staticmethod
    def _validate_balance(lines):
        if len(lines) < 2:
            raise EmptyJournalEntryException("A journal entry needs at least 2 lines (one debit side, one credit side).")
        total_debit = sum((Decimal(str(l["debit"])) for l in lines), Decimal("0.00"))
        total_credit = sum((Decimal(str(l["credit"])) for l in lines), Decimal("0.00"))
        if total_debit != total_credit:
            raise UnbalancedJournalEntryException(
                f"Not balanced: Debit={total_debit}, Credit={total_credit}"
            )
        if total_debit == 0:
            raise UnbalancedJournalEntryException("Entry amount cannot be zero.")
    @staticmethod
    def create_entry(*, tenant, date, description, lines, created_by,
                    source_invoice=None, auto_post=False):
        """
        lines = [
            {"account_id": 1, "debit": 5000, "credit": 0, "narration": "Cash received"},
            {"account_id": 9, "debit": 0, "credit": 5000, "narration": "Sales revenue"},
        ]
        """
        resolved_lines = []
        for line in lines:
            account = AccountRepository.get_by_id(line["account_id"], tenant)
            resolved_lines.append({
                "account": account,
                "debit": line.get("debit", 0),
                "credit": line.get("credit", 0),
                "narration": line.get("narration", ""),
            })
        JournalEntryService._validate_balance(resolved_lines)
        with transaction.atomic():
            entry = JournalEntryRepository.create(
                tenant=tenant, date=date, description=description,
                created_by=created_by, source_invoice=source_invoice,
            )
            JournalEntryLineRepository.bulk_create(entry, resolved_lines)
            if auto_post:
                entry.status = "POSTED"
                entry.save(update_fields=["status", "updated_at"])
            return JournalEntryRepository.get_by_id(entry.id, tenant)

    @staticmethod
    def post_entry(entry_id, tenant):
        with transaction.atomic():
            entry = JournalEntryRepository.get_locked_by_id(entry_id, tenant)
            if entry.status == "POSTED":
                raise JournalEntryAlreadyPostedException()
            entry.status = "POSTED"
            entry.save(update_fields=["status", "updated_at"])
            return entry

    @staticmethod
    def void_entry(entry_id, tenant):
        with transaction.atomic():
            entry = JournalEntryRepository.get_locked_by_id(entry_id, tenant)
            entry.status = "VOID"
            entry.save(update_fields=["status", "updated_at"])
            return entry


class LedgerService:
    @staticmethod
    def account_balance(account, as_of=None):
        """Signed balance according to the account's normal_balance nature."""
        lines = JournalEntryLineRepository.get_ledger_for_account(account, end_date=as_of)
        total_debit = sum((l.debit for l in lines), Decimal("0.00"))
        total_credit = sum((l.credit for l in lines), Decimal("0.00"))
        if account.account_type.normal_balance == "DEBIT":
            return total_debit - total_credit
        return total_credit - total_debit

    @staticmethod
    def trial_balance(tenant):
            from .repositories import AccountRepository
            accounts = AccountRepository.list_by_tenant(tenant).select_related("parent", "account_type")
            totals = {}
            for account in accounts:
                lines = JournalEntryLineRepository.get_ledger_for_account(account)
                debit_total = sum((l.debit for l in lines), Decimal("0.00"))
                credit_total = sum((l.credit for l in lines), Decimal("0.00"))
                if not debit_total and not credit_total:
                    continue
                target = account.parent if account.parent_id else account
                if target.id not in totals:
                    totals[target.id] = {"account": target, "debit": Decimal("0.00"), "credit": Decimal("0.00")}
                totals[target.id]["debit"] += debit_total
                totals[target.id]["credit"] += credit_total
            result = []
            for entry in sorted(totals.values(), key=lambda e: e["account"].code):
                account = entry["account"]
                net_balance = (
                    entry["debit"] - entry["credit"] if account.account_type.normal_balance == "DEBIT"
                    else entry["credit"] - entry["debit"]
                )
                result.append({
                    "account": account.name, "code": account.code,
                    "debit_total": entry["debit"], "credit_total": entry["credit"],
                    "balance": net_balance,
                })
            return result
            

class AccountingIntegrationService:
    @staticmethod
    def record_transaction(tenant, user, transaction_type, **data):
        strategy = TransactionStrategyFactory.get(transaction_type)
        description, lines, source_invoice = strategy.build(tenant, data)
        AccountingIntegrationService._validate_sufficient_balance(tenant, lines)
        return JournalEntryService.create_entry(
            tenant=tenant,
            date=timezone.now().date(),
            description=data.get("description") or description,
            created_by=user,
            source_invoice=source_invoice,
            auto_post=True,
            lines=lines,
        )
    @staticmethod
    def _validate_sufficient_balance(tenant, lines):
        for line in lines:
            credit_amount = line.get("credit") or 0
            if not credit_amount:
                continue
            account = AccountRepository.get_by_id(line["account_id"], tenant)
            if account.account_type.normal_balance == "DEBIT":  # Asset/Expense accounts
                current_balance = LedgerService.account_balance(account)
                if current_balance < credit_amount:
                    raise InsufficientBalanceException(
                        f"Insufficient balance in {account.name}: available Rs.{current_balance}, required Rs.{credit_amount}"
                    )

class ChartOfAccountsSeederService:
    @staticmethod
    def seed_defaults(tenant):
        for name, nature in DEFAULT_ACCOUNT_TYPES:
            acc_type, _ = AccountType.objects.get_or_create(
                name=name, defaults={"normal_balance": nature}
            )
            for code, acc_name in DEFAULT_ACCOUNTS[name]:
                Account.objects.get_or_create(
                    tenant=tenant, code=code,
                    defaults={"account_type": acc_type, "name": acc_name},
                )