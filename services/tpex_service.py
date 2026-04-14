import logging

import httpx

from config import TPEX_QUOTE_URL, to_roc_date
from services.rate_limiter import twse_rate_limiter

logger = logging.getLogger("uvicorn.error")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_download.php",
}


async def fetch_tpex_ranking(date_str: str) -> list[dict]:
    """Fetch TPEX OTC stocks daily data for a given date (YYYY-MM-DD).
    Returns empty list on failure (e.g. when called from overseas).
    """
    try:
        return await _fetch_tpex(date_str)
    except Exception as e:
        logger.warning(f"TPEX fetch failed (may be blocked from overseas): {e}")
        return []


async def _fetch_tpex(date_str: str) -> list[dict]:
    await twse_rate_limiter.acquire()

    roc_date = to_roc_date(date_str)
    params = {"l": "zh-tw", "d": roc_date, "_": "1"}

    async with httpx.AsyncClient(timeout=15, verify=False, headers=_HEADERS) as client:
        resp = await client.get(TPEX_QUOTE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

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

    logger.info(f"TPEX: fetched {len(results)} stocks")
    return results


def _parse_tpex_row(row: list) -> dict | None:
    """Parse a single row from TPEX tables[0]["data"]."""
    code = str(row[0]).strip()
    name = str(row[1]).strip()

    if not code.isdigit() or len(code) != 4:
        return None

    close = _parse_number(row[2])
    open_ = _parse_number(row[4])
    high = _parse_number(row[5])
    low = _parse_number(row[6])
    volume = _parse_number(row[8])

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
