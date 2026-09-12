from abc import ABC, abstractmethod
from .constants import SystemAccountCodes, PAYMENT_METHOD_ACCOUNT_MAP
from .repositories import AccountRepository
from .exceptions import AccountingException


class TransactionStrategy(ABC):
    @abstractmethod
    def build(self, tenant, data):
        """Returns (description, lines[], source_invoice_or_None)"""
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
        cash_or_bank = self._cash_or_bank(tenant, data.get("payment_method", "CASH"))
        inventory = AccountRepository.get_by_code(tenant, SystemAccountCodes.INVENTORY)
        amount = data["amount"]
        lines = [
            {"account_id": inventory.id, "debit": amount, "credit": 0, "narration": "Stock purchased"},
            {"account_id": cash_or_bank.id, "debit": 0, "credit": amount,
            "narration": f"Paid via {data.get('payment_method', 'CASH')}"},
        ]
        return data.get("description") or "Inventory purchase", lines, None


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
    """Owner ne business se paisa nikala personal use ke liye."""
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

class TransactionStrategyFactory:
    """Naya transaction type add karna ho to bas yahan register karein — endpoint/view nahi badalna."""
    _strategies = {
        "SALE": SaleStrategy(),
        "PURCHASE": PurchaseStrategy(),
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
    
    
    