from pathlib import Path

BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "cache"
KLINE_CACHE_DIR = CACHE_DIR / "kline"

# TWSE API
TWSE_MI_INDEX_URL = "https://www.twse.com.tw/exchangeReport/MI_INDEX"
TWSE_STOCK_DAY_ALL_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

# TPEX API
TPEX_QUOTE_URL = "https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php"

# ISIN (sector codes)
TWSE_ISIN_URL = "https://isin.twse.com.tw/isin/C_public.jsp"

# Rate limit
RATE_LIMIT_REQUESTS = 3
RATE_LIMIT_WINDOW = 5.0  # seconds

# Defaults
DEFAULT_TOP_N = 100
KLINE_DAYS = 240
KLINE_CACHE_MAX_AGE_HOURS = 18
CODES_CACHE_MAX_AGE_DAYS = 7


def to_roc_date(date_str: str) -> str:
    """Convert 'YYYY-MM-DD' to 'YYY/MM/DD' (ROC calendar)."""
    y, m, d = date_str.split("-")
    return f"{int(y) - 1911}/{m}/{d}"


def to_twse_date(date_str: str) -> str:
    """Convert 'YYYY-MM-DD' to 'YYYYMMDD'."""
    return date_str.replace("-", "")
