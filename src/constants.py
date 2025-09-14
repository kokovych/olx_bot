import os

from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

# --- Category IDs ---
REAL_ESTATE_BUY_HOUSE = 1602
REAL_ESTATE_BUY_APPARTMENT = 1758

# --- Currency options ---
CURRENCY_UAH = "UAH"
CURRENCY_USD = "USD"
CURRENCY_EUR = "EUR"

# --- Price options ---
PRICE_FROM_OPTIONS = [
    ("немає", ""),
    ("10 000", "10000"),
    ("20 000", "20000"),
    ("30 000", "30000"),
    ("50 000", "50000"),
    ("100 000", "100000"),
]

PRICE_TO_OPTIONS = [
    ("немає", ""),
    ("30 000", "30000"),
    ("50 000", "50000"),
    ("60 000", "60000"),
    ("70 000", "70000"),
    ("100 000", "100000"),
    ("1 000 000", "1000000"),
]
