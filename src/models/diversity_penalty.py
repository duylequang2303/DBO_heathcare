"""Penalty for repeated main dishes across a seven-day menu plan.

Only lunch_0 and dinner_0 are main dishes. Pass meal_order explicitly when
working with full daily food vectors; otherwise the function expects exactly
two main-dish IDs per day (lunch, dinner), including in history.
"""
from __future__ import annotations

import math

MAIN_SLOTS = ("lunch_0", "dinner_0")


def _main_dishes(food_ids: list[str], meal_order: list[str] | None) -> list[str]:
    if meal_order is None:
        if len(food_ids) != 2:
            raise ValueError("Without meal_order, each day must contain exactly two main dishes")
        return list(food_ids)
    if len(food_ids) != len(meal_order):
        raise ValueError("food_ids and meal_order must have equal lengths")
    if len(set(meal_order)) != len(meal_order):
        raise ValueError("meal_order contains duplicate slots")
    missing = [slot for slot in MAIN_SLOTS if slot not in meal_order]
    if missing:
        raise ValueError(f"Missing main-dish slots: {missing}")
    return [food_ids[meal_order.index(slot)] for slot in MAIN_SLOTS]


def diversity_penalty(
    day_food_ids: list[str],
    history_food_ids: list[list[str]],
    penalty_weight: float = 10.0,
    lookback_days: int = 2,
    *,
    meal_order: list[str] | None = None,
) -> float:
    """Return weight times repeated main-dish occurrences in recent days.

    Each occurrence is counted against each historical day, so a dish present
    on both previous days contributes twice. The history must use the same
    slot order as the current day when meal_order is provided.
    """
    if not math.isfinite(penalty_weight) or penalty_weight < 0:
        raise ValueError("penalty_weight must be finite and non-negative")
    if isinstance(lookback_days, bool) or not isinstance(lookback_days, int) or lookback_days < 0:
        raise ValueError("lookback_days must be a non-negative integer")
    current = _main_dishes(day_food_ids, meal_order)
    if lookback_days == 0:
        return 0.0
    duplicates = 0
    for previous in history_food_ids[-lookback_days:]:
        previous_main = set(_main_dishes(previous, meal_order))
        duplicates += sum(fid in previous_main for fid in current)
    return float(penalty_weight * duplicates)
