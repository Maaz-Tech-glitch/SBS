from rest_framework import serializers
from .models import AccountType, Account, JournalEntry, JournalEntryLine
class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = ["id", "name", "normal_balance"]

class AccountSerializer(serializers.ModelSerializer):
    account_type_name = serializers.CharField(source="account_type.name", read_only=True)
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ["id", "code", "name", "account_type", "account_type_name", "parent", "is_active", "balance"]
        read_only_fields = ["id"]

    def get_balance(self, obj):
        from .services import LedgerService
        return float(LedgerService.account_balance(obj))
class JournalEntryLineInputSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    debit = serializers.DecimalField(max_digits=14, decimal_places=2, default=0, min_value=0)
    credit = serializers.DecimalField(max_digits=14, decimal_places=2, default=0, min_value=0)
    narration = serializers.CharField(required=False, allow_blank=True, max_length=255)

class JournalEntryCreateSerializer(serializers.Serializer):
    date = serializers.DateField()
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)
    lines = JournalEntryLineInputSerializer(many=True)
    auto_post = serializers.BooleanField(default=False)


class JournalEntryLineOutputSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source="account.name", read_only=True)
    account_code = serializers.CharField(source="account.code", read_only=True)
    class Meta:
        model = JournalEntryLine
        fields = ["id", "account", "account_name", "account_code", "debit", "credit", "narration"]
        
class JournalEntryDetailSerializer(serializers.ModelSerializer):
    lines = JournalEntryLineOutputSerializer(many=True, read_only=True)
    class Meta:
        model = JournalEntry
        fields = ["id", "reference", "date", "description", "status", "lines", "created_at"]
class JournalEntryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = ["id", "reference", "date", "description", "status", "created_at"]
        
class TransactionSerializer(serializers.Serializer):
    transaction_type = serializers.ChoiceField(
        choices=["OWNER_INVESTMENT", "OWNER_DRAWINGS", "EXPENSE_PAYMENT", "PURCHASE", "SUPPLIER_PAYMENT"]
    )
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0.01)
    paid_amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, min_value=0)
    account_id = serializers.IntegerField(required=False, allow_null=True)  
    supplier_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    payment_method = serializers.ChoiceField(choices=["CASH", "CARD", "ONLINE"], default="CASH")
    expense_type = serializers.ChoiceField(choices=["RENT", "SALARY", "ELECTRICITY", "INTERNET"], required=False)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)
