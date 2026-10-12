"""Unit tests for Diversity Penalty module."""

import pytest
from src.models.diversity_penalty import (
    calculate_unique_main_dish_pct,
    diversity_penalty,
)


def test_no_history_zero_penalty():
    """Verify penalty is 0 when history is empty."""
    day1 = ["f0", "f1", "main_lunch_1", "f3", "main_dinner_1", "f5", "f6", "f7"]
    assert diversity_penalty(day1, []) == 0.0
    assert diversity_penalty(day1, None) == 0.0


def test_unique_main_dishes_zero_penalty():
    """Verify penalty is 0 when all main dishes are unique across consecutive days."""
    day1 = ["f0", "f1", "L1", "f3", "D1", "f5", "f6", "f7"]
    day2 = ["f0", "f1", "L2", "f3", "D2", "f5", "f6", "f7"]
    assert diversity_penalty(day2, [day1], penalty_weight=10.0) == 0.0


def test_duplicate_main_dish_triggers_penalty():
    """Verify penalty triggers when lunch or dinner main dish repeats."""
    day1 = ["f0", "f1", "L1", "f3", "D1", "f5", "f6", "f7"]
    # day2 repeats L1
    day2 = ["f0", "f1", "L1", "f3", "D2", "f5", "f6", "f7"]
    assert diversity_penalty(day2, [day1], penalty_weight=15.0) == 15.0

    # day2 repeats both L1 and D1
    day2_both = ["f0", "f1", "L1", "f3", "D1", "f5", "f6", "f7"]
    assert diversity_penalty(day2_both, [day1], penalty_weight=15.0) == 30.0


def test_lookback_window():
    """Verify dishes outside the lookback window are not penalized."""
    day1 = ["f0", "f1", "L1", "f3", "D1", "f5", "f6", "f7"]
    day2 = ["f0", "f1", "L2", "f3", "D2", "f5", "f6", "f7"]
    day3 = ["f0", "f1", "L3", "f3", "D3", "f5", "f6", "f7"]
    # day4 repeats L1 (3 days ago). With lookback_days=2 (checks day2 and day3), penalty should be 0.
    day4 = ["f0", "f1", "L1", "f3", "D4", "f5", "f6", "f7"]

    assert diversity_penalty(day4, [day1, day2, day3], lookback_days=2) == 0.0
    # With lookback_days=3, day1 is included -> penalty triggers
    assert diversity_penalty(day4, [day1, day2, day3], lookback_days=3) == 10.0


def test_calculate_unique_main_dish_pct():
    """Verify calculation of percentage of unique main dishes."""
    # 2 days, 2 main dishes per day -> 4 total main dishes.
    # 3 unique, 1 duplicate -> 3/4 = 75%
    week = [
        ["f0", "f1", "L1", "f3", "D1", "f5", "f6", "f7"],
        ["f0", "f1", "L1", "f3", "D2", "f5", "f6", "f7"],
    ]
    pct = calculate_unique_main_dish_pct(week)
    assert pct == 75.0
