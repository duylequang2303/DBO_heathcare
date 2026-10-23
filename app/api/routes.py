"""FastAPI routes cho Week 10.

Endpoints (theo TASK_WEEK10.md):
  GET  /api/health
  GET  /api/profiles
  POST /api/targets
  POST /api/menu/generate
  POST /api/menu/swap        ← swap.py (Cương) — stub ở đây
  GET  /api/foods
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query

from .schemas import (
    FoodItem,
    GenerateIn,
    MenuOut,
    ProfileIn,
    SwapIn,
    SwapOut,
    TargetsOut,
)
from .services import (
    PRESET_PROFILES,
    generate_menu,
    get_targets,
    search_foods,
)

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Profiles presets (P1 / P2 / P3)
# ---------------------------------------------------------------------------


@router.get("/profiles", tags=["profile"])
async def list_profiles():
    """Trả 3 preset profile P1/P2/P3 cho frontend điền sẵn."""
    return PRESET_PROFILES


# ---------------------------------------------------------------------------
# Targets: nhận hồ sơ → trả BMR/TDEE/macro
# ---------------------------------------------------------------------------


@router.post("/targets", response_model=TargetsOut, tags=["nutrition"])
async def compute_targets(profile: ProfileIn) -> TargetsOut:
    """Tính BMR, TDEE, và mục tiêu dinh dưỡng từ hồ sơ người dùng."""
    return await asyncio.to_thread(get_targets, profile)


# ---------------------------------------------------------------------------
# Menu generate
# ---------------------------------------------------------------------------


@router.post("/menu/generate", response_model=MenuOut, tags=["menu"])
async def api_generate_menu(req: GenerateIn) -> MenuOut:
    """Chạy IDBO two-tier solver → trả menu + dinh dưỡng + vi phạm."""
    return await asyncio.to_thread(generate_menu, req)


# ---------------------------------------------------------------------------
# Menu swap  (stub — Cương implements swap.py)
# ---------------------------------------------------------------------------


@router.post("/menu/swap", response_model=SwapOut, tags=["menu"])
async def api_swap_menu(req: SwapIn) -> SwapOut:
    """Thay 1 món trong slot → tối ưu lại khẩu phần → trả menu mới + delta."""
    try:
        from .swap import swap_menu_item
    except ImportError:
        raise HTTPException(status_code=501, detail="swap.py chưa được triển khai")
    return await asyncio.to_thread(swap_menu_item, req)


# ---------------------------------------------------------------------------
# Food search
# ---------------------------------------------------------------------------


@router.get("/foods", response_model=list[FoodItem], tags=["food"])
async def api_search_foods(
    q: str = Query(default="", description="Từ khóa tìm kiếm"),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[FoodItem]:
    """Tìm kiếm món ăn trong cơ sở dữ liệu."""
    return await asyncio.to_thread(search_foods, q, limit)
