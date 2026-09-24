from users.exceptions import AppException


class SubscriptionException(AppException):
    status_code = 400
    message = "Subscription error"


class NoActiveSubscriptionException(SubscriptionException):
    status_code = 403
    message = "No active subscription found for your account. Please subscribe to continue."


class PlanNotFoundException(SubscriptionException):
    status_code = 404
    message = "Plan not found"


class SubscriptionNotFoundException(SubscriptionException):
    status_code = 404
    message = "Subscription not found"


class PaymentFailedException(SubscriptionException):
    status_code = 402
    message = "Payment failed"
    
class NoTenantException(SubscriptionException):
    status_code = 400
    message = "Please complete shop setup before subscribing to a plan"

class SubscriptionAlreadyActiveException(SubscriptionException):
    status_code = 409
    message = "You already have an active subscription. Wait for it to expire before subscribing again."
    
    
class TrialNotAvailableException(SubscriptionException):
    status_code = 400
    message = "Free trial is not available for this plan"


class TrialAlreadyUsedException(SubscriptionException):
    status_code = 409
    message = "You have already used the free trial for this plan"