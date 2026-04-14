import os

import httpx
from bs4 import BeautifulSoup

from config import TWSE_ISIN_URL, CACHE_DIR, CODES_CACHE_MAX_AGE_DAYS
from services.cache_manager import read_cache, write_cache, is_cache_fresh

_VERIFY_SSL = os.environ.get("DISABLE_SSL_VERIFY", "").strip() != "1"

_CODES_CACHE_PATH = CACHE_DIR / "codes.json"
_codes_cache: dict[str, dict] | None = None


async def get_all_codes() -> dict[str, dict]:
    """Return {code: {name, market, group}} for all listed + OTC stocks."""
    global _codes_cache
    if _codes_cache is not None:
        return _codes_cache

    if is_cache_fresh(_CODES_CACHE_PATH, CODES_CACHE_MAX_AGE_DAYS * 24):
        data = read_cache(_CODES_CACHE_PATH)
        if data:
            _codes_cache = data
            return data

    codes = {}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=_VERIFY_SSL) as client:
        # strMode=2: TWSE listed, strMode=4: TPEX OTC
        for mode, market in [("2", "上市"), ("4", "上櫃")]:
            resp = await client.get(TWSE_ISIN_URL, params={"strMode": mode})
            # ISIN page is Big5 encoded — decode from raw bytes
            html = resp.content.decode("big5", errors="ignore")
            _parse_isin_html(html, market, codes)

    write_cache(_CODES_CACHE_PATH, codes)
    _codes_cache = codes
    return codes


def _parse_isin_html(html: str, market: str, codes: dict):
    """Parse ISIN HTML table and populate codes dict."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="h4")
    if not table:
        return

    current_type = None
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) == 1:
            # Section header row (e.g., "股票", "ETF")
            current_type = cells[0].get_text(strip=True)
            continue
        if current_type != "股票" or len(cells) < 7:
            continue

        code_name = cells[0].get_text(strip=True)
        # Code and name separated by \u3000 (fullwidth space)
        parts = code_name.split("\u3000")
        if len(parts) < 2:
            continue
        code = parts[0].strip()
        name = parts[1].strip()

        # Only 4-digit numeric codes are individual stocks
        if not code.isdigit() or len(code) != 4:
            continue

        group = cells[4].get_text(strip=True) if len(cells) > 4 else ""
        codes[code] = {"name": name, "market": market, "group": group}


def get_sector_list(codes: dict) -> list[str]:
    """Return sorted unique sector names."""
    sectors = sorted({v["group"] for v in codes.values() if v["group"]})
    return sectors
