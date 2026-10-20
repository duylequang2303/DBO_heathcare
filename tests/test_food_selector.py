"""Tests for food_selector module (discrete food selection)."""

import numpy as np
import pytest

from src.models.food_selector import (
    build_meal_pools,
    decode_food_selection,
    get_meal_order_slots,
)
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db


@pytest.fixture
def food_map_fixture():
    df = load_food_db()
    return build_food_map(df)


@pytest.fixture
def sample_profile():
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


def test_deterministic_decoding():
    """1. Cùng z -> cùng food_ids (deterministic)."""
    pools = {
        "slot_0": ["F1", "F2", "F3", "F4", "F5"],
        "slot_1": ["F1", "F2", "F3", "F4", "F5"],
    }
    meal_order = ["slot_0", "slot_1"]
    z = np.array([0.25, 0.75])

    res1 = decode_food_selection(z, pools, meal_order)
    res2 = decode_food_selection(z, pools, meal_order)
    assert res1 == res2


def test_no_duplicate_within_same_meal():
    """2. Không trùng food_id trong cùng bữa khi z_i chọn cùng chỉ số."""
    pools = {
        "breakfast_0": ["F1", "F2", "F3"],
        "breakfast_1": ["F1", "F2", "F3"],
    }
    meal_order = ["breakfast_0", "breakfast_1"]
    # Cả hai z đều trỏ về index 0
    z = np.array([0.05, 0.05])

    res = decode_food_selection(z, pools, meal_order)
    assert len(res) == 2
    assert res[0] != res[1]
    assert set(res) == {"F1", "F2"}


def test_z_zero_picks_first_element():
    """3. z toàn 0.0 -> lấy phần tử đầu pool (khi khác bữa)."""
    pools = {
        "breakfast_0": ["B1", "B2"],
        "lunch_0": ["L1", "L2"],
    }
    meal_order = ["breakfast_0", "lunch_0"]
    z = np.array([0.0, 0.0])

    res = decode_food_selection(z, pools, meal_order)
    assert res == ["B1", "L1"]


def test_z_near_one_picks_last_element():
    """4. z toàn 0.999 -> lấy phần tử cuối pool."""
    pools = {
        "breakfast_0": ["B1", "B2", "B3"],
        "lunch_0": ["L1", "L2", "L3"],
    }
    meal_order = ["breakfast_0", "lunch_0"]
    z = np.array([0.999, 0.999])

    res = decode_food_selection(z, pools, meal_order)
    assert res == ["B3", "L3"]


def test_empty_pool_raises_value_error():
    """5. Pool rỗng sau lọc dị ứng hoặc không đủ min_pool_size -> ValueError rõ ràng."""
    fake_map = {
        "F1": {"food_name": "Peanut Butter", "meal_type": "breakfast"},
    }
    profile_allergic = UserProfile(
        name="Test",
        age=25,
        gender=Gender.FEMALE,
        weight_kg=55.0,
        height_cm=160.0,
        activity_level=ActivityLevel.SEDENTARY,
        allergies=["peanut"],
        meal_counts={"breakfast": 1},
    )
    with pytest.raises(ValueError, match="less than min_pool_size"):
        build_meal_pools(fake_map, {"breakfast": 1}, profile_allergic, min_pool_size=1)


def test_min_pool_size_satisfied_for_p1(food_map_fixture, sample_profile):
    """6. min_pool_size=20: pool đủ size với Profile P1 trên kho 15.929 món."""
    pools = build_meal_pools(
        food_map_fixture,
        sample_profile.meal_counts,
        sample_profile,
        min_pool_size=20,
    )
    slots = get_meal_order_slots(sample_profile.meal_counts)
    assert len(slots) == 8
    for slot in slots:
        assert slot in pools
        assert len(pools[slot]) >= 20


# Cương — Week 8: edge-case coverage for linear probing.
def test_all_candidates_exhausted_raises():
    pools = {"lunch_0": ["F1"], "lunch_1": ["F1"]}
    with pytest.raises(ValueError, match="Not enough unique"):
        decode_food_selection(np.array([0.0, 0.0]), pools, list(pools))

def test_duplicate_ids_in_pool_cannot_bypass_probing():
    pools = {"dinner_0": ["F1", "F1"], "dinner_1": ["F1", "F1"]}
    with pytest.raises(ValueError, match="Not enough unique"):
        decode_food_selection(np.array([0.0, 0.0]), pools, list(pools))

@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_nonfinite_coordinates_rejected(bad):
    with pytest.raises(ValueError, match="finite"):
        decode_food_selection(np.array([bad]), {"lunch_0": ["F1"]}, ["lunch_0"])

def test_boundary_coordinates_are_clamped():
    pools = {"lunch_0": ["F1", "F2", "F3"]}
    assert decode_food_selection(np.array([-0.1]), pools, ["lunch_0"]) == ["F1"]
    assert decode_food_selection(np.array([1.0]), pools, ["lunch_0"]) == ["F3"]

def test_missing_slot_and_shape_rejected():
    with pytest.raises(ValueError, match="empty or missing"):
        decode_food_selection(np.array([0.2]), {}, ["lunch_0"])
    with pytest.raises(ValueError, match="one-dimensional"):
        decode_food_selection(np.array([[0.2]]), {"lunch_0": ["F1"]}, ["lunch_0"])


def test_real_database_pools_exclude_raw_ingredients(food_map_fixture, sample_profile):
    from src.models.dish_category import is_raw_or_industrial_junk
    pools = build_meal_pools(food_map_fixture, sample_profile.meal_counts, sample_profile)
    for ids in pools.values():
        assert ids
        for food_id in ids:
            food = food_map_fixture[food_id]
            assert not is_raw_or_industrial_junk(food['food_name'], food.get('category', ''))


def test_real_database_slots_have_expected_roles(food_map_fixture, sample_profile):
    from src.models.dish_category import DishRole, classify_dish_role
    pools = build_meal_pools(food_map_fixture, sample_profile.meal_counts, sample_profile)
    expected = {
        'breakfast_0': {DishRole.STAPLE},
        'breakfast_1': {DishRole.MAIN_PROTEIN, DishRole.FRUIT_SNACK},
        'lunch_0': {DishRole.STAPLE},
        'lunch_1': {DishRole.MAIN_PROTEIN, DishRole.VEGETABLE, DishRole.SOUP},
        'dinner_0': {DishRole.STAPLE},
        'dinner_1': {DishRole.MAIN_PROTEIN, DishRole.VEGETABLE, DishRole.SOUP},
        'snack_0': {DishRole.FRUIT_SNACK, DishRole.BEVERAGE},
    }
    for slot, roles in expected.items():
        assert len(pools[slot]) >= 20
        for food_id in pools[slot]:
            food = food_map_fixture[food_id]
            role = classify_dish_role(str(food['food_name']), str(food.get('category', '')), str(food.get('source', '')))
            assert role in roles
