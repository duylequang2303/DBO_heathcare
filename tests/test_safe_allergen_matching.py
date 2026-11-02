"""Bộ test cho khớp dị ứng an toàn (allergen_rules).

Mục tiêu: chặn đúng nhóm dị ứng theo ranh giới từ, đồng thời KHÔNG chặn nhầm
các món Việt Nam thông thường (củ cái, rau giấp cá, quả bơ, đậu bắp...).

Đây là kiểm tra theo TÊN MÓN. Dataset chưa có bảng nguyên liệu/allergen nên
kết quả chỉ mang tính hỗ trợ, không phải kết luận an lâm sàng.
"""
import pytest
from fastapi.testclient import TestClient

from app.api.services import get_food_map
from app.main import app
from src.models.allergen_rules import (
    ALLERGEN_TAXONOMY,
    allergen_group_for,
    conflicting_allergens,
    is_allergen_conflict,
)
from src.models.constraints import validate_menu
from src.models.food_sampler import candidates_for_meal
from src.models.menu import Meal, MealType, Menu
from src.models.user_profile import ActivityLevel, Gender, Goal, UserProfile
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


# ---------------------------------------------------------------------------
# 1. Khớp theo nhóm: CHẶN đúng
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "food_name, allergy",
    [
        # hải sản
        ("Tôm hấp nước dừa", "hải sản"),
        ("Cá điêu hồng kho tộ", "hải sản"),
        ("Cua đồng rang muối", "hải sản"),
        ("Mực xào chua ngọt", "hải sản"),
        ("Tép rang", "shrimp"),
        ("Salmon áp chảo", "fish"),
        ("Nghêu hấp sả", "seafood"),
        ("Cá hồi", "cá"),
        # sữa
        ("Sữa chua Ba Vì", "sữa"),
        ("Sữa chua (từ sữa bò)", "dairy"),
        ("Phô mai con bò cười", "sữa"),
        ("Pho mát", "pho mát"),
        ("Bánh mì phô mai", "milk"),
        # đậu phộng
        ("Kẹo đậu phộng", "đậu phộng"),
        ("Lạc rang muối", "lạc"),
        ("Peanut butter", "peanut"),
        ("Bơ đậu phộng", "đậu phộng"),
        # trứng
        ("Trứng gà luộc", "trứng"),
        ("Trứng vịt bắc thảo", "egg"),
    ],
)
def test_allergen_group_blocks_real_dishes(food_name, allergy):
    assert is_allergen_conflict(food_name, [allergy]) is True


# ---------------------------------------------------------------------------
# 2. Khớp theo nhóm: CHO QUA (không false-positive)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "food_name, allergy",
    [
        ("Rau giấp cá", "hải sản"),
        ("Dầu cám", "hải sản"),
        ("Củ cái muối", "hải sản"),
        ("Gạo nếp cái", "cá"),
        ("Quả bơ sáp", "sữa"),
        ("Sữa đậu nành", "sữa"),
        ("Sữa bắp", "dairy"),
        ("Bơ thực vật", "sữa"),
        ("Bơ đậu phộng", "sữa"),
        ("Canh đậu bắp", "đậu phộng"),
        ("Đậu cô ve luộc", "lạc"),
        ("Đậu hũ sốt cà", "đậu phộng"),
        ("Cà tím nướng", "trứng"),
    ],
)
def test_common_vietnamese_dishes_are_not_false_positives(food_name, allergy):
    assert is_allergen_conflict(food_name, [allergy]) is False


def test_unknown_token_keeps_substring_fallback():
    # Dị ứng ngoài taxonomy vẫn phải chặn (không bỏ sót do người dùng tự nhập).
    assert is_allergen_conflict("Sữa đậu nành", ["đậu nành"]) is True
    assert is_allergen_conflict("Cháo hạt sen", ["hạt sen"]) is True
    assert is_allergen_conflict("Cháo hạt sen", ["đậu nành"]) is False


def test_empty_allergy_list_never_blocks():
    assert is_allergen_conflict("Tôm hấp", []) is False
    assert is_allergen_conflict("Tôm hấp", ["", "  "]) is False


def test_taxonomy_tokens_all_map_back_to_their_group():
    for key, group in ALLERGEN_TAXONOMY.items():
        for token in group.tokens:
            assert allergen_group_for(token).key == key


def test_conflicting_allergens_reports_the_user_token():
    hits = conflicting_allergens("Cá hồi", ["hải sản", "đậu phộng"])
    assert hits == ["hải sản"]


