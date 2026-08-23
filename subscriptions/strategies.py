from abc import ABC, abstractmethod


class PaymentStrategy(ABC):
    @abstractmethod
    def process(self, subscription, **kwargs):
        pass


class ManualPaymentStrategy(PaymentStrategy):
    def process(self, subscription, **kwargs):
        return True


class OnlinePaymentStrategy(PaymentStrategy):
    """TODO: Real gateway (Stripe/JazzCash) yahan integrate hoga - OCP."""
    def process(self, subscription, **kwargs):
        return True


class PaymentStrategyFactory:
    _strategies = {
        "CASH": ManualPaymentStrategy(),
        "CARD": OnlinePaymentStrategy(),
        "ONLINE": OnlinePaymentStrategy(),
    }

    @classmethod
    def register(cls, name, strategy):
        cls._strategies[name] = strategy

    @classmethod
    def get(cls, payment_method):
        strategy = cls._strategies.get(payment_method)
        if not strategy:
            from .exceptions import PaymentFailedException
            raise PaymentFailedException(f"Unsupported payment method: {payment_method}")
        return strategy