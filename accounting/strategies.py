from abc import ABC, abstractmethod
from .constants import SystemAccountCodes, PAYMENT_METHOD_ACCOUNT_MAP
from .repositories import AccountRepository
from .exceptions import AccountingException

class TransactionStrategy(ABC):
    @abstractmethod
    def build(self, tenant, data):
        pass
    @staticmethod
    def _cash_or_bank(tenant, payment_method):
        code = PAYMENT_METHOD_ACCOUNT_MAP.get(payment_method, SystemAccountCodes.CASH)
        return AccountRepository.get_by_code(tenant, code)

class SaleStrategy(TransactionStrategy):
    def build(self, tenant, data):
        invoice = data["invoice"]
        cash_or_bank = self._cash_or_bank(tenant, invoice.payment_method)
        sales_revenue = AccountRepository.get_by_code(tenant, SystemAccountCodes.SALES_REVENUE)
        lines = [
            {"account_id": cash_or_bank.id, "debit": invoice.final_amount, "credit": 0,
            "narration": f"Received via {invoice.payment_method}"},
            {"account_id": sales_revenue.id, "debit": 0, "credit": invoice.final_amount,
            "narration": "Sales revenue"},
        ]
        return f"Sale - Invoice {invoice.invoice_number}", lines, invoice
class PurchaseStrategy(TransactionStrategy):
    def build(self, tenant, data):
        inventory = AccountRepository.get_by_code(tenant, SystemAccountCodes.INVENTORY)
        total_amount = data["amount"]
        paid_amount = data.get("paid_amount", total_amount)
        supplier_name = data.get("supplier_name")
        if paid_amount > total_amount:
            raise AccountingException("Paid amount cannot exceed total purchase amount.")
        remaining = total_amount - paid_amount
        lines = [
            {"account_id": inventory.id, "debit": total_amount, "credit": 0, "narration": "Stock purchased"},
        ]
        if paid_amount > 0:
            cash_or_bank = self._cash_or_bank(tenant, data.get("payment_method", "CASH"))
            lines.append({
                "account_id": cash_or_bank.id, "debit": 0, "credit": paid_amount,
                "narration": f"Paid via {data.get('payment_method', 'CASH')}",
            })
        if remaining > 0:
            if not supplier_name:
                raise AccountingException("supplier_name is required when purchase is not fully paid.")
            payable_account = AccountRepository.get_or_create_supplier_payable(tenant, supplier_name)
            lines.append({
                "account_id": payable_account.id, "debit": 0, "credit": remaining,
                "narration": f"Amount payable to {supplier_name}",
            })
        desc = data.get("description") or (
            f"Purchase from {supplier_name}" if supplier_name else "Inventory purchase"
        )
        return desc, lines, None
class OwnerInvestmentStrategy(TransactionStrategy):
    def build(self, tenant, data):
        cash_or_bank = self._cash_or_bank(tenant, data.get("payment_method", "CASH"))
        owner_capital = AccountRepository.get_by_code(tenant, SystemAccountCodes.OWNER_CAPITAL)
        amount = data["amount"]
        lines = [
            {"account_id": cash_or_bank.id, "debit": amount, "credit": 0, "narration": "Cash invested by owner"},
            {"account_id": owner_capital.id, "debit": 0, "credit": amount, "narration": "Owner capital contribution"},
        ]
        return data.get("description") or "Owner capital investment", lines, None


class OwnerDrawingsStrategy(TransactionStrategy):
    def build(self, tenant, data):
        cash_or_bank = self._cash_or_bank(tenant, data.get("payment_method", "CASH"))
        owner_drawings = AccountRepository.get_by_code(tenant, SystemAccountCodes.OWNER_DRAWINGS)
        amount = data["amount"]
        lines = [
            {"account_id": owner_drawings.id, "debit": amount, "credit": 0, "narration": "Owner withdrawal"},
            {"account_id": cash_or_bank.id, "debit": 0, "credit": amount, "narration": "Cash paid to owner"},
        ]
        return data.get("description") or "Owner drawings", lines, None


