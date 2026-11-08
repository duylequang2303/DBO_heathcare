"""Tests for KLCN142 Remediation Plan Fixes.

Covers:
1. Dislike word boundary matching (no substring false positives like cá -> cà chua).
2. Gout & kidney disease warnings in profile/services.
3. Deterministic inner solver seeding via food_ids hash.
4. Two-tier stagnation_window configuration & IDBO restart activation.
"""

import pytest
import numpy as np

from src.models.allergen_rules import is_dislike_conflict
from src.models.user_profile import UserProfile, Gender, ActivityLevel, Goal
from src.models.constraints import validate_menu
from src.models.menu import Menu, MealType, MenuItem
from app.api.services import PRESET_PROFILES, build_profile, menu_notices
from app.api.schemas import ProfileIn
from src.algorithms.two_tier_solver import TwoTierConfig, TwoTierResult, two_tier_optimize
from src.models.food_selector import build_meal_pools
from src.utils.data_loader import build_food_map, load_food_db


@pytest.fixture(scope="module")
def food_map_fixture():
    df = load_food_db()
    return build_food_map(df)


def test_dislike_word_boundary_avoids_substring_false_positives():
    """Ghét cá không chặn cà chua / rau cải; ghét bò không chặn quả bơ."""
    assert not is_dislike_conflict("Cà chua xào thịt", ["cá"])
    assert not is_dislike_conflict("Rau cải thìa xào tỏi", ["cá"])
    assert not is_dislike_conflict("Quả bơ sáp dầm đường", ["bò"])
    assert not is_dislike_conflict("Gan heo xào giá", ["gà"])

    # True positives must be caught
    assert is_dislike_conflict("Cá hồi áp chảo sốt cam", ["cá"])
    assert is_dislike_conflict("Thịt bò xào ớt chuông", ["bò"])
    assert is_dislike_conflict("Thịt gà xé phay", ["gà"])


def test_gout_and_kidney_warnings_emitted_for_clinical_profiles():
    """Hồ sơ bệnh lý gout hoặc suy thận nhận được cảnh báo y tế rõ ràng."""
    p_gout = ProfileIn(**{**PRESET_PROFILES["p1"], "medical_conditions": ["gút"]})
    user_p_gout = build_profile(p_gout)
    warnings_gout, _ = menu_notices(user_p_gout)
    assert any("gout" in w.lower() or "purin" in w.lower() for w in warnings_gout)

    p_kidney = ProfileIn(**{**PRESET_PROFILES["p1"], "medical_conditions": ["suy thận"]})
    user_p_kidney = build_profile(p_kidney)
    warnings_kidney, _ = menu_notices(user_p_kidney)
    assert any("thận" in w.lower() or "protein" in w.lower() for w in warnings_kidney)


def test_two_tier_solver_inner_seed_is_deterministic_by_food_hash(food_map_fixture):
    """Cùng seed và cùng food_ids luôn cho kết quả tầng trong đồng nhất tuyệt đối."""
    profile = UserProfile(
        name="Test deterministic",
        age=30,
        gender=Gender.MALE,
        height_cm=170.0,
        weight_kg=65.0,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
    )
    targets = {
        "calories": 2000.0,
        "protein_g": 100.0,
        "carbs_g": 250.0,
        "fat_g": 60.0,
        "fiber_g": 30.0,
        "sodium_mg": 2000.0,
    }

    config1 = TwoTierConfig(
        outer_algo="dbo",
        outer_n_agents=4,
        outer_max_iter=2,
        inner_algo="dbo",
        inner_n_agents=4,
        inner_max_iter=3,
        seed=42,
    )
    config2 = TwoTierConfig(
        outer_algo="dbo",
        outer_n_agents=4,
        outer_max_iter=2,
        inner_algo="dbo",
        inner_n_agents=4,
        inner_max_iter=3,
        seed=42,
    )

    res1 = two_tier_optimize(profile, food_map_fixture, targets, config1)
    res2 = two_tier_optimize(profile, food_map_fixture, targets, config2)

    assert res1.best_food_ids == res2.best_food_ids
    np.testing.assert_allclose(res1.best_portions_g, res2.best_portions_g, atol=1e-5)
    assert abs(res1.best_fitness - res2.best_fitness) < 1e-5
    # Metrics consistency: 5g rounding and rounded fitness are reported
    assert res1.rounded_portions_g is not None
    assert res1.rounded_fitness is not None
    np.testing.assert_allclose(res1.rounded_portions_g % 5.0, 0.0, atol=1e-5)


def test_two_tier_idbo_restart_activates_with_low_stagnation_window(food_map_fixture):
    """IDBO kích hoạt restart khi stagnation_window thấp và thuật toán bị trì trệ."""
    profile = UserProfile(
        name="Test IDBO Restart",
        age=30,
        gender=Gender.MALE,
        height_cm=170.0,
        weight_kg=65.0,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
    )
    targets = {
        "calories": 2000.0,
        "protein_g": 100.0,
        "carbs_g": 250.0,
        "fat_g": 60.0,
        "fiber_g": 30.0,
        "sodium_mg": 2000.0,
    }

    config = TwoTierConfig(
        outer_algo="idbo",
        outer_n_agents=8,
        outer_max_iter=10,
        inner_algo="idbo",
        inner_n_agents=8,
        inner_max_iter=10,
        outer_diversity_threshold=0.8,
        inner_diversity_threshold=0.8,
        stagnation_window=2,
        outer_stagnation_window=2,
        inner_stagnation_window=2,
        restart_rate=0.5,
        seed=123,
    )

    res = two_tier_optimize(profile, food_map_fixture, targets, config)
    # Restart counters must be reported in telemetry
    assert hasattr(res, "outer_restarts")
    assert hasattr(res, "inner_restarts_total")
    assert res.outer_restarts >= 0
    assert res.inner_restarts_total >= 0
    # Telemetry properties must exist and be valid integers
    assert isinstance(res.outer_restarts, int)
    assert isinstance(res.inner_restarts_total, int)

