"""Discrete food selection module for Mixed-Integer Two-Tier Optimization.

Maps continuous decision variables z_i in [0, 1) into discrete food_ids
selected from candidate pools for each meal slot.
"""

from __future__ import annotations

import numpy as np

from src.models.food_sampler import MEAL_ORDER, candidates_for_meal
from src.models.dish_category import DishRole, classify_dish_role, is_raw_or_industrial_junk
from src.models.user_profile import UserProfile


def _is_user_facing_food(food: dict) -> bool:
    """Return whether a record is suitable as a standalone menu item.

    Source nutrition rows are preserved. The filter only controls the
    user-facing search space and rejects records already classified as raw or
    industrial ingredients.
    """
    name = str(food.get("food_name", ""))
    category = str(food.get("category", ""))
    return bool(name.strip()) and not is_raw_or_industrial_junk(name, category)


def _roles_for_slot(meal_name: str, slot_idx: int, count: int) -> set[DishRole]:
    """Practical role choices for the small 2+2+2+1 web menu layout."""
    if meal_name == "snack":
        return {DishRole.FRUIT_SNACK, DishRole.BEVERAGE}
    if meal_name == "breakfast":
        if slot_idx == 0:
            return {DishRole.STAPLE}
        return {DishRole.MAIN_PROTEIN, DishRole.FRUIT_SNACK}
    if slot_idx == 0:
        return {DishRole.STAPLE}
    return {DishRole.MAIN_PROTEIN, DishRole.VEGETABLE, DishRole.SOUP}


def build_meal_pools(
    food_map: dict,
    meal_counts: dict[str, int],
    profile: UserProfile,
    min_pool_size: int = 20,
) -> dict[str, list[str]]:
    """Build deterministic, user-facing and role-aware candidate pools.

    The original CSV is not modified. Allergy/dislike and meal-type filtering
    happens first, then raw ingredients are removed, and finally each slot is
    assigned realistic culinary roles. If role classification is too sparse,
    the function safely falls back to the cleaned meal pool, never to raw
    ingredients.
    """
    pools: dict[str, list[str]] = {}
    for meal_name in MEAL_ORDER:
        count = meal_counts.get(meal_name, 0)
        if count <= 0:
            continue
        meal_candidates = sorted(set(candidates_for_meal(food_map, meal_name, profile)))
        cleaned = [fid for fid in meal_candidates if _is_user_facing_food(food_map[fid])]
        if len(cleaned) < min_pool_size:
            raise ValueError(
                f"User-facing pool for '{meal_name}' has size {len(cleaned)}, "
                f"less than min_pool_size={min_pool_size}."
            )
        for slot_idx in range(count):
            allowed_roles = _roles_for_slot(meal_name, slot_idx, count)
            role_candidates = []
            for fid in cleaned:
                food = food_map[fid]
                role = classify_dish_role(
                    str(food.get("food_name", "")),
                    str(food.get("category", "")),
                    str(food.get("source", "vietnamese")),
                )
                if role in allowed_roles:
                    role_candidates.append(fid)
            selected = role_candidates if len(role_candidates) >= min_pool_size else cleaned
            pools[f"{meal_name}_{slot_idx}"] = selected
    return pools


def get_meal_order_slots(meal_counts: dict[str, int]) -> list[str]:
    """Generate ordered list of meal slot names according to MEAL_ORDER."""
    slots = []
    for meal_name in MEAL_ORDER:
        count = meal_counts.get(meal_name, 0)
        for i in range(count):
            slots.append(f"{meal_name}_{i}")
    return slots


def decode_food_selection(
    z: np.ndarray,
    pools: dict[str, list[str]],
    meal_order: list[str],
) -> list[str]:
    """Decode a mixed-integer food selection vector using linear probing.

    For each slot i, the initial index is floor(clamp(z_i, 0, 1-eps) * N).
    If the candidate was already selected in the same meal, scan cyclically
    until an unused ID is found. Complexity per slot is O(N) worst case.
    Different meals may reuse a food ID; the 7-day diversity constraint is
    handled separately by diversity_penalty().

    Args:
        z: 1D array of shape (k,) with values in [0, 1).
        pools: Mapping from slot name to candidate list of food_ids.
        meal_order: Ordered list of slot names corresponding to elements of z.

    Returns:
        List of selected food_ids matching the order of meal_order.

    Raises:
        ValueError: If len(z) != len(meal_order) or a slot has an empty pool.
    """
    z = np.asarray(z)
    if z.ndim != 1:
        raise ValueError("z must be a one-dimensional vector.")
    if not np.all(np.isfinite(z)):
        raise ValueError("z must contain only finite values.")
    if len(z) != len(meal_order):
        raise ValueError(
            f"Length mismatch: z has length {len(z)}, but meal_order has length {len(meal_order)}."
        )

    selected_food_ids: list[str] = []
    # Track used foods per meal prefix (e.g. 'breakfast', 'lunch') to avoid intra-meal duplicates
    used_per_meal: dict[str, set[str]] = {}

    for i, slot_name in enumerate(meal_order):
        pool = pools.get(slot_name, [])
        if not pool:
            raise ValueError(f"Pool for slot '{slot_name}' is empty or missing.")

        meal_prefix = slot_name.rsplit("_", 1)[0]
        if meal_prefix not in used_per_meal:
            used_per_meal[meal_prefix] = set()

        pool_len = len(pool)
        # Clamp finite optimizer coordinates to [0, 1). This also supports
        # slight boundary overshoot from numerical optimization.
        z_val = float(np.clip(z[i], 0.0, 1.0 - 1e-12))
        base_idx = int(z_val * pool_len) % pool_len

        # Linear probing to avoid duplicates within the same meal
        chosen_fid = None
        for offset in range(pool_len):
            cand_idx = (base_idx + offset) % pool_len
            cand_fid = pool[cand_idx]
            if cand_fid not in used_per_meal[meal_prefix]:
                chosen_fid = cand_fid
                break

        # Never silently re-use a food within the same meal.
        if chosen_fid is None:
            raise ValueError(
                f"Not enough unique food_ids for meal '{meal_prefix}' "
                f"at slot '{slot_name}'."
            )

        used_per_meal[meal_prefix].add(chosen_fid)
        selected_food_ids.append(chosen_fid)

    return selected_food_ids