class ExpensePaymentStrategy(TransactionStrategy):
    EXPENSE_CODE_MAP = {
        "RENT": SystemAccountCodes.RENT_EXPENSE,
        "SALARY": SystemAccountCodes.SALARY_EXPENSE,
        "ELECTRICITY": SystemAccountCodes.ELECTRICITY_EXPENSE,
        "INTERNET": SystemAccountCodes.INTERNET_EXPENSE,
    }

    def build(self, tenant, data):
        expense_type = data["expense_type"]
        expense_code = self.EXPENSE_CODE_MAP.get(expense_type)
        if not expense_code:
            raise AccountingException(f"Unknown expense_type: {expense_type}")

        cash_or_bank = self._cash_or_bank(tenant, data.get("payment_method", "CASH"))
        expense_account = AccountRepository.get_by_code(tenant, expense_code)
        amount = data["amount"]
        lines = [
            {"account_id": expense_account.id, "debit": amount, "credit": 0, "narration": f"{expense_type} expense"},
            {"account_id": cash_or_bank.id, "debit": 0, "credit": amount,
            "narration": f"Paid via {data.get('payment_method', 'CASH')}"},
        ]
        return data.get("description") or f"{expense_type.title()} expense payment", lines, None

class OpeningStockStrategy(TransactionStrategy):
        def build(self, tenant, data):
            inventory = AccountRepository.get_by_code(tenant, SystemAccountCodes.INVENTORY)
            owner_capital = AccountRepository.get_by_code(tenant, SystemAccountCodes.OWNER_CAPITAL)
            amount = data["amount"]
            lines = [
                {"account_id": inventory.id, "debit": amount, "credit": 0, "narration": "Opening stock recorded"},
                {"account_id": owner_capital.id, "debit": 0, "credit": amount, "narration": "Existing stock as capital"},
            ]
            return data.get("description") or "Opening stock", lines, None

class SupplierPaymentStrategy(TransactionStrategy):
    def build(self, tenant, data):
        from .services import LedgerService 
        account_id = data.get("account_id")
        supplier_name = data.get("supplier_name")
        if account_id:
            payable_account = AccountRepository.get_by_id(account_id, tenant)
            supplier_label = payable_account.name.replace("A/P - ", "")
        elif supplier_name:
            payable_account = AccountRepository.get_or_create_supplier_payable(tenant, supplier_name)
            supplier_label = supplier_name
        else:
            raise AccountingException("Supplier payment ke liye 'account_id' ya 'supplier_name' lazmi hai.")

        amount = data["amount"]
        outstanding = LedgerService.account_balance(payable_account)
        if amount > outstanding:
            raise AccountingException(
                f"Payment amount (Rs. {amount}) exceeds outstanding balance "
                f"for {supplier_label} (Rs. {outstanding})."
            )

        cash_or_bank = self._cash_or_bank(tenant, data.get("payment_method", "CASH"))
        lines = [
            {"account_id": payable_account.id, "debit": amount, "credit": 0,
            "narration": f"Payment to {supplier_label}"},
            {"account_id": cash_or_bank.id, "debit": 0, "credit": amount,
            "narration": f"Paid via {data.get('payment_method', 'CASH')}"},
        ]
        return f"Supplier payment - {supplier_label}", lines, None
    
class TransactionStrategyFactory:
    _strategies = {
        "SALE": SaleStrategy(),
        "PURCHASE": PurchaseStrategy(),
        "SUPPLIER_PAYMENT": SupplierPaymentStrategy(), 
        "OWNER_INVESTMENT": OwnerInvestmentStrategy(),
        "OWNER_DRAWINGS": OwnerDrawingsStrategy(),
        "EXPENSE_PAYMENT": ExpensePaymentStrategy(),
        "OPENING_STOCK": OpeningStockStrategy(),
    }
    @classmethod
    def register(cls, name, strategy):
        cls._strategies[name] = strategy
    @classmethod
    def get(cls, transaction_type):
        strategy = cls._strategies.get(transaction_type)
        if not strategy:
            raise AccountingException(f"Unsupported transaction_type: {transaction_type}")
        return strategy
    