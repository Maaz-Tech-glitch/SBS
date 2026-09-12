from .models import Account, AccountType, JournalEntry, JournalEntryLine
from .exceptions import AccountNotFoundException, JournalEntryNotFoundException



class AccountTypeRepository:
    @staticmethod
    def get_by_name(name):
        return AccountType.objects.get(name=name)

    @staticmethod
    def list_all():
        return AccountType.objects.all()


class AccountRepository:
    @staticmethod
    def get_by_id(account_id, tenant):
        try:
            return Account.objects.get(id=account_id, tenant=tenant)
        except Account.DoesNotExist:
            raise AccountNotFoundException()

    @staticmethod
    def get_locked_by_id(account_id, tenant):
        try:
            return Account.objects.select_for_update().get(id=account_id, tenant=tenant)
        except Account.DoesNotExist:
            raise AccountNotFoundException()

    @staticmethod
    def list_by_tenant(tenant):
        return Account.objects.filter(tenant=tenant).select_related("account_type")

    @staticmethod
    def create(tenant, account_type, code, name, parent=None):
        return Account.objects.create(
            tenant=tenant, account_type=account_type, code=code, name=name, parent=parent
        )
    @staticmethod
    def get_by_code(tenant, code):
        try:
            return Account.objects.get(tenant=tenant, code=code)
        except Account.DoesNotExist:
            raise AccountNotFoundException(
                f"Account with code {code} not found. Run seed_chart_of_accounts first."
            )


class JournalEntryRepository:
    @staticmethod
    def create(tenant, date, description, created_by, source_invoice=None):
        return JournalEntry.objects.create(
            tenant=tenant, date=date, description=description,
            created_by=created_by, source_invoice=source_invoice,
        )

    @staticmethod
    def get_by_id(entry_id, tenant):
        try:
            return (
                JournalEntry.objects
                .prefetch_related("lines__account")
                .get(id=entry_id, tenant=tenant)
            )
        except JournalEntry.DoesNotExist:
            raise JournalEntryNotFoundException()

    @staticmethod
    def get_locked_by_id(entry_id, tenant):
        try:
            return JournalEntry.objects.select_for_update().get(id=entry_id, tenant=tenant)
        except JournalEntry.DoesNotExist:
            raise JournalEntryNotFoundException()

    @staticmethod
    def list_by_tenant(tenant):
        return JournalEntry.objects.filter(tenant=tenant).order_by("-date", "-id")


class JournalEntryLineRepository:
    @staticmethod
    def bulk_create(entry, lines):
        objs = [
            JournalEntryLine(
                entry=entry, account=line["account"],
                debit=line.get("debit", 0), credit=line.get("credit", 0),
                narration=line.get("narration", ""),
            )
            for line in lines
        ]
        return JournalEntryLine.objects.bulk_create(objs)

    @staticmethod
    def get_ledger_for_account(account, start_date=None, end_date=None):
        qs = (
            JournalEntryLine.objects
            .filter(account=account, entry__status="POSTED")
            .select_related("entry")
        )
        if start_date:
            qs = qs.filter(entry__date__gte=start_date)
        if end_date:
            qs = qs.filter(entry__date__lte=end_date)
        return qs.order_by("entry__date", "entry__id")
    

