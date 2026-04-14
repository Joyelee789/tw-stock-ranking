import logging
import os
import ssl
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

import config
from routers import ranking, kline, sectors, batch_kline

DISABLE_SSL = os.environ.get("DISABLE_SSL_VERIFY", "").strip() == "1"
if DISABLE_SSL:
    os.environ["PYTHONHTTPSVERIFY"] = "0"
    os.environ["CURL_CA_BUNDLE"] = ""
    ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger("uvicorn.error")


async def _preload_sectors():
    """Background task to preload sector codes without blocking startup."""
    try:
        from services.sector_service import get_all_codes
        await get_all_codes()
        logger.info("Sector codes loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to preload sector codes: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    config.CACHE_DIR.mkdir(exist_ok=True)
    config.KLINE_CACHE_DIR.mkdir(exist_ok=True)
    asyncio.create_task(_preload_sectors())
    yield


app = FastAPI(title="台股漲幅排行", lifespan=lifespan)


class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


app.add_middleware(NoCacheStaticMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ranking.router, prefix="/api")
app.include_router(kline.router, prefix="/api")
app.include_router(sectors.router, prefix="/api")
app.include_router(batch_kline.router, prefix="/api")

@app.get("/")
async def root():
    return FileResponse(config.BASE_DIR / "static" / "index.html")


@app.get("/mobile")
async def mobile():
    return FileResponse(config.BASE_DIR / "static" / "mobile.html")


app.mount("/static", StaticFiles(directory=config.BASE_DIR / "static"), name="static")