# ---------------------------------------------------------------------------
# 3. Bộ lọc candidate pool dùng cùng logic
# ---------------------------------------------------------------------------
def test_candidate_pool_excludes_seafood_but_keeps_radish():
    food_map = {
        "FISH": {"food_name": "Cá hồi", "meal_type": "all"},
        "SHRIMP": {"food_name": "Tôm đồng", "meal_type": "all"},
        "RADISH": {"food_name": "Củ cái", "meal_type": "all"},
        "RICE": {"food_name": "Cơm trắng", "meal_type": "all"},
    }
    profile = UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        height_cm=170.0,
        weight_kg=65.0,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        allergies=["hải sản"],
        dislikes=[],
        likes=[],
        meal_counts={"lunch": 2},
    )
    ids = candidates_for_meal(food_map, "lunch", profile)
    assert "FISH" not in ids
    assert "SHRIMP" not in ids
    assert "RADISH" in ids
    assert "RICE" in ids


# ---------------------------------------------------------------------------
# 4. validate_menu bắt dị ứng theo nhóm
# ---------------------------------------------------------------------------
def _profile(allergies):
    return UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        height_cm=170.0,
        weight_kg=65.0,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        allergies=allergies,
        dislikes=[],
        likes=[],
        meal_counts={"lunch": 1},
    )


def _menu_with(food_map, food_ids):
    menu = Menu()
    menu.meals[MealType.LUNCH] = Meal(
        MealType.LUNCH, [item_from_map(food_map, fid, 150.0) for fid in food_ids]
    )
    return menu


def _targets():
    return {
        "calories": 2000.0,
        "protein_g": 100.0,
        "carbs_g": 250.0,
        "fat_g": 60.0,
        "fiber_g": 25.0,
        "sodium_mg": 2300.0,
    }


def test_validate_menu_flags_seafood_group(food_map):
    # VN_8011 = "Cá hồi"; người dùng khai báo "hải sản" (không phải "cá").
    menu = _menu_with(food_map, ["VN_8011"])
    issues = validate_menu(menu, _profile(["hải sản"]), _targets())
    assert any("allergen" in msg and "hải sản" in msg for msg in issues)


def test_validate_menu_does_not_flag_radish_for_seafood_allergy(food_map):
    # Tên món thật trong whitelist có "Củ cái" — không được coi là hải sản.
    radish_ids = [
        fid
        for fid, row in get_food_map().items()
        if row["food_name"].strip().lower() == "củ cái"
    ]
    assert radish_ids, "Whitelist phải còn món 'Củ cái' để kiểm tra false-positive"
    menu = _menu_with(food_map, [radish_ids[0]]) if radish_ids[0] in food_map else Menu()
    if radish_ids[0] not in food_map:
        pytest.skip("Món Củ cái không có trong food_map đầy đủ của fixture")
    issues = validate_menu(menu, _profile(["hải sản", "cá"]), _targets())
    assert not any("allergen" in msg for msg in issues)


# ---------------------------------------------------------------------------
# 5. API: swap từ chối hải sản khi hồ sơ khai báo "hải sản"
# ---------------------------------------------------------------------------
def test_swap_rejects_seafood_when_profile_says_hai_san():
    profile = dict(BASE_PROFILE, allergies=["hải sản"])
    generated = client.post(
        "/api/menu/generate",
        json={"profile": profile, "seed": 9001, "config": "smoke"},
    )
    assert generated.status_code == 200, generated.text
    menu = generated.json()
    food_ids = [item["food_id"] for item in menu["items"]]
    assert "VN_8011" not in food_ids

    res = client.post(
        "/api/menu/swap",
        json={
            "profile": profile,
            "food_ids": food_ids,
            "slot": "lunch_1",
            "new_food_id": "VN_8011",  # Cá hồi
            "seed": 9001,
        },
    )
    assert res.status_code == 400, res.text
    assert "dị ứng" in res.text.lower()


def test_generate_with_seafood_allergy_has_no_seafood_items():
    profile = dict(BASE_PROFILE, allergies=["hải sản"])
    res = client.post(
        "/api/menu/generate",
        json={"profile": profile, "seed": 9001, "config": "smoke"},
    )
    assert res.status_code == 200, res.text
    for item in res.json()["items"]:
        assert not is_allergen_conflict(item["name"], ["hải sản"]), item["name"]
