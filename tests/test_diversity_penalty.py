"""Cương — Week 9 tests for main-dish diversity."""
import pytest
from src.models.diversity_penalty import diversity_penalty

def test_no_repeat():
    assert diversity_penalty(["L3", "D3"], [["L1", "D1"], ["L2", "D2"]]) == 0

def test_one_repeat():
    assert diversity_penalty(["L1", "D3"], [["L1", "D1"]]) == 10

def test_two_repeats():
    assert diversity_penalty(["L1", "D1"], [["L1", "D1"]]) == 20

def test_lookback_ignores_old_days():
    assert diversity_penalty(["L1", "D4"], [["L1", "D1"], ["L2", "D2"], ["L3", "D3"]], lookback_days=2) == 0

def test_repeated_on_two_days_counts_twice():
    assert diversity_penalty(["L1", "D3"], [["L1", "D1"], ["L1", "D2"]]) == 20

def test_empty_history_and_zero_lookback():
    assert diversity_penalty(["L1", "D1"], []) == 0
    assert diversity_penalty(["L1", "D1"], [["L1", "D1"]], lookback_days=0) == 0

def test_full_day_only_main_slots_counted():
    slots = ["breakfast_0", "lunch_0", "lunch_1", "dinner_0", "snack_0"]
    yesterday = ["B1", "L1", "SIDE", "D1", "S1"]
    today = ["B1", "L2", "SIDE", "D1", "S1"]
    assert diversity_penalty(today, [yesterday], meal_order=slots) == 10

@pytest.mark.parametrize("weight", [-1, float("nan"), float("inf")])
def test_invalid_weight(weight):
    with pytest.raises(ValueError, match="penalty_weight"):
        diversity_penalty(["L1", "D1"], [], penalty_weight=weight)

@pytest.mark.parametrize("lookback", [-1, 1.5, True])
def test_invalid_lookback(lookback):
    with pytest.raises(ValueError, match="lookback_days"):
        diversity_penalty(["L1", "D1"], [], lookback_days=lookback)

def test_ambiguous_full_day_without_slots_rejected():
    with pytest.raises(ValueError, match="exactly two"):
        diversity_penalty(["B1", "L1", "D1"], [])
