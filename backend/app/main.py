import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.middleware import LocalUploadMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.extraction_slots = asyncio.Semaphore(settings.max_concurrent_extractions)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", docs_url="/docs", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_middleware(LocalUploadMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
app.include_router(api_router, prefix="/api")

frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
# backend/app/main.py -> backend -> repo (parents[2])
if frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    async def frontend() -> FileResponse:
        return FileResponse(frontend_dist / "index.html")
