from src.models.constraints import (
    PORTION_RANGE,
    is_feasible,
    validate_menu,
)
from src.models.menu import MealType
from tests.conftest import build_menu, item_from_map


def test_feasible_when_all_constraints_pass(valid_menu, profile, targets):
    assert is_feasible(valid_menu, profile, targets)


def test_no_duplicate_in_valid_menu(valid_menu, profile, targets):
    issues = validate_menu(valid_menu, profile, targets)
    assert not any("duplicate" in msg for msg in issues)


def test_portion_min_and_max_inclusive(valid_menu, profile, targets):
    valid_menu.meals[MealType.SNACK].items[0].portion_g = PORTION_RANGE["min"]
    valid_menu.meals[MealType.SNACK].items[1].portion_g = PORTION_RANGE["max"]
    issues = [msg for msg in validate_menu(valid_menu, profile, targets) if "portion" in msg]
    assert issues == []


def test_duplicate_name_same_day(valid_menu, profile, targets, food_map):
    extra = item_from_map(food_map, "VN_1004", 80)
    extra.food_id = "VN_1004_COPY"
    valid_menu.meals[MealType.DINNER].add_item(extra)
    profile.meal_counts["dinner"] = 3
    issues = validate_menu(valid_menu, profile, targets)
    assert any("duplicate food_name" in msg for msg in issues)


def test_lunch_rejects_breakfast_item(food_map, profile, targets):
    menu = build_menu(
        food_map,
        [
            (MealType.BREAKFAST, "VN_10009", 80.0),
            (MealType.BREAKFAST, "USDA_2057257", 120.0),
            (MealType.LUNCH, "VN_10009", 80.0),
            (MealType.LUNCH, "VN_7018", 120.0),
            (MealType.DINNER, "VN_8011", 120.0),
            (MealType.DINNER, "VN_4051", 60.0),
            (MealType.SNACK, "VN_5007", 120.0),
            (MealType.SNACK, "USDA_1855534", 40.0),
        ],
    )
    issues = validate_menu(menu, profile, targets)
    assert any("not allowed in lunch" in msg for msg in issues)
