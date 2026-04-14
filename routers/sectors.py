from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Query

from config import CACHE_DIR, DEFAULT_TOP_N
from services.cache_manager import read_cache
from services.sector_service import get_all_codes, get_sector_list

router = APIRouter()


@router.get("/sectors")
async def get_sectors():
    codes = await get_all_codes()
    sectors = get_sector_list(codes)
    return {"sectors": sectors}


@router.get("/sector-stats")
async def get_sector_stats(
    date_str: str = Query(default=None, alias="date", description="YYYY-MM-DD"),
    top: int = Query(default=DEFAULT_TOP_N, ge=1, le=500),
):
    if date_str is None:
        date_str = date.today().isoformat()

    cache_path = CACHE_DIR / f"ranking_{date_str.replace('-', '')}.json"
    cached = read_cache(cache_path)

    if not cached or not cached.get("data"):
        return {"date": date_str, "stats": [], "message": "請先載入排行資料"}

    stocks = cached["data"][:top]

    # Group by sector
    sector_groups = defaultdict(list)
    for s in stocks:
        sector = s.get("sector", "其他")
        sector_groups[sector].append(s["change_pct"])

    stats = []
    for sector, pcts in sector_groups.items():
        stats.append({
            "sector": sector,
            "count": len(pcts),
            "avg_change_pct": round(sum(pcts) / len(pcts), 2),
        })

    stats.sort(key=lambda x: x["count"], reverse=True)
    return {"date": date_str, "stats": stats}
