"""Services layer: bridge tới lõi solver đã có (không viết lại thuật toán).

Module này được Duy hoàn thiện. Phiên bản hiện tại cung cấp:
  - build_profile()     : ProfileIn → UserProfile
  - get_targets()       : ProfileIn → TargetsOut
  - generate_menu()     : GenerateIn → MenuOut
  - search_foods()      : query str → list[FoodItem]

Lazy singleton food_map: nạp một lần khi app khởi động, không load mỗi request.
"""

from __future__ import annotations

import asyncio
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.menu_objective import decode_result
from src.algorithms.two_tier_solver import TwoTierConfig, two_tier_optimize
from src.models.constraints import validate_menu
from src.models.diversity_penalty import calculate_unique_main_dish_pct
from src.models.food_selector import get_meal_order_slots
from src.models.user_profile import (
    ActivityLevel,
    DietType,
    Gender,
    Goal,
    UserProfile,
)
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import calc_bmr, calc_tdee, daily_all_targets
from src.utils.portion_utils import round_portions

from .schemas import (
    FoodItem,
    GenerateIn,
    MacroDict,
    MenuItemOut,
    MenuOut,
    ProfileIn,
    TargetsOut,
)


# ---------------------------------------------------------------------------
# Lazy singleton food map (nạp một lần khi startup)
# ---------------------------------------------------------------------------

_food_map: dict[str, dict] | None = None
_food_df = None


def get_food_map() -> dict[str, dict]:
    """Return food map singleton — lazy load on first call."""
    global _food_map, _food_df
    if _food_map is None:
        _food_df = load_food_db()
        _food_map = build_food_map(_food_df)
    return _food_map


def get_food_df():
    get_food_map()  # ensure loaded
    return _food_df


# ---------------------------------------------------------------------------
# Preset profiles P1 / P2 / P3 (tái dùng từ generate_options_week9.py)
# ---------------------------------------------------------------------------

