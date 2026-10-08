"""Discrete food selection module for Mixed-Integer Two-Tier Optimization.

Maps continuous decision variables z_i in [0, 1) into discrete food_ids
selected from candidate pools for each meal slot.
"""

from __future__ import annotations

import numpy as np

from src.models.food_sampler import MEAL_ORDER, candidates_for_meal
from src.models.user_profile import UserProfile


def build_meal_pools(
    food_map: dict,
    meal_counts: dict[str, int],
    profile: UserProfile,
    min_pool_size: int = 20,
) -> dict[str, list[str]]:
    """Build candidate food pools for each meal slot, filtered by meal_type and allergies.

    Args:
        food_map: Dictionary of available food items keyed by food_id.
        meal_counts: Mapping from meal name ('breakfast', 'lunch', etc.) to item count.
        profile: User profile containing allergies and dislikes.
        min_pool_size: Minimum required size for each candidate pool.

    Returns:
        Dictionary mapping each meal slot (e.g. 'breakfast_0', 'lunch_0') to its list of candidate food_ids.

    Raises:
        ValueError: If candidate pool size for any requested meal is less than min_pool_size.
    """
    pools: dict[str, list[str]] = {}

    for meal_name in MEAL_ORDER:
        count = meal_counts.get(meal_name, 0)
        if count <= 0:
            continue

        cands = candidates_for_meal(food_map, meal_name, profile)
        # Ensure deterministic ordering across runs
        cands = sorted(set(cands))

        if len(cands) < min_pool_size:
            raise ValueError(
                f"Candidate pool for '{meal_name}' has size {len(cands)}, "
                f"which is less than min_pool_size={min_pool_size}."
            )

        for slot_idx in range(count):
            slot_name = f"{meal_name}_{slot_idx}"
            pools[slot_name] = list(cands)

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
