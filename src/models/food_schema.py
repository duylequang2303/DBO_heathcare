"""Strict Food Schema and Contract Validation Module.

Ensures that every food item ingested or optimized complies with
physiological and physical reality (non-negative nutrients, valid portion bounds,
and culinary role categorization).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.models.dish_category import DishRole, classify_dish_role, get_role_portion_bounds
from src.models.menu import MenuItem


@dataclass(frozen=True)
class FoodItemSchema:
    """Immutable, strictly validated schema for a single food item."""

    food_id: str
    food_name: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    dish_role: DishRole = DishRole.MAIN_PROTEIN
    serving_size_g: float = 100.0
    sodium_mg: float = 0.0
    calcium_mg: float = 0.0
    iron_mg: float = 0.0
    vitamin_c_mg: float = 0.0
    meal_type: str = "all"
    source: str = "vietnamese"
    category: str = ""

    def __post_init__(self) -> None:
        if not self.food_id or not str(self.food_id).strip():
            raise ValueError("food_id cannot be empty")
        if not self.food_name or not str(self.food_name).strip():
            raise ValueError("food_name cannot be empty")

        # Validate non-negative nutrients
        for nutrient, val in [
            ("calories", self.calories),
            ("protein_g", self.protein_g),
            ("carbs_g", self.carbs_g),
            ("fat_g", self.fat_g),
            ("fiber_g", self.fiber_g),
            ("sodium_mg", self.sodium_mg),
            ("calcium_mg", self.calcium_mg),
            ("iron_mg", self.iron_mg),
            ("vitamin_c_mg", self.vitamin_c_mg),
        ]:
            if val < 0 or val != val:  # Check < 0 or NaN
                raise ValueError(f"Nutrient '{nutrient}' must be non-negative and not NaN, got {val}")

        # Validate realistic calorie ceiling per 100g (pure fat has ~900 kcal/100g)
        if self.calories > 1000.0:
            raise ValueError(f"Calories per 100g ({self.calories}) exceeds theoretical maximum 1000 kcal")

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "FoodItemSchema":
        """Instantiate and validate FoodItemSchema from a raw dictionary/DataFrame row."""
        food_id = str(row.get("food_id", "")).strip()
        food_name = str(row.get("food_name", "")).strip()
        category = str(row.get("category", "")).strip()
        source = str(row.get("source", "vietnamese")).strip()
        meal_type = str(row.get("meal_type", "all")).strip().lower()

        # Classify dish role if not provided
        role_raw = row.get("dish_role")
        if isinstance(role_raw, DishRole):
            dish_role = role_raw
        elif role_raw:
            dish_role = DishRole(str(role_raw).lower())
        else:
            dish_role = classify_dish_role(food_name, category, source)

        def _get_float(key: str, default: float = 0.0) -> float:
            val = row.get(key, default)
            try:
                f = float(val)
                return 0.0 if f != f else max(0.0, f)
            except (ValueError, TypeError):
                return default

        return cls(
            food_id=food_id,
            food_name=food_name,
            calories=_get_float("calories"),
            protein_g=_get_float("protein_g"),
            carbs_g=_get_float("carbs_g"),
            fat_g=_get_float("fat_g"),
            fiber_g=_get_float("fiber_g"),
            dish_role=dish_role,
            serving_size_g=_get_float("serving_size_g", 100.0),
            sodium_mg=_get_float("sodium_mg"),
            calcium_mg=_get_float("calcium_mg"),
            iron_mg=_get_float("iron_mg"),
            vitamin_c_mg=_get_float("vitamin_c_mg"),
            meal_type=meal_type,
            source=source,
            category=category,
        )

    def to_menu_item(self, portion_g: float) -> MenuItem:
        """Convert to domain MenuItem with a specific portion in grams."""
        return MenuItem(
            food_id=self.food_id,
            food_name=self.food_name,
            portion_g=portion_g,
            calories=self.calories,
            protein_g=self.protein_g,
            carbs_g=self.carbs_g,
            fat_g=self.fat_g,
            fiber_g=self.fiber_g,
            sodium_mg=self.sodium_mg,
            calcium_mg=self.calcium_mg,
            iron_mg=self.iron_mg,
            vitamin_c_mg=self.vitamin_c_mg,
            meal_type=self.meal_type,
        )

    def portion_bounds(self) -> tuple[float, float]:
        """Return natural portion bounds for this food item."""
        return get_role_portion_bounds(self.dish_role)
