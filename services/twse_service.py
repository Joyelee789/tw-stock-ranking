import httpx

from config import TWSE_MI_INDEX_URL, to_twse_date
from services.rate_limiter import twse_rate_limiter


async def fetch_twse_ranking(date_str: str) -> list[dict]:
    """Fetch TWSE listed stocks daily data for a given date (YYYY-MM-DD).
    Returns list of {code, name, open, high, low, close, change, change_pct, volume}.
    """
    await twse_rate_limiter.acquire()

    params = {
        "response": "json",
        "date": to_twse_date(date_str),
        "type": "ALLBUT0999",
    }

    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        resp = await client.get(TWSE_MI_INDEX_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    # Find the table containing individual stock data
    tables = data.get("tables", [])
    stock_table = None
    for t in tables:
        title = t.get("title", "")
        if "每日收盤行情" in title:
            stock_table = t
            break

    if not stock_table:
        return []

    results = []
    for row in stock_table.get("data", []):
        try:
            result = _parse_twse_row(row)
            if result:
                results.append(result)
        except (ValueError, IndexError):
            continue

    return results


def _parse_twse_row(row: list) -> dict | None:
    """Parse a single row from MI_INDEX table.
    Fields: [證券代號, 證券名稱, 成交股數, 成交筆數, 成交金額,
             開盤價, 最高價, 最低價, 收盤價, 漲跌(+/-), 漲跌價差,
             最後揭示買價, 最後揭示買量, 最後揭示賣價, 最後揭示賣量, 本益比]
    """
    code = row[0].strip()
    name = row[1].strip()

    # Only 4-digit stock codes
    if not code.isdigit() or len(code) != 4:
        return None

    close = _parse_number(row[8])
    open_ = _parse_number(row[5])
    high = _parse_number(row[6])
    low = _parse_number(row[7])
    volume = _parse_number(row[2])

    if close is None or close == 0 or volume is None or volume == 0:
        return None

    # Parse change direction and value
    direction = row[9].strip()  # "+" or "-" or " "
    change_val = _parse_number(row[10])
    if change_val is None:
        change_val = 0.0

    if "-" in direction:
        change_val = -change_val

    prev_close = close - change_val
    change_pct = (change_val / prev_close * 100) if prev_close != 0 else 0.0

    return {
        "code": code,
        "name": name,
        "open": open_ or 0,
        "high": high or 0,
        "low": low or 0,
        "close": close,
        "change": round(change_val, 2),
        "change_pct": round(change_pct, 2),
        "volume": int(volume),
        "market": "上市",
    }


def _parse_number(s: str) -> float | None:
    """Parse a number string, removing commas. Returns None for invalid values."""
    s = s.strip().replace(",", "")
    if not s or s == "--" or s.startswith("X"):
        return None
    try:
        return float(s)
    except ValueError:
        return None
