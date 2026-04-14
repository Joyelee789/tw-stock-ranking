import asyncio

from fastapi import APIRouter, Query
from pydantic import BaseModel

from config import KLINE_DAYS
from services.sector_service import get_all_codes
from services.kline_service import fetch_kline, preload_klines, preload_progress

router = APIRouter()


class PreloadRequest(BaseModel):
    symbols: list[dict]  # [{code, market}, ...]


@router.get("/kline")
async def get_kline(
    symbol: str = Query(..., description="Stock code, e.g. 2330"),
    days: int = Query(default=KLINE_DAYS, ge=1, le=500),
):
    codes = await get_all_codes()
    info = codes.get(symbol, {})
    market = info.get("market", "上市")
    name = info.get("name", "")

    try:
        data = await fetch_kline(symbol, market, days)
    except Exception as e:
        return {"symbol": symbol, "name": name, "days": days, "data": [], "error": str(e)}

    return {"symbol": symbol, "name": name, "sector": info.get("group", ""), "days": days, "data": data}


@router.post("/kline/preload")
async def preload(request: PreloadRequest):
    if preload_progress.get("running"):
        return {"status": "already_running", **preload_progress}

    asyncio.create_task(preload_klines(request.symbols))
    return {"status": "started", "total": len(request.symbols)}


@router.get("/kline/progress")
async def get_progress():
    return preload_progress
