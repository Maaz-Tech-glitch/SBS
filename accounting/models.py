import uuid
from django.db import models
from django.core.exceptions import ValidationError
from tenants.models import Tenant


class AccountType(models.Model):
    """The 5 fundamental categories: Asset, Liability, Equity, Revenue, Expense"""
    NATURE_CHOICES = [
        ("DEBIT", "Debit"),    
        ("CREDIT", "Credit"),  
    ]
    name = models.CharField(max_length=50, unique=True)  # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    normal_balance = models.CharField(max_length=10, choices=NATURE_CHOICES)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Account(models.Model):
    """Individual ledger account e.g. Cash, Bank, Sales Revenue, Rent Expense"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="accounts")
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, related_name="accounts")
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=150)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(models.Model):
    """Header: one business transaction (e.g. 'Cash sale of Rs. 5000')"""
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("POSTED", "Posted"),
        ("VOID", "Void"),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="journal_entries")
    reference = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="DRAFT")
    source_invoice = models.ForeignKey(
        "billing.Invoice", null=True, blank=True, on_delete=models.SET_NULL, related_name="journal_entries"
    )
    created_by = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="journal_entries")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.reference:
            self.reference = f"TEMP-{uuid.uuid4().hex[:10]}"
        super().save(*args, **kwargs)
        if is_new and self.reference.startswith("TEMP-"):
            self.reference = f"JE-{self.pk:06d}"
            super().save(update_fields=["reference"])

    def __str__(self):
        return f"{self.reference} ({self.date}) - {self.status}"


class JournalEntryLine(models.Model):
    """Detail: one debit or one credit line inside a JournalEntry"""
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="entry_lines")
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    narration = models.CharField(max_length=255, blank=True, default="")

    def clean(self):
        if self.debit and self.credit:
            raise ValidationError("A line cannot have both debit and credit amounts.")
        if not self.debit and not self.credit:
            raise ValidationError("A line must have either a debit or a credit amount.")

    def __str__(self):
        return f"{self.account.name}: Dr {self.debit} / Cr {self.credit}"