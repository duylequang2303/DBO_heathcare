"""FastAPI app entry point — Week 10.
Khởi động:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
Phục vụ cả API lẫn static files trên một cổng (tránh CORS + cấu hình proxy).
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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
_FIELD_LABELS = {
    "name": "Họ tên",
    "age": "Tuổi",
    "gender": "Giới tính",
    "height_cm": "Chiều cao",
    "weight_kg": "Cân nặng",
    "activity_level": "Mức độ hoạt động",
    "goal": "Mục tiêu",
    "meal_counts": "Số món mỗi bữa",
    "medical_conditions": "Bệnh lý",
    "allergies": "Dị ứng",
    "dislikes": "Không thích",
    "seed": "Seed",
    "config": "Cấu hình solver",
    "food_ids": "Danh sách món",
    "slot": "Slot bữa",
    "new_food_id": "Món thay thế",
    "old_portions_g": "Khẩu phần cũ",
    "profile": "Hồ sơ",
}


def _loc_label(loc: list) -> str:
    parts = [str(x) for x in loc if x not in {"body", "query", "path"}]
    if not parts:
        return "Dữ liệu"
    last = parts[-1]
    return _FIELD_LABELS.get(last, last)


def _translate_422_msg(msg: str, loc: list) -> str:
    label = _loc_label(loc)
    low = (msg or "").lower()
    if "field required" in low:
        return f"Thiếu trường {label}"
    if "greater than or equal to" in low:
        return f"{label} phải lớn hơn hoặc bằng giá trị tối thiểu"
    if "less than or equal to" in low:
        return f"{label} phải nhỏ hơn hoặc bằng giá trị tối đa"
    if "greater than" in low:
        return f"{label} phải lớn hơn 0"
    if "valid integer" in low:
        return f"{label} phải là số nguyên"
    if "valid number" in low or "valid float" in low:
        return f"{label} phải là số"
    if "input should be" in low:
        return f"{label} không hợp lệ"
    return f"{label}: {msg}"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for err in exc.errors():
        loc = list(err.get("loc") or [])
        details.append({
            "loc": loc,
            "msg": _translate_422_msg(str(err.get("msg") or ""), loc),
            "type": err.get("type"),
        })
    return JSONResponse(status_code=422, content={"detail": details})


# Gắn API router
app.include_router(router)
# Serve static files (frontend của Đăng)
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
