import asyncio

from fastapi import APIRouter, Query

from config import KLINE_DAYS
from services.sector_service import get_all_codes
from services.kline_service import fetch_kline
from services.path_service import build_kline_paths

router = APIRouter()


@router.get("/batch-kline")
async def get_batch_kline(
    symbols: str = Query(..., description="Comma-separated stock codes, e.g. 2330,2317"),
    days: int = Query(default=KLINE_DAYS, ge=1, le=500),
):
    codes = await get_all_codes()
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]

    async def fetch_one(symbol: str) -> tuple[str, dict | None]:
        info = codes.get(symbol, {})
        market = info.get("market", "上市")
        try:
            data = await fetch_kline(symbol, market, days)
            paths = build_kline_paths(data)
            return symbol, paths
        except Exception:
            return symbol, None

    results = await asyncio.gather(*[fetch_one(s) for s in symbol_list])
    return {symbol: paths for symbol, paths in results if paths is not None}
