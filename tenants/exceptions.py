from users.exceptions import AppException


class TenantException(AppException):
    status_code = 400
    message = "Tenant error"


class TenantNotFoundException(TenantException):
    status_code = 404
    message = "Tenant not found"


class TenantAlreadyExistsException(TenantException):
    status_code = 409
    message = "Shop is already set up for this account"