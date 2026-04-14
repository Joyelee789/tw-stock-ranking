import logging

import httpx

from config import TWSE_MI_INDEX_URL, TWSE_STOCK_DAY_ALL_URL, to_twse_date
from services.rate_limiter import twse_rate_limiter

logger = logging.getLogger("uvicorn.error")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


async def fetch_twse_ranking(date_str: str) -> list[dict]:
    """Fetch TWSE listed stocks daily data.
    Tries OpenData API first (works from overseas), falls back to MI_INDEX.
    """
    try:
        return await _fetch_via_opendata()
    except Exception as e:
        logger.warning(f"TWSE OpenData failed, trying MI_INDEX: {e}")

    return await _fetch_via_mi_index(date_str)


async def _fetch_via_opendata() -> list[dict]:
    """Fetch from openapi.twse.com.tw (reliable from overseas)."""
    async with httpx.AsyncClient(timeout=20, verify=False, headers=_HEADERS) as client:
        resp = await client.get(TWSE_STOCK_DAY_ALL_URL)
        resp.raise_for_status()
        rows = resp.json()

    results = []
    for row in rows:
        try:
            result = _parse_opendata_row(row)
            if result:
                results.append(result)
        except (ValueError, KeyError):
            continue

    logger.info(f"TWSE OpenData: fetched {len(results)} stocks")
    return results


async def _fetch_via_mi_index(date_str: str) -> list[dict]:
    """Fallback: fetch from MI_INDEX (may not work from overseas)."""
    await twse_rate_limiter.acquire()

    params = {
        "response": "json",
        "date": to_twse_date(date_str),
        "type": "ALLBUT0999",
    }

    async with httpx.AsyncClient(timeout=20, verify=False, headers={
        **_HEADERS,
        "Referer": "https://www.twse.com.tw/zh/trading/historical/mi-index.html",
    }) as client:
        resp = await client.get(TWSE_MI_INDEX_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

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


def _parse_opendata_row(row: dict) -> dict | None:
    """Parse a row from TWSE OpenData STOCK_DAY_ALL."""
    code = str(row.get("Code", "")).strip()
    name = str(row.get("Name", "")).strip()

    if not code.isdigit() or len(code) != 4:
        return None

    close = _safe_float(row.get("ClosingPrice"))
    open_ = _safe_float(row.get("OpeningPrice"))
    high = _safe_float(row.get("HighestPrice"))
    low = _safe_float(row.get("LowestPrice"))
    volume = _safe_float(row.get("TradeVolume"))
    change_val = _safe_float(row.get("Change"))

    if close is None or close == 0 or volume is None or volume == 0:
        return None
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
        "market": "上市",
    }


def _parse_twse_row(row: list) -> dict | None:
    """Parse a single row from MI_INDEX table."""
    code = row[0].strip()
    name = row[1].strip()

    if not code.isdigit() or len(code) != 4:
        return None

    close = _parse_number(row[8])
    open_ = _parse_number(row[5])
    high = _parse_number(row[6])
    low = _parse_number(row[7])
    volume = _parse_number(row[2])

    if close is None or close == 0 or volume is None or volume == 0:
        return None

    direction = row[9].strip()
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


def _safe_float(val) -> float | None:
    """Parse a value to float, handling empty strings and commas."""
    if val is None:
        return None
    s = str(val).strip().replace(",", "")
    if not s or s in ("--", "---"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_number(s: str) -> float | None:
    """Parse a number string, removing commas. Returns None for invalid values."""
    s = s.strip().replace(",", "")
    if not s or s == "--" or s.startswith("X"):
        return None
    try:
        return float(s)
    except ValueError:
        return None
