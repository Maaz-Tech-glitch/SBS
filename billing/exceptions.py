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

class SaleReturnException(InvoiceException):
    status_code = 400
    message = "Sale return error"


class ReturnNotAllowedException(SaleReturnException):
    status_code = 400
    message = "Only completed invoices can be returned"


class InvalidReturnQuantityException(SaleReturnException):
    status_code = 400
    message = "Invalid return quantity"


class ReturnItemNotFoundException(SaleReturnException):
    status_code = 400
    message = "One or more selected invoice items are invalid"


class ReturnRequestConflictException(SaleReturnException):
    status_code = 409
    message = "This return request ID is already being used for another invoice"

