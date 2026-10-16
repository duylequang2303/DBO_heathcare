"""Meal Structure and Slot-Based Composition Module.

Defines the culinary composition of balanced meals (e.g., Staple + Main Protein + Vegetable/Soup)
to prevent unpalatable combinations (such as eating two dry pastas or 100g egg powder).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.models.dish_category import (
    DishRole,
    classify_dish_role,
    get_role_portion_bounds,
    is_raw_or_industrial_junk,
)
from src.models.food_sampler import MEAL_ORDER, _is_blocked_food
from src.models.user_profile import UserProfile


@dataclass
class MealSlot:
    """Represents a specific slot within a meal requiring a particular culinary role."""

    slot_name: str                   # e.g., 'lunch_staple', 'lunch_protein'
    meal_name: str                   # 'breakfast', 'lunch', 'dinner', 'snack'
    slot_index: int                  # 0, 1, 2...
    primary_role: DishRole           # e.g., DishRole.STAPLE
    allowed_roles: list[DishRole] = field(default_factory=list)
    min_portion_g: float = 50.0
    max_portion_g: float = 250.0

    def __post_init__(self) -> None:
        if not self.allowed_roles:
            self.allowed_roles = [self.primary_role]
        bounds = get_role_portion_bounds(self.primary_role)
        self.min_portion_g = bounds[0]
        self.max_portion_g = bounds[1]


# Standard slot composition templates for Vietnamese and balanced dining
DEFAULT_MEAL_TEMPLATES: dict[str, list[tuple[DishRole, list[DishRole]]]] = {
    "breakfast": [
        (DishRole.STAPLE, [DishRole.STAPLE]),
        (DishRole.MAIN_PROTEIN, [DishRole.MAIN_PROTEIN, DishRole.FRUIT_SNACK]),
        (DishRole.FRUIT_SNACK, [DishRole.FRUIT_SNACK, DishRole.BEVERAGE]),
    ],
    "lunch": [
        (DishRole.STAPLE, [DishRole.STAPLE]),
        (DishRole.MAIN_PROTEIN, [DishRole.MAIN_PROTEIN]),
        (DishRole.VEGETABLE, [DishRole.VEGETABLE, DishRole.SOUP]),
        (DishRole.SOUP, [DishRole.SOUP, DishRole.VEGETABLE]),
        (DishRole.FRUIT_SNACK, [DishRole.FRUIT_SNACK]),
    ],
    "dinner": [
        (DishRole.STAPLE, [DishRole.STAPLE]),
        (DishRole.MAIN_PROTEIN, [DishRole.MAIN_PROTEIN]),
        (DishRole.VEGETABLE, [DishRole.VEGETABLE, DishRole.SOUP]),
        (DishRole.SOUP, [DishRole.SOUP, DishRole.VEGETABLE]),
        (DishRole.FRUIT_SNACK, [DishRole.FRUIT_SNACK]),
    ],
    "snack": [
        (DishRole.FRUIT_SNACK, [DishRole.FRUIT_SNACK, DishRole.BEVERAGE]),
        (DishRole.MAIN_PROTEIN, [DishRole.FRUIT_SNACK, DishRole.MAIN_PROTEIN]),
    ],
}


def create_meal_slots(meal_counts: dict[str, int]) -> list[MealSlot]:
    """Generate structured meal slots matching meal_counts.

    For example, if meal_counts={"lunch": 2}, slots generated are:
      - lunch_0: primary role STAPLE
      - lunch_1: primary role MAIN_PROTEIN
    """
    slots: list[MealSlot] = []

    for meal_name in MEAL_ORDER:
        count = meal_counts.get(meal_name, 0)
        if count <= 0:
            continue

        template = DEFAULT_MEAL_TEMPLATES.get(meal_name, [])
        for i in range(count):
            slot_name = f"{meal_name}_{i}"
            if i < len(template):
                primary_role, allowed_roles = template[i]
            else:
                # Fallback for extra dishes: allow vegetables or protein
                primary_role = DishRole.VEGETABLE
                allowed_roles = [DishRole.VEGETABLE, DishRole.SOUP, DishRole.MAIN_PROTEIN]

            slots.append(
                MealSlot(
                    slot_name=slot_name,
                    meal_name=meal_name,
                    slot_index=i,
                    primary_role=primary_role,
                    allowed_roles=allowed_roles,
                )
            )

    return slots


def build_structured_pools(
    food_map: dict,
    slots: list[MealSlot],
    profile: UserProfile,
    min_pool_size: int = 5,
) -> dict[str, list[str]]:
    """Build candidate food pools for each structured meal slot filtered by culinary role.

    Excludes raw industrial junk and items violating allergies/dislikes.
    """
    pools: dict[str, list[str]] = {}

    for slot in slots:
        cands: list[str] = []

        for food_id, row in food_map.items():
            food_name = str(row.get("food_name", ""))
            category = str(row.get("category", ""))
            source = str(row.get("source", "vietnamese"))

            # 1. Filter out raw industrial junk
            if is_raw_or_industrial_junk(food_name, category):
                continue

            # 2. Filter out allergies & dislikes
            if _is_blocked_food(food_name, profile):
                continue

            # 3. Check role matching
            role = row.get("dish_role")
            if not isinstance(role, DishRole):
                role = classify_dish_role(food_name, category, source)

            if role in slot.allowed_roles:
                cands.append(food_id)

        # Fallback if filtered pool is too small: relax to any non-junk candidate
        if len(cands) < min_pool_size:
            for food_id, row in food_map.items():
                food_name = str(row.get("food_name", ""))
                category = str(row.get("category", ""))
                if not is_raw_or_industrial_junk(food_name, category) and not _is_blocked_food(food_name, profile):
                    cands.append(food_id)

        pools[slot.slot_name] = sorted(set(cands))

    return pools
