"""Tests for food_selector module (discrete food selection)."""

import numpy as np
import pytest

from src.models.food_selector import (
    MIN_ROLE_POOL_SIZE,
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
    with pytest.raises(ValueError, match="ít hơn ngưỡng tối thiểu"):
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
        'breakfast_1': {DishRole.MAIN_PROTEIN, DishRole.VEGETABLE},
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


def test_staple_slots_contain_only_staple(food_map_fixture, sample_profile):
    """lunch_0, dinner_0, breakfast_0 chỉ chứa STAPLE."""
    from src.models.dish_category import DishRole, classify_dish_role
    pools = build_meal_pools(food_map_fixture, sample_profile.meal_counts, sample_profile)
    for slot in ["breakfast_0", "lunch_0", "dinner_0"]:
        assert slot in pools
        for fid in pools[slot]:
            food = food_map_fixture[fid]
            role = classify_dish_role(
                str(food.get("food_name", "")),
                str(food.get("category", "")),
                str(food.get("source", "vietnamese")),
            )
            assert role == DishRole.STAPLE, f"Slot {slot} chứa món {fid} ({food.get('food_name')}) role={role} != STAPLE"


def test_main_slots_contain_only_protein_veg_soup(food_map_fixture, sample_profile):
    """lunch_1, dinner_1 chỉ chứa MAIN_PROTEIN / VEGETABLE / SOUP."""
    from src.models.dish_category import DishRole, classify_dish_role
    pools = build_meal_pools(food_map_fixture, sample_profile.meal_counts, sample_profile)
    allowed = {DishRole.MAIN_PROTEIN, DishRole.VEGETABLE, DishRole.SOUP}
    for slot in ["lunch_1", "dinner_1"]:
        assert slot in pools
        for fid in pools[slot]:
            food = food_map_fixture[fid]
            role = classify_dish_role(
                str(food.get("food_name", "")),
                str(food.get("category", "")),
                str(food.get("source", "vietnamese")),
            )
            assert role in allowed, f"Slot {slot} chứa món {fid} ({food.get('food_name')}) role={role} not in {allowed}"


def test_production_whitelist_role_pools_are_complete():
    """Production whitelist (163 items), not the 15k legacy DB, must pass C4."""
    from app.api.schemas import ProfileIn
    from app.api.services import PRESET_PROFILES, build_profile, get_food_map
    from src.models.dish_category import classify_dish_role
    from src.models.food_selector import _roles_for_slot

    food_map = get_food_map()
    for profile_key in ["p1", "p2", "p3"]:
        profile = build_profile(ProfileIn(**PRESET_PROFILES[profile_key]))
        pools = build_meal_pools(food_map, profile.meal_counts, profile)
        for slot_name, food_ids in pools.items():
            meal_name, idx_raw = slot_name.rsplit("_", 1)
            count = profile.meal_counts[meal_name]
            allowed = _roles_for_slot(meal_name, int(idx_raw), count)
            assert len(food_ids) >= MIN_ROLE_POOL_SIZE
            for fid in food_ids:
                row = food_map[fid]
                role = classify_dish_role(
                    str(row.get("food_name", "")),
                    str(row.get("category", "")),
                    str(row.get("source", "")),
                )
                assert role in allowed, (profile_key, slot_name, fid, role)


def test_role_pool_too_small_raises_value_error():
    """Role pool < 3 món -> raise ValueError rõ ràng."""
    fake_map = {
        "F1": {"food_name": "Cơm trắng", "category": "ngũ cốc", "source": "vietnamese", "meal_type": "all"},
        "F2": {"food_name": "Cơm tấm", "category": "ngũ cốc", "source": "vietnamese", "meal_type": "all"},
    }
    profile = UserProfile(
        name="Test",
        age=25,
        gender=Gender.FEMALE,
        weight_kg=55.0,
        height_cm=160.0,
        activity_level=ActivityLevel.SEDENTARY,
        meal_counts={"lunch": 1},
    )
    with pytest.raises(ValueError, match="Nhóm món theo vai trò cho slot 'lunch_0' quá nhỏ"):
        build_meal_pools(fake_map, {"lunch": 1}, profile, min_pool_size=1)


def test_30_seeds_p1_p2_p3_no_duplicates_no_role_violations(food_map_fixture):
    """30 seed P1/P2/P3: 0 food_id trùng, 0 vi phạm vai trò theo định nghĩa hệ thống."""
    from app.api.services import PRESET_PROFILES, build_profile
    from app.api.schemas import ProfileIn
    from src.models.dish_category import classify_dish_role
    from src.models.food_selector import _roles_for_slot

    slots_order = ["breakfast_0", "breakfast_1", "lunch_0", "lunch_1", "dinner_0", "dinner_1", "snack_0"]

    for profile_key in ["p1", "p2", "p3"]:
        profile_in = ProfileIn(**PRESET_PROFILES[profile_key])
        profile = build_profile(profile_in)
        pools = build_meal_pools(food_map_fixture, profile.meal_counts, profile)

        for seed in range(9001, 9031):
            rng = np.random.default_rng(seed)
            z = rng.random(len(slots_order))
            selected_ids = decode_food_selection(z, pools, slots_order)

            # 1. Chống trùng toàn ngày
            assert len(selected_ids) == len(set(selected_ids)), (
                f"Duplicate food_id in profile={profile_key}, seed={seed}: {selected_ids}"
            )

            # 2. Ràng buộc vai trò slot
            for slot_name, fid in zip(slots_order, selected_ids):
                food = food_map_fixture[fid]
                meal_name, idx_str = slot_name.split("_")
                count = profile.meal_counts.get(meal_name, 0)
                allowed = _roles_for_slot(meal_name, int(idx_str), count)
                role = classify_dish_role(
                    str(food.get("food_name", "")),
                    str(food.get("category", "")),
                    str(food.get("source", "vietnamese")),
                )
                assert role in allowed, (
                    f"Role violation in profile={profile_key}, seed={seed}, slot={slot_name}: "
                    f"food={fid} ({food.get('food_name')}) role={role} not in {allowed}"
                )
