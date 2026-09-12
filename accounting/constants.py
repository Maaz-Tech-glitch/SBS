class SystemAccountCodes:
    CASH = "1001"
    BANK = "1002"
    ACCOUNTS_RECEIVABLE = "1003"
    INVENTORY = "1004"
    ACCOUNTS_PAYABLE = "2001"
    OWNER_CAPITAL = "3001"
    OWNER_DRAWINGS = "3002"
    SALES_REVENUE = "4001"
    RENT_EXPENSE = "5001"
    SALARY_EXPENSE = "5002"
    ELECTRICITY_EXPENSE = "5003"
    INTERNET_EXPENSE = "5004"


PAYMENT_METHOD_ACCOUNT_MAP = {
    "CASH": SystemAccountCodes.CASH,
    "CARD": SystemAccountCodes.BANK,
    "ONLINE": SystemAccountCodes.BANK,
}

DEFAULT_ACCOUNT_TYPES = [
    ("ASSET", "DEBIT"),
    ("LIABILITY", "CREDIT"),
    ("EQUITY", "CREDIT"),
    ("REVENUE", "CREDIT"),
    ("EXPENSE", "DEBIT"),
]

DEFAULT_ACCOUNTS = {
    "ASSET": [
        ("1001", "Cash"), ("1002", "Bank"), ("1003", "Accounts Receivable"),
        ("1004", "Inventory"), ("1005", "Furniture & Equipment"),
    ],
    "LIABILITY": [
        ("2001", "Accounts Payable"), ("2002", "Loan Payable"), ("2003", "Tax Payable"),
    ],
    "EQUITY": [
        ("3001", "Owner Capital"), ("3002", "Owner Drawings"),
    ],
    "REVENUE": [
        ("4001", "Sales Revenue"), ("4002", "Service Revenue"),
    ],
    "EXPENSE": [
        ("5001", "Rent Expense"), ("5002", "Salary Expense"),
        ("5003", "Electricity Expense"), ("5004", "Internet Expense"),
    ],
}