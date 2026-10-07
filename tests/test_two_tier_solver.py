"""Tests for Two-Tier Mixed-Integer Solver."""

import time
import numpy as np
import pytest

from src.algorithms.two_tier_solver import TwoTierConfig, two_tier_optimize
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets


@pytest.fixture(scope="module")
def food_map_fixture():
    df = load_food_db()
    return build_food_map(df)


@pytest.fixture
def profile_p1():
    return UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        weight_kg=65.0,
        height_cm=170.0,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        diet_type=DietType.STANDARD,
        meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 2},
        allergies=[],
        dislikes=[],
        likes=[],
    )


def test_default_config_p1(food_map_fixture, profile_p1):
    """1. Test that two_tier_optimize executes cleanly on profile P1 with small iterations."""
    targets = daily_all_targets(profile_p1)
    config = TwoTierConfig(
        outer_algo="idbo",
        outer_n_agents=5,
        outer_max_iter=3,
        inner_algo="idbo",
        inner_n_agents=5,
        inner_max_iter=3,
        seed=8001,
    )
    result = two_tier_optimize(profile_p1, food_map_fixture, targets, config)
    assert result is not None
    assert isinstance(result.best_fitness, float)
    assert len(result.history) > 0


def test_portions_in_range(food_map_fixture, profile_p1):
    """2. Test that all returned best_portions_g values are within [25.0, 350.0]."""
    targets = daily_all_targets(profile_p1)
    config = TwoTierConfig(
        outer_algo="idbo",
        outer_n_agents=5,
        outer_max_iter=2,
        inner_algo="idbo",
        inner_n_agents=5,
        inner_max_iter=2,
        seed=8002,
    )
    result = two_tier_optimize(profile_p1, food_map_fixture, targets, config)
    assert np.all(result.best_portions_g >= 25.0)
    assert np.all(result.best_portions_g <= 350.0)


def test_food_ids_count(food_map_fixture, profile_p1):
    """3. Test that best_food_ids matches sum(meal_counts.values()) and foods exist in food_map."""
    targets = daily_all_targets(profile_p1)
    config = TwoTierConfig(
        outer_algo="idbo",
        outer_n_agents=5,
        outer_max_iter=2,
        inner_algo="idbo",
        inner_n_agents=5,
        inner_max_iter=2,
        seed=8003,
    )
    result = two_tier_optimize(profile_p1, food_map_fixture, targets, config)
    expected_count = sum(profile_p1.meal_counts.values())
    assert len(result.best_food_ids) == expected_count
    for fid in result.best_food_ids:
        assert fid in food_map_fixture


def test_dbo_outer_algo(food_map_fixture, profile_p1):
    """4. Test that outer_algo='dbo' runs cleanly."""
    targets = daily_all_targets(profile_p1)
    config = TwoTierConfig(
        outer_algo="dbo",
        outer_n_agents=5,
        outer_max_iter=2,
        inner_algo="dbo",
        inner_n_agents=5,
        inner_max_iter=2,
        seed=8004,
    )
    result = two_tier_optimize(profile_p1, food_map_fixture, targets, config)
    assert result.best_fitness is not None
    assert len(result.best_food_ids) == 8


def test_smoke_fast(food_map_fixture, profile_p1):
    """5. Fast smoke test (outer=3, inner=3, n_agents=5) finishes in under 30 seconds."""
    targets = daily_all_targets(profile_p1)
    config = TwoTierConfig(
        outer_algo="idbo",
        outer_n_agents=5,
        outer_max_iter=3,
        inner_algo="idbo",
        inner_n_agents=5,
        inner_max_iter=3,
        seed=8005,
    )
    t0 = time.perf_counter()
    result = two_tier_optimize(profile_p1, food_map_fixture, targets, config)
    elapsed = time.perf_counter() - t0

    assert elapsed < 30.0, f"Expected smoke test to complete in <30s, took {elapsed:.2f}s"
    assert result.runtime_s > 0
    assert result.outer_evals > 0
    assert result.inner_evals_total > 0
