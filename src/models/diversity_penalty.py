"""Diversity penalty for repeated main dishes across a weekly menu plan.

Main dishes are the first lunch (lunch_0) and first dinner (dinner_0) slots.
When working with a full daily food vector, pass ``meal_order`` describing the
slot layout so main dishes can be located by slot name. When working with a
trimmed vector that already contains exactly the two main-dish IDs, ``meal_order``
may be omitted.
"""
from __future__ import annotations

import math

MAIN_SLOTS = ("lunch_0", "dinner_0")


def _main_dishes(food_ids: list[str], meal_order: list[str] | None) -> list[str]:
    if meal_order is None:
        if len(food_ids) != len(MAIN_SLOTS):
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


def calculate_unique_main_dish_pct(
    weekly_food_ids: list[list[str]],
    meal_order: list[str] | None = None,
) -> float:
    """Return the percentage of unique main dishes across a weekly plan.

    Args:
        weekly_food_ids: One food-id sequence per day in the plan.
        meal_order: Slot order matching each daily sequence. Required when the
            daily sequences contain more than the two main dishes.

    Returns:
        float: Percentage in [0.0, 100.0]; 100.0 for an empty plan.
    """
    main_dishes: list[str] = []
    for day in weekly_food_ids:
        main_dishes.extend(_main_dishes(day, meal_order))
    if not main_dishes:
        return 100.0
    return float((len(set(main_dishes)) / len(main_dishes)) * 100.0)
