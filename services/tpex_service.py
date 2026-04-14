import httpx

from config import TPEX_QUOTE_URL, to_roc_date
from services.rate_limiter import twse_rate_limiter


async def fetch_tpex_ranking(date_str: str) -> list[dict]:
    """Fetch TPEX OTC stocks daily data for a given date (YYYY-MM-DD).
    Returns list of {code, name, open, high, low, close, change, change_pct, volume}.
    """
    await twse_rate_limiter.acquire()

    roc_date = to_roc_date(date_str)
    params = {"l": "zh-tw", "d": roc_date, "_": "1"}

    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        resp = await client.get(TPEX_QUOTE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    # TPEX returns data in tables[0]["data"], not aaData
    tables = data.get("tables", [])
    rows = tables[0]["data"] if tables and "data" in tables[0] else []
    if not rows:
        return []

    results = []
    for row in rows:
        try:
            result = _parse_tpex_row(row)
            if result:
                results.append(result)
        except (ValueError, IndexError):
            continue

    return results


def _parse_tpex_row(row: list) -> dict | None:
    """Parse a single row from TPEX tables[0]["data"].
    Fields: [代號, 名稱, 收盤, 漲跌, 開盤, 最高, 最低, 均價,
             成交股數, 成交金額(元), 成交筆數, ...]
    """
    code = str(row[0]).strip()
    name = str(row[1]).strip()

    # Only 4-digit stock codes
    if not code.isdigit() or len(code) != 4:
        return None

    close = _parse_number(row[2])
    open_ = _parse_number(row[4])
    high = _parse_number(row[5])
    low = _parse_number(row[6])
    volume = _parse_number(row[8])  # 成交股數 is at index 8

    if close is None or close == 0 or volume is None or volume == 0:
        return None

    change_val = _parse_number(row[3])
    if change_val is None:
        change_val = 0.0

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
        "market": "上櫃",
    }


def _parse_number(s) -> float | None:
    """Parse a number string, removing commas. Returns None for invalid values."""
    s = str(s).strip().replace(",", "")
    if not s or s == "--" or s == "---" or s.startswith("X"):
        return None
    try:
        return float(s)
    except ValueError:
        return None
