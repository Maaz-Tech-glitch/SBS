from users.exceptions import AppException


class AccountingException(AppException):
    status_code = 400
    message = "Accounting error"


class AccountNotFoundException(AccountingException):
    status_code = 404
    message = "Account not found"


class JournalEntryNotFoundException(AccountingException):
    status_code = 404
    message = "Journal entry not found"


class UnbalancedJournalEntryException(AccountingException):
    status_code = 400
    message = "Journal entry is not balanced: total debit must equal total credit"


class EmptyJournalEntryException(AccountingException):
    status_code = 400
    message = "Journal entry must contain at least two lines"


class JournalEntryAlreadyPostedException(AccountingException):
    status_code = 409
    message = "This journal entry is already posted and cannot be modified"
    
class InsufficientBalanceException(AccountingException):
    status_code = 400
    message = "Insufficient balance in the selected account to complete this transaction"