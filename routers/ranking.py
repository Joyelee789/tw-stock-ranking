import asyncio
from datetime import date

from fastapi import APIRouter, Query

from config import CACHE_DIR, DEFAULT_TOP_N
from services.cache_manager import read_cache, write_cache
from services.sector_service import get_all_codes
from services.twse_service import fetch_twse_ranking
from services.tpex_service import fetch_tpex_ranking

router = APIRouter()


@router.get("/ranking")
async def get_ranking(
    date_str: str = Query(default=None, alias="date", description="YYYY-MM-DD"),
    top: int = Query(default=DEFAULT_TOP_N, ge=1, le=500),
):
    if date_str is None:
        date_str = date.today().isoformat()

    cache_path = CACHE_DIR / f"ranking_{date_str.replace('-', '')}.json"
    cached = read_cache(cache_path)
    if cached and isinstance(cached, dict) and cached.get("data"):
        data = cached["data"][:top]
        # Re-rank
        for i, item in enumerate(data, 1):
            item["rank"] = i
        return {"date": date_str, "count": len(data), "data": data}

    # Fetch from TWSE + TPEX concurrently
    try:
        twse_data, tpex_data = await asyncio.gather(
            fetch_twse_ranking(date_str),
            fetch_tpex_ranking(date_str),
        )
    except Exception as e:
        return {"date": date_str, "count": 0, "data": [], "message": f"資料取得失敗: {e}"}

    all_stocks = twse_data + tpex_data
    if not all_stocks:
        return {"date": date_str, "count": 0, "data": [], "message": "非交易日或尚無資料"}

    # Enrich with sector info
    codes = await get_all_codes()
    for stock in all_stocks:
        info = codes.get(stock["code"], {})
        stock["sector"] = info.get("group", "其他")
        if not stock.get("name") and info.get("name"):
            stock["name"] = info["name"]

    # Sort by change_pct descending
    all_stocks.sort(key=lambda x: x["change_pct"], reverse=True)

    # Add rank
    for i, stock in enumerate(all_stocks, 1):
        stock["rank"] = i

    # Cache the full ranking (not just top N)
    write_cache(cache_path, {"date": date_str, "count": len(all_stocks), "data": all_stocks})

    data = all_stocks[:top]
    return {"date": date_str, "count": len(data), "data": data}
