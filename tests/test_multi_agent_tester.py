"""Tests for scripts/multi_agent_tester.py (multi-agent tester module).

Covers profile generation, Vietnamese report building/formatting, food-name
translation, report review, and end-to-end report generation for sample menus.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from src.models.menu import Meal, MealType, Menu
from src.models.report import (
    MenuItemReport,
    MenuReport,
    build_menu_report,
    format_menu_report,
    get_vietnamese_food_name,
)
from src.models.user_profile import ActivityLevel, Gender, Goal, UserProfile
from src.utils.nutrition import daily_targets
from scripts.multi_agent_tester import (
    generate_test_profiles,
    generate_vietnamese_report,
    review_report_output,
    validate_menu_for_profile,
)
from tests.conftest import build_menu


VN_CHEESE_ROW: dict[str, Any] = {
    "food_id": "VN_TEST_CHEESE",
    "food_name": "Pho mát",
    "category": "Sữa và sản phẩm chế biến",
    "meal_type": "breakfast",
    "source": "vietnamese",
    "calories": 380.0,
    "protein_g": 25.5,
    "carbs_g": 0.0,
    "fat_g": 30.9,
    "fiber_g": 0.0,
    "sodium_mg": 621.0,
    "calcium_mg": 760.0,
    "iron_mg": 0.5,
    "vitamin_c_mg": 1.0,
}

USDA_BACON_ROW: dict[str, Any] = {
    "food_id": "USDA_TEST_BACON",
    "food_name": "Bacon, crispy",
    "category": "Meat/Poultry",
    "meal_type": "breakfast",
    "source": "usda",
    "calories": 541.0,
    "protein_g": 37.0,
    "carbs_g": 1.4,
    "fat_g": 42.0,
    "fiber_g": 0.0,
    "sodium_mg": 1833.0,
    "calcium_mg": 11.0,
    "iron_mg": 1.1,
    "vitamin_c_mg": 0.0,
}

USDA_SALMON_ROW: dict[str, Any] = {
    "food_id": "USDA_TEST_SALMON",
    "food_name": "Atlantic salmon fillet",
    "category": "Seafood",
    "meal_type": "lunch",
    "source": "usda",
    "calories": 206.0,
    "protein_g": 22.0,
    "carbs_g": 0.0,
    "fat_g": 13.0,
    "fiber_g": 0.0,
    "sodium_mg": 61.0,
    "calcium_mg": 12.0,
    "iron_mg": 0.4,
    "vitamin_c_mg": 0.0,
}

USDA_CEREAL_ROW: dict[str, Any] = {
    "food_id": "USDA_TEST_CEREAL",
    "food_name": "Cereals ready-to-eat",
    "category": "Breakfast Cereals",
    "meal_type": "breakfast",
    "source": "usda",
    "calories": 380.0,
    "protein_g": 7.0,
    "carbs_g": 85.0,
    "fat_g": 2.0,
    "fiber_g": 8.0,
    "sodium_mg": 300.0,
    "calcium_mg": 0.0,
    "iron_mg": 0.0,
    "vitamin_c_mg": 0.0,
}


def _extended_food_map(food_map: dict) -> dict[str, dict]:
    extended = dict(food_map)
    extended.update(
        {
            "VN_TEST_CHEESE": VN_CHEESE_ROW,
            "USDA_TEST_BACON": USDA_BACON_ROW,
            "USDA_TEST_SALMON": USDA_SALMON_ROW,
            "USDA_TEST_CEREAL": USDA_CEREAL_ROW,
        }
    )
    return extended


# ---------------------------------------------------------------------------
# 1. build_menu_report produces Vietnamese food names
# ---------------------------------------------------------------------------

def test_build_menu_report_returns_menu_report_with_vietnamese_names(food_map):
    food_map = _extended_food_map(food_map)
    menu = build_menu(
        food_map,
        [
            (MealType.BREAKFAST, "VN_TEST_CHEESE", 60.0),
            (MealType.BREAKFAST, "USDA_TEST_BACON", 30.0),
            (MealType.LUNCH, "USDA_TEST_SALMON", 100.0),
        ],
    )
    report = build_menu_report(
        menu=menu,
        food_map=food_map,
        profile_name="Người kiểm thử",
        targets={"calories": 2200.0},
    )

    assert isinstance(report, MenuReport)
    assert report.profile_name == "Người kiểm thử"
    assert len(report.items) == 3

    vi_names = [item.food_name_vi for item in report.items]
    assert "Pho mát" in vi_names, "Vietnamese-source food should keep its Vietnamese name"
    assert "Xông xô" in vi_names, "USDA bacon should be translated to Vietnamese"
    assert "Cá hồi" in vi_names, "USDA salmon should be translated to Vietnamese"

    # Raw technical names must not leak into displayed names.
    assert "Bacon, crispy" not in vi_names
    assert "Atlantic salmon fillet" not in vi_names
    assert "Cereals ready-to-eat" not in vi_names
    for item in report.items:
        assert "USDA_" not in item.food_name_vi, f"raw ID leaked: {item.food_name_vi}"
        assert "VN_" not in item.food_name_vi, f"raw ID leaked: {item.food_name_vi}"
        assert isinstance(item, MenuItemReport)
        assert item.portion_g > 0


# ---------------------------------------------------------------------------
# 2. format_menu_report output
# ---------------------------------------------------------------------------

def test_format_menu_report_contains_vietnamese_and_no_bare_ids(food_map):
    food_map = _extended_food_map(food_map)
    menu = build_menu(
        food_map,
        [
            (MealType.BREAKFAST, "VN_TEST_CHEESE", 60.0),
            (MealType.LUNCH, "USDA_TEST_SALMON", 100.0),
            (MealType.SNACK, "VN_5007", 100.0),
        ],
    )
    report = build_menu_report(
        menu=menu,
        food_map=food_map,
        profile_name="Duy",
        targets={"calories": 2000.0},
    )
    text = format_menu_report(report)

    assert "BÁO CÁO THỰC ĐƠN ĐỀ XUẤT" in text
    assert "TỔNG KẾT NGÀY:" in text
    assert "Pho mát" in text
    assert "Cá hồi" in text

    # No bare USDA_/VN_ identifiers without Vietnamese names.
    assert re.search(r"\bUSDA_\d+\b", text) is None, "bare USDA id found in report"
    assert re.search(r"\bVN_\d+\b", text) is None, "bare VN id found in report"
    assert "USDA_" not in text
    assert "VN_" not in text


# ---------------------------------------------------------------------------
# 3. review_report_output detects technical IDs and hard names
# ---------------------------------------------------------------------------

def test_review_report_output_detects_usda_and_vn_ids():
    text = "Bữa sáng dùng USDA_40011 và VN_123 kèm theo món Pho bo."
    issues = review_report_output(text, {})

    assert len(issues) == 2
    assert any("USDA" in issue for issue in issues)
    assert any("VN" in issue for issue in issues)


@pytest.mark.parametrize(
    "technical_name",
    ["Cereals ready-to-eat", "Honey Nut Shredded", "BACN,", "ATLANTIC SALMON"],
)
def test_review_report_output_detects_technical_names(technical_name):
    text = f"Chọn món {technical_name} cho bữa sáng hôm nay."
    issues = review_report_output(text, {})

    assert issues, f"expected review issues for technical name: {technical_name}"
    assert any("khó hiểu" in issue for issue in issues)


def test_review_report_output_accepts_clean_vietnamese_report():
    text = (
        "BÁO CÁO THỰC ĐƠN ĐỀ XUẤT\n"
        "1. [Bữa sáng] Pho mát\n"
        "2. [Bữa trưa] Cá hồi\n"
        "TỔNG KẾT NGÀY: Năng lượng: 500 kcal\n"
        "KẾT LUẬN: Thực đơn đáp ứng các ràng buộc dinh dưỡng đã cấu hình."
    )
    assert review_report_output(text, {}) == []


# ---------------------------------------------------------------------------
# 4. generate_test_profiles
# ---------------------------------------------------------------------------

def test_generate_test_profiles_count_and_ranges():
    profiles = generate_test_profiles(seed=42, num_profiles=6)

    assert len(profiles) == 6
    for profile in profiles:
        assert 18 <= profile.age <= 65, f"age out of range: {profile.age}"
        assert 45.0 <= profile.weight_kg <= 90.0, f"weight out of range: {profile.weight_kg}"
        assert 150.0 <= profile.height_cm <= 185.0, f"height out of range: {profile.height_cm}"
        assert profile.name.startswith("Người kiểm thử")
        assert profile.age == int(profile.age)


def test_generate_test_profiles_is_deterministic_with_same_seed():
    first = generate_test_profiles(seed=7, num_profiles=4)
    second = generate_test_profiles(seed=7, num_profiles=4)

    assert [(p.name, p.age, p.weight_kg, p.height_cm) for p in first] == [
        (p.name, p.age, p.weight_kg, p.height_cm) for p in second
    ]


def test_generate_test_profiles_differs_with_different_seed():
    first = generate_test_profiles(seed=1, num_profiles=3)
    second = generate_test_profiles(seed=2, num_profiles=3)

    assert first != second


# ---------------------------------------------------------------------------
# 5. get_vietnamese_food_name
# ---------------------------------------------------------------------------

def test_get_vietnamese_food_name_vietnamese_source_keeps_name():
    row: dict[str, Any] = {"source": "vietnamese", "food_name": "Pho mát"}
    assert get_vietnamese_food_name(row) == "Pho mát"


def test_get_vietnamese_food_name_usda_source_translated():
    assert get_vietnamese_food_name({"source": "usda", "food_name": "Bacon, crispy"}) == "Xông xô"
    assert get_vietnamese_food_name({"source": "usda", "food_name": "Atlantic salmon fillet"}) == "Cá hồi"
    assert get_vietnamese_food_name({"source": "usda", "food_name": "Boiled rice"}) == "Cơm"
    assert get_vietnamese_food_name({"source": "usda", "food_name": "Whole wheat bread"}) == "Bánh mì"


def test_get_vietnamese_food_name_usda_does_not_leak_raw_name():
    row = {"source": "usda", "food_name": "Cereals ready-to-eat"}
    name = get_vietnamese_food_name(row)
    assert name != "Cereals ready-to-eat"


# ---------------------------------------------------------------------------
# 6. Sample menu report is readable in Vietnamese
# ---------------------------------------------------------------------------

def test_generated_report_contains_vietnamese_meal_names(food_map):
    food_map = _extended_food_map(food_map)
    menu = build_menu(
        food_map,
        [
            (MealType.BREAKFAST, "VN_TEST_CHEESE", 60.0),
            (MealType.LUNCH, "USDA_TEST_SALMON", 100.0),
            (MealType.DINNER, "VN_8011", 100.0),
            (MealType.SNACK, "VN_5007", 100.0),
        ],
    )
    report = build_menu_report(
        menu=menu,
        food_map=food_map,
        profile_name="Duy",
        targets={"calories": 2000.0},
    )
    text = format_menu_report(report)

    assert "Bữa sáng" in text
    assert "Bữa trưa" in text
    assert "Bữa tối" in text
    assert "Bữa phụ" in text
    assert "Cá hồi" in text
    assert "Pho mát" in text


# ---------------------------------------------------------------------------
# Additional coverage for other module functions
# ---------------------------------------------------------------------------

def test_generate_vietnamese_report_returns_vietnamese_text(food_map, profile):
    food_map = _extended_food_map(food_map)
    targets = daily_targets(profile)
    menu = build_menu(
        food_map,
        [
            (MealType.BREAKFAST, "VN_TEST_CHEESE", 60.0),
            (MealType.LUNCH, "USDA_TEST_SALMON", 100.0),
        ],
    )
    text = generate_vietnamese_report(
        menu=menu,
        food_map=food_map,
        profile=profile,
        targets=targets,
        violations=[],
    )

    assert isinstance(text, str)
    assert "BÁO CÁO THỰC ĐƠN ĐỀ XUẤT" in text
    assert "Người dùng" in text or profile.name in text
    assert "Bữa sáng" in text
    assert "Bữa trưa" in text
    assert "Pho mát" in text
    assert "Cá hồi" in text
    assert re.search(r"\bUSDA_\d+\b", text) is None
    assert re.search(r"\bVN_\d+\b", text) is None


def test_validate_menu_for_profile_returns_violations_and_flag(food_map, profile):
    targets = daily_targets(profile)
    menu = build_menu(food_map)

    # Universal bounds only (no food_map): valid_menu from conftest is feasible.
    violations, ok = validate_menu_for_profile(menu, profile, targets, food_map=None)

    assert isinstance(violations, list)
    assert isinstance(ok, bool)
    assert ok is True
    assert violations == []


def test_validate_menu_for_profile_flags_raw_ingredient_portions(food_map, profile):
    targets = daily_targets(profile)
    menu = build_menu(food_map)

    # Role-aware bounds (with food_map) flag items classified as raw ingredients.
    violations, ok = validate_menu_for_profile(menu, profile, targets, food_map=food_map)

    assert isinstance(violations, list)
    assert isinstance(ok, bool)
    assert ok is False
    assert any("portion" in v for v in violations)
