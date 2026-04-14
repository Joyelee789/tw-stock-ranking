import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import yfinance as yf

_DISABLE_SSL = os.environ.get("DISABLE_SSL_VERIFY", "").strip() == "1"
if _DISABLE_SSL:
    from curl_cffi.requests import Session as CurlSession
    _yf_session = CurlSession(verify=False, impersonate="chrome")
else:
    import requests as _requests
    _yf_session = _requests.Session()

from config import KLINE_CACHE_DIR, KLINE_CACHE_MAX_AGE_HOURS, KLINE_DAYS
from services.cache_manager import read_cache, write_cache, is_cache_fresh

_executor = ThreadPoolExecutor(max_workers=5)

# Preload progress tracking
preload_progress = {"total": 0, "completed": 0, "failed": 0, "running": False}


def _fetch_yf_history(ticker: str, days: int) -> list[dict]:
    """Synchronous yfinance fetch — runs in thread pool."""
    period = "1y" if days <= 252 else "2y"
    t = yf.Ticker(ticker, session=_yf_session)
    df = t.history(period=period, interval="1d")

    if df.empty:
        return []

    df = df.tail(days)
    result = []
    for ts, row in df.iterrows():
        result.append({
            "time": ts.strftime("%Y-%m-%d"),
            "open": round(row["Open"], 2),
            "high": round(row["High"], 2),
            "low": round(row["Low"], 2),
            "close": round(row["Close"], 2),
            "volume": int(row["Volume"]),
        })
    return result


async def fetch_kline(symbol: str, market: str, days: int = KLINE_DAYS) -> list[dict]:
    """Fetch K-line data for a stock, with caching."""
    cache_path = KLINE_CACHE_DIR / f"{symbol}.json"

    if is_cache_fresh(cache_path, KLINE_CACHE_MAX_AGE_HOURS):
        cached = read_cache(cache_path)
        if cached and isinstance(cached, dict) and cached.get("data"):
            return cached["data"]

    ticker = f"{symbol}.TW" if market == "上市" else f"{symbol}.TWO"
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(_executor, _fetch_yf_history, ticker, days)

    cache_obj = {
        "symbol": symbol,
        "last_updated": date.today().isoformat(),
        "data": data,
    }
    write_cache(cache_path, cache_obj)
    return data


async def preload_klines(stocks: list[dict]):
    """Batch preload K-line data for multiple stocks."""
    preload_progress["total"] = len(stocks)
    preload_progress["completed"] = 0
    preload_progress["failed"] = 0
    preload_progress["running"] = True

    sem = asyncio.Semaphore(5)

    async def _fetch_one(stock: dict):
        async with sem:
            try:
                await fetch_kline(stock["code"], stock["market"])
                preload_progress["completed"] += 1
            except Exception:
                preload_progress["failed"] += 1
                preload_progress["completed"] += 1

    await asyncio.gather(*[_fetch_one(s) for s in stocks])
    preload_progress["running"] = False
