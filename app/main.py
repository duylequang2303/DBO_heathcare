"""FastAPI app entry point — Week 10.
Khởi động:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
Phục vụ cả API lẫn static files trên một cổng (tránh CORS + cấu hình proxy).
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.api.services import get_food_map  # warm-up lazy singleton
# ---------------------------------------------------------------------------
# Lifespan: warm-up food_map singleton on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Nạp food_map vào RAM khi app khởi động — không load mỗi request."""
    import asyncio
    await asyncio.to_thread(get_food_map)
    print("[startup] Food database loaded.")
    yield
# ---------------------------------------------------------------------------
# App khởi tạo
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DBO Healthcare Menu API",
    description="Hệ thống đề xuất thực đơn dinh dưỡng cá nhân hóa bằng IDBO (Tuần 10)",
    version="1.0.0",
    lifespan=lifespan,
)
# Gắn API router
app.include_router(router)
# Serve static files (frontend của Đăng)
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
