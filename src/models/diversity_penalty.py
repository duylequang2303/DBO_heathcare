"""Diversity Penalty Module for Weekly Menu Planning.

Penalizes repeated main dishes across consecutive days within a configurable
lookback window (e.g. 2 days) to ensure meal variety in 7-day meal plans.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple


def diversity_penalty(
    day_food_ids: Sequence[str],
    history_food_ids: Sequence[Sequence[str]] | None,
    penalty_weight: float = 10.0,
    lookback_days: int = 2,
    main_dish_indices: Tuple[int, ...] = (2, 4),
) -> float:
    """Compute penalty for duplicate main dishes within lookback days.

    Args:
        day_food_ids: List of food_ids assigned for the current day.
        history_food_ids: List of daily food_ids from previous days.
        penalty_weight: Multiplier penalty per repeated main dish.
        lookback_days: Number of recent past days to check for duplicates.
        main_dish_indices: Indices in day_food_ids representing main dishes
                           (default: indices 2 and 4 for lunch_0 and dinner_0).

    Returns:
        float: Non-negative penalty value (0.0 if all main dishes are unique).
    """
    if not history_food_ids or not day_food_ids or penalty_weight <= 0:
        return 0.0

    recent_history = history_food_ids[-lookback_days:]

    # Collect past main dishes within the lookback window
    past_main_dishes: set[str] = set()
    for past_day in recent_history:
        for idx in main_dish_indices:
            if idx < len(past_day):
                past_main_dishes.add(past_day[idx])

    # Count violations for current day main dishes
    n_violations = 0
    for idx in main_dish_indices:
        if idx < len(day_food_ids):
            item_id = day_food_ids[idx]
            if item_id in past_main_dishes:
                n_violations += 1

    return float(n_violations * penalty_weight)


def calculate_unique_main_dish_pct(
    weekly_food_ids: Sequence[Sequence[str]],
    main_dish_indices: Tuple[int, ...] = (2, 4),
) -> float:
    """Calculate the percentage of unique main dishes across a weekly plan.

    Args:
        weekly_food_ids: 7-day list of daily food_id sequences.
        main_dish_indices: Indices representing main dishes.

    Returns:
        float: Percentage of unique main dishes in range [0.0, 100.0].
    """
    total_slots = 0
    all_main_dishes: list[str] = []

    for day in weekly_food_ids:
        for idx in main_dish_indices:
            if idx < len(day):
                all_main_dishes.append(day[idx])
                total_slots += 1

    if total_slots == 0:
        return 100.0

    unique_count = len(set(all_main_dishes))
    return float((unique_count / total_slots) * 100.0)
