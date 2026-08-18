from users.exceptions import AppException


class InvoiceException(AppException):
    status_code = 400
    message = "Invoice error"


class InvoiceNotFoundException(InvoiceException):
    status_code = 404
    message = "Invoice not found"


class UnauthorizedInvoiceActionException(InvoiceException):
    status_code = 403
    message = "You are not authorized to perform this action on this invoice"


class InvalidInvoiceStateException(InvoiceException):
    status_code = 400
    message = "This action cannot be performed on the invoice in its current state"


class InsufficientStockException(InvoiceException):
    status_code = 400
    message = "Insufficient stock available"


class EmptyInvoiceException(InvoiceException):
    status_code = 400
    message = "Invoice must contain at least one item"