"""Pydantic request/response schemas cho Week 10 API.

Hợp đồng API (TASK_WEEK10.md):
  POST /api/targets      → TargetsOut
  POST /api/menu/generate → MenuOut
  POST /api/menu/swap    → SwapOut
  GET  /api/foods        → list[FoodItem]
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------


class ProfileIn(BaseModel):
    name: str
    age: int = Field(ge=0, le=120)
    gender: Literal["male", "female"]
    height_cm: float = Field(gt=0, le=250)
    weight_kg: float = Field(gt=0, le=400)
    activity_level: Literal["SEDENTARY", "LIGHT", "MODERATE", "ACTIVE", "VERY_ACTIVE"]
    goal: Literal["LOSE_WEIGHT", "MAINTAIN", "GAIN_WEIGHT"]
    meal_counts: dict[str, int] = Field(
        default={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1}
    )
    medical_conditions: list[str] = []
    allergies: list[str] = []
    dislikes: list[str] = []

    @field_validator("meal_counts")
    @classmethod
    def validate_meal_counts(cls, v: dict[str, int]) -> dict[str, int]:
        allowed_meals = {"breakfast": 5, "lunch": 5, "dinner": 5, "snack": 3}
        for meal, count in v.items():
            if meal not in allowed_meals:
                raise ValueError(f"Bữa ăn '{meal}' không hợp lệ. Chỉ chấp nhận {list(allowed_meals.keys())}")
            max_c = allowed_meals[meal]
            if count < 0 or count > max_c:
                raise ValueError(f"Số món cho '{meal}' phải từ 0 đến {max_c}")
        return v


class GenerateIn(BaseModel):
    profile: ProfileIn
    seed: int = 9001
    config: Literal["smoke", "web", "full"] = "web"


class SwapIn(BaseModel):
    profile: ProfileIn
    food_ids: list[str]
    slot: str          # vd "lunch_0"
    new_food_id: str | None = None   # None → tự chọn món khác cùng pool
    seed: int = 9001


# ---------------------------------------------------------------------------
# Output sub-schemas
# ---------------------------------------------------------------------------


class MacroDict(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float


class MenuItemOut(BaseModel):
    food_id: str
    name: str
    slot: str
    meal_type: str
    portion_g: float        # giá trị liên tục từ solver
    portion_g_rounded: int  # làm tròn bội số 5g (chỉ dùng để hiển thị)
    macros: MacroDict       # dinh dưỡng tính từ portion_g gốc


class TargetsOut(BaseModel):
    bmr: float
    tdee: float
    targets: dict[str, float]   # calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg, …


class MenuOut(BaseModel):
    items: list[MenuItemOut]
    totals: dict[str, float]
    targets: dict[str, float]
    fitness: float
    violations: list[str]
    diversity_pct: float
    runtime_s: float


class SwapOut(BaseModel):
    items: list[MenuItemOut]
    totals: dict[str, float]
    targets: dict[str, float]
    violations: list[str]
    delta: dict[str, float]     # totals_new - totals_old cho từng chỉ số


class FoodItem(BaseModel):
    food_id: str
    food_name: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float
    meal_type: str
