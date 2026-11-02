"""Regression tests: ràng buộc khẩu phần theo vai trò món (Tuần 11).

Trước đây solver và validator dùng khoảng vô hướng [25, 350] cho mọi món nên
món tráng miệng/rau bị kịch trần 350g. Bộ test này khoá lại 3 điểm:

1. generate: khẩu phần sau làm tròn 5g nằm trong ROLE_PORTION_BOUNDS.
2. swap: inner solver nhận vector bounds theo vai trò + làm tròn vẫn hợp lệ.
3. validate_menu(food_map=...) phát hiện khẩu phần vượt biên vai trò.
"""
import pytest
from fastapi.testclient import TestClient

from app.api.services import (
    _get_targets_with_conditions,
    build_profile,
    get_food_map,
)
from app.api.schemas import ProfileIn
from app.main import app
from src.models.constraints import validate_menu
from src.models.dish_category import (
    classify_dish_role,
    get_role_portion_bounds,
    portion_bounds_for_food_ids,
)
from src.models.menu import Meal, MealType, Menu
from tests.conftest import item_from_map

client = TestClient(app)

BASE_PROFILE = {
    "name": "Duy",
    "age": 22,
    "gender": "male",
    "height_cm": 170.0,
    "weight_kg": 65.0,
    "activity_level": "MODERATE",
    "goal": "MAINTAIN",
    "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
    "medical_conditions": ["healthy"],
    "allergies": [],
    "dislikes": [],
}


@pytest.fixture(scope="module")
def sample_menu():
    res = client.post(
        "/api/menu/generate",
        json={"profile": BASE_PROFILE, "seed": 9001, "config": "smoke"},
    )
    assert res.status_code == 200, res.text
    return res.json()


def _role_bounds(food_id: str) -> tuple[float, float]:
    row = get_food_map()[food_id]
    role = classify_dish_role(
        str(row["food_name"]),
        str(row.get("category", "")),
        str(row.get("source", "")),
    )
    return get_role_portion_bounds(role)


def test_portion_bounds_helper_matches_role_table():
    food_map = get_food_map()
    ids = list(food_map)[:8]
    lows, highs = portion_bounds_for_food_ids(ids, food_map)
    assert len(lows) == len(highs) == len(ids)
    for fid, low, high in zip(ids, lows, highs):
        assert (low, high) == _role_bounds(fid)


def test_generate_portions_respect_role_bounds(sample_menu):
    for item in sample_menu["items"]:
        low, high = _role_bounds(item["food_id"])
        assert item["portion_g_rounded"] % 5 == 0
        assert low <= item["portion_g_rounded"] <= high, (
            f"{item['name']}: {item['portion_g_rounded']}g ngoài [{low}, {high}]"
        )


def test_generate_has_no_technical_350g_ceiling_for_non_soup(sample_menu):
    for item in sample_menu["items"]:
        _, high = _role_bounds(item["food_id"])
        if high < 350.0:
            assert item["portion_g_rounded"] <= high


def test_generated_menu_validates_clean_against_role_bounds(sample_menu):
    profile = build_profile(ProfileIn(**BASE_PROFILE))
    targets = _get_targets_with_conditions(profile)
    food_map = get_food_map()
    menu = Menu()
    for meal_type in MealType:
        items = [
            item_from_map(food_map, it["food_id"], float(it["portion_g_rounded"]))
            for it in sample_menu["items"]
            if it["slot"].rsplit("_", 1)[0] == meal_type.value
        ]
        menu.meals[meal_type] = Meal(meal_type, items)
    violations = validate_menu(menu, profile, targets, food_map=food_map)
    assert not any("out of range" in msg for msg in violations), violations


@pytest.mark.parametrize("slot", ["snack_0", "lunch_1"])
def test_swap_portions_respect_role_bounds(sample_menu, slot):
    food_ids = [item["food_id"] for item in sample_menu["items"]]
    portions = [item["portion_g"] for item in sample_menu["items"]]
    for seed in (9001, 9002, 9003):
        res = client.post(
            "/api/menu/swap",
            json={
                "profile": BASE_PROFILE,
                "food_ids": food_ids,
                "slot": slot,
                "new_food_id": None,
                "seed": seed,
                "old_portions_g": portions,
            },
        )
        assert res.status_code == 200, res.text
        data = res.json()
        for item in data["items"]:
            low, high = _role_bounds(item["food_id"])
            assert low <= item["portion_g_rounded"] <= high, (
                f"slot {slot} seed {seed}: {item['name']} "
                f"{item['portion_g_rounded']}g ngoài [{low}, {high}]"
            )
        assert not any("out of range" in msg for msg in data["violations"]), data["violations"]


def test_cauliflower_is_vegetable_not_soup():
    """'Súp lơ' phải là rau (trần 220g), không phải canh/súp (350g)."""
    from src.models.dish_category import DishRole

    for name in ("Súp lơ trắng", "Súp lơ xanh", "Súp lơ trắng luộc"):
        role = classify_dish_role(name)
        assert role is DishRole.VEGETABLE, (name, role)
        assert get_role_portion_bounds(role) == (80.0, 220.0)
    # Canh/súp thật vẫn giữ nguyên vai trò và trần 350g.
    assert classify_dish_role("Canh cải xanh") is DishRole.SOUP
    assert get_role_portion_bounds(DishRole.SOUP) == (100.0, 350.0)


def test_validate_menu_flags_out_of_role_bounds():
    food_map = get_food_map()
    protein_id = next(
        fid
        for fid in food_map
        if classify_dish_role(
            str(food_map[fid]["food_name"]), str(food_map[fid].get("category", ""))
        ).value
        == "main_protein"
    )
    low, high = _role_bounds(protein_id)
    assert (low, high) == (60.0, 180.0)

    menu = Menu()
    menu.meals[MealType.LUNCH] = Meal(
        MealType.LUNCH, [item_from_map(food_map, protein_id, 220.0)]
    )
    profile = build_profile(ProfileIn(**BASE_PROFILE))
    targets = _get_targets_with_conditions(profile)

    issues = validate_menu(menu, profile, targets, food_map=food_map)
    assert any("out of range [60, 180]" in msg for msg in issues), issues
