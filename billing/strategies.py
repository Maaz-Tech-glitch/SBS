from abc import ABC, abstractmethod
from decimal import Decimal


class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, gross_amount, discount):
        pass

    @abstractmethod
    def display(self, discount):
        pass


class PercentageDiscount(DiscountStrategy):
    def apply(self, gross_amount, discount):
        discount = min(max(discount, Decimal("0.00")), Decimal("100"))
        return gross_amount - ((gross_amount * discount) / Decimal("100"))

    def display(self, discount):
        return f"{discount}%"


class FixedDiscount(DiscountStrategy):
    def apply(self, gross_amount, discount):
        discount = max(discount, Decimal("0.00"))
        discount = min(discount, gross_amount)
        return gross_amount - discount

    def display(self, discount):
        return f"Rs. {discount}"


class DiscountFactory:
    _strategies = {
        "PERCENTAGE": PercentageDiscount(),
        "FIXED": FixedDiscount(),
    }

    @classmethod
    def register(cls, name, strategy):
        cls._strategies[name] = strategy

    @classmethod
    def get(cls, discount_type):
        return cls._strategies.get(discount_type, PercentageDiscount())