PRESET_PROFILES = {
    "p1": {
        "name": "Duy",
        "age": 22,
        "gender": "male",
        "height_cm": 170.0,
        "weight_kg": 65.0,
        "activity_level": "MODERATE",
        "goal": "MAINTAIN",
        "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
        "medical_conditions": ["healthy"],
        "allergies": [],
        "dislikes": [],
    },
    "p2": {
        "name": "Lan",
        "age": 45,
        "gender": "female",
        "height_cm": 158.0,
        "weight_kg": 62.0,
        "activity_level": "LIGHT",
        "goal": "LOSE_WEIGHT",
        "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
        "medical_conditions": ["diabetes"],
        "allergies": [],
        "dislikes": [],
    },
    "p3": {
        "name": "Minh",
        "age": 55,
        "gender": "male",
        "height_cm": 168.0,
        "weight_kg": 75.0,
        "activity_level": "SEDENTARY",
        "goal": "MAINTAIN",
        "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
        "medical_conditions": ["hypertension"],
        "allergies": [],
        "dislikes": [],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ACTIVITY_MAP = {
    "SEDENTARY": ActivityLevel.SEDENTARY,
    "LIGHT": ActivityLevel.LIGHT,
    "MODERATE": ActivityLevel.MODERATE,
    "ACTIVE": ActivityLevel.ACTIVE,
    "VERY_ACTIVE": ActivityLevel.VERY_ACTIVE,
}

_GOAL_MAP = {
    "LOSE_WEIGHT": Goal.LOSE_WEIGHT,
    "MAINTAIN": Goal.MAINTAIN,
    "GAIN_WEIGHT": Goal.GAIN_WEIGHT,
}


def build_profile(pin: ProfileIn) -> UserProfile:
    """ProfileIn (Pydantic) → UserProfile (domain)."""
    return UserProfile(
        name=pin.name,
        age=pin.age,
        gender=Gender.MALE if pin.gender == "male" else Gender.FEMALE,
        height_cm=pin.height_cm,
        weight_kg=pin.weight_kg,
        activity_level=_ACTIVITY_MAP[pin.activity_level],
        goal=_GOAL_MAP[pin.goal],
        meal_counts=pin.meal_counts,
        medical_conditions=pin.medical_conditions,
        allergies=pin.allergies,
        dislikes=pin.dislikes,
        diet_type=DietType.STANDARD,
    )


# Backward compatibility alias
profile_in_to_user_profile = build_profile


def _get_targets_with_conditions(profile: UserProfile) -> dict[str, float]:
    """Tính targets + áp điều chỉnh bệnh lý (sodium giảm cho hypertension)."""
    targets = daily_all_targets(profile)
    conditions = {c.strip().lower() for c in profile.medical_conditions}
    if "hypertension" in conditions:
        targets["sodium_mg"] = 1500.0
    return targets


def _menu_item_out(item: Any, slot: str) -> MenuItemOut:
    """Convert MenuItem domain object → MenuItemOut."""
    return MenuItemOut(
        food_id=item.food_id,
        name=item.food_name,
        slot=slot,
        meal_type=item.meal_type or "",
        portion_g=round(item.portion_g, 1),
        portion_g_rounded=int(round_portions(item.portion_g, step=5)),
        macros=MacroDict(
            calories=round(item.calories * item.portion_g / 100, 1),
            protein_g=round(item.protein_g * item.portion_g / 100, 2),
            carbs_g=round(item.carbs_g * item.portion_g / 100, 2),
            fat_g=round(item.fat_g * item.portion_g / 100, 2),
            fiber_g=round(item.fiber_g * item.portion_g / 100, 2),
            sodium_mg=round(item.sodium_mg * item.portion_g / 100, 1),
        ),
    )


def _build_menu_items_out(menu, meal_counts: dict[str, int]) -> list[MenuItemOut]:
    """Convert Menu domain → list[MenuItemOut] với slot name đúng thứ tự."""
    from src.models.menu import MealType
    from src.models.food_selector import MEAL_ORDER as _MEAL_ORDER_STR

    items_out: list[MenuItemOut] = []
    meal_order_str = [m for m in _MEAL_ORDER_STR if meal_counts.get(m, 0) > 0]

    for meal_name in meal_order_str:
        try:
            meal_type_enum = MealType(meal_name)
        except ValueError:
            continue
        meal = menu.meals.get(meal_type_enum)
        if meal is None:
            continue
        for idx, item in enumerate(meal.items):
            slot = f"{meal_name}_{idx}"
            items_out.append(_menu_item_out(item, slot))

    return items_out


def _totals_from_menu(menu) -> dict[str, float]:
    return {
        "calories": round(menu.total("calories"), 1),
        "protein_g": round(menu.total("protein_g"), 2),
        "carbs_g": round(menu.total("carbs_g"), 2),
        "fat_g": round(menu.total("fat_g"), 2),
        "fiber_g": round(menu.total("fiber_g"), 2),
        "sodium_mg": round(menu.total("sodium_mg"), 1),
    }


# ---------------------------------------------------------------------------
# TwoTierConfig presets
# ---------------------------------------------------------------------------

_WEB_CONFIG = dict(outer_n_agents=10, outer_max_iter=25, inner_n_agents=10, inner_max_iter=25)
_SMOKE_CONFIG = dict(outer_n_agents=4, outer_max_iter=5, inner_n_agents=4, inner_max_iter=5)
_FULL_CONFIG = dict(outer_n_agents=20, outer_max_iter=100, inner_n_agents=15, inner_max_iter=50)


def _make_tt_config(config_name: str, seed: int) -> TwoTierConfig:
    kwargs = {"web": _WEB_CONFIG, "smoke": _SMOKE_CONFIG, "full": _FULL_CONFIG}[config_name]
    return TwoTierConfig(outer_algo="idbo", inner_algo="idbo", seed=seed, **kwargs)


# ---------------------------------------------------------------------------
# Service functions (sync, called via asyncio.to_thread from routes)
# ---------------------------------------------------------------------------


def get_targets(pin: ProfileIn) -> TargetsOut:
    """Tính BMR, TDEE, macro/micro targets từ hồ sơ."""
    profile = build_profile(pin)
    bmr = calc_bmr(profile)
    tdee = calc_tdee(profile)
    targets = _get_targets_with_conditions(profile)
    return TargetsOut(bmr=round(bmr, 1), tdee=round(tdee, 1), targets={k: round(v, 2) for k, v in targets.items()})


def generate_menu(req: GenerateIn) -> MenuOut:
    """Chạy two_tier_optimize → decode → validate → trả MenuOut.

    Pipeline đúng theo AGENTS.md:
      continuous solution → round portions 5g → decode → recalc nutrients → validate
    """
    profile = build_profile(req.profile)
    if sum(profile.meal_counts.values()) <= 0:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Cần ít nhất 1 món ăn trong thực đơn để tối ưu.")
    food_map = get_food_map()
    targets = _get_targets_with_conditions(profile)
    config = _make_tt_config(req.config, req.seed)

    res = two_tier_optimize(profile, food_map, targets, config)

    # Round chỉ dùng cho output, optimizer vẫn dùng liên tục
    rounded = round_portions(res.best_portions_g, step=5)
    menu = decode_result(res.best_food_ids, rounded, food_map, profile.meal_counts)
    violations = validate_menu(menu, profile, targets)

    meal_order = get_meal_order_slots(profile.meal_counts)
    diversity_pct = calculate_unique_main_dish_pct([res.best_food_ids], meal_order)

    items_out = _build_menu_items_out(menu, profile.meal_counts)
    totals = _totals_from_menu(menu)

    return MenuOut(
        items=items_out,
        totals=totals,
        targets={k: round(v, 2) for k, v in targets.items()},
        fitness=round(res.best_fitness, 2),
        violations=violations,
        diversity_pct=round(diversity_pct, 1),
        runtime_s=round(res.runtime_s, 2),
    )


def search_foods(q: str, limit: int = 20) -> list[FoodItem]:
    """Tìm kiếm món trong DB theo tên (full-text simple)."""
    df = get_food_df()
    if df is None:
        return []
    q_lower = q.lower().strip()
    if q_lower:
        mask = df["food_name"].str.lower().str.contains(q_lower, na=False, regex=False)
        matched = df[mask].head(limit)
    else:
        matched = df.head(limit)

    results: list[FoodItem] = []
    for _, row in matched.iterrows():
        results.append(
            FoodItem(
                food_id=str(row.get("food_id", "")),
                food_name=str(row.get("food_name", "")),
                calories=float(row.get("calories", 0)),
                protein_g=float(row.get("protein_g", 0)),
                carbs_g=float(row.get("carbs_g", 0)),
                fat_g=float(row.get("fat_g", 0)),
                fiber_g=float(row.get("fiber_g", 0)),
                sodium_mg=float(row.get("sodium_mg", 0)),
                meal_type=str(row.get("meal_type", "")),
            )
        )
    return results
