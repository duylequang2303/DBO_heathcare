"""Unit tests for menu_objective adapter."""

import numpy as np
import pytest

from src.algorithms.idbo import IDBO
from src.algorithms.menu_objective import decode_result, make_menu_objective
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets


@pytest.fixture(scope="module")
def food_data():
    """Load food database and return food mapping dictionary."""
    df = load_food_db()
    food_map = build_food_map(df)
    return food_map


@pytest.fixture
def profile_p1():
    """Fixture providing standard UserProfile P1 for testing."""
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
    )


@pytest.fixture
def sample_food_ids(food_data, profile_p1):
    """Fixture providing 8 valid sampled food IDs using seed 7000."""
    from src.models.food_sampler import sample_food_ids
    rng = np.random.default_rng(7000)
    return sample_food_ids(food_data, profile_p1.meal_counts, profile_p1, rng)


def test_dimension_validation(food_data, profile_p1, sample_food_ids):
    """Ensure objective rejects vectors whose dimension does not match sum(meal_counts)."""
    targets = daily_all_targets(profile_p1)
    obj = make_menu_objective(profile_p1, sample_food_ids, food_data, targets)

    # Wrong dimension must raise ValueError
    with pytest.raises(ValueError):
        obj(np.array([100.0] * 7))

    with pytest.raises(ValueError):
        obj(np.array([100.0] * 9))

    # Correct dimension must not raise
    val = obj(np.array([100.0] * 8))
    assert isinstance(val, float)


def test_objective_bounded_and_deterministic(food_data, profile_p1, sample_food_ids):
    """Verify objective returns deterministic values within [-100, 100] fitness bounds."""
    targets = daily_all_targets(profile_p1)
    obj = make_menu_objective(profile_p1, sample_food_ids, food_data, targets)

    x = np.array([150.0] * 8)
    val1 = obj(x)
    val2 = obj(x)

    assert val1 == val2
    # Since fitness is in [-100, 100], -val1 is fitness
    fitness = -val1
    assert -100.0 <= fitness <= 100.0


def test_better_menu_has_lower_objective(food_data, profile_p1, sample_food_ids):
    """Ensure a more balanced menu has a lower objective value (higher fitness)."""
    targets = daily_all_targets(profile_p1)
    obj = make_menu_objective(profile_p1, sample_food_ids, food_data, targets)

    # An extreme portion (e.g. 25g each) produces way too few calories vs target (~2500 kcal)
    # A moderate portion (e.g. 150g) will be closer to target calories
    x_tiny = np.array([25.0] * 8)
    x_moderate = np.array([150.0] * 8)

    val_tiny = obj(x_tiny)
    val_moderate = obj(x_moderate)

    # Since lower objective means higher (better) fitness
    assert val_moderate < val_tiny


def test_idbo_integration(food_data, profile_p1, sample_food_ids):
    """Test full integration with IDBO optimize loop within bounds [25, 350]."""
    targets = daily_all_targets(profile_p1)
    obj = make_menu_objective(profile_p1, sample_food_ids, food_data, targets)

    optimizer = IDBO(n_agents=8, max_iter=5)
    result = optimizer.optimize(obj, dim=8, lb=25.0, ub=350.0, seed=42)

    assert len(result.best_x) == 8
    assert np.all(result.best_x >= 25.0 - 1e-6)
    assert np.all(result.best_x <= 350.0 + 1e-6)
    assert len(result.history) == 6  # iter 0 to 5
    # decode result
    menu = decode_result(sample_food_ids, result.best_x, food_data, profile_p1.meal_counts)
    assert len(menu.all_items()) == 8
