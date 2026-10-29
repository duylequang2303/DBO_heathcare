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


def test_hypertension_rejects_sodium_above_profile_limit(valid_menu, profile, targets):
    profile.medical_conditions = ["hypertension"]
    targets["sodium_mg"] = 1.0
    issues = validate_menu(valid_menu, profile, targets)
    assert any("sodium_mg" in msg and "exceeds" in msg for msg in issues)


def test_healthy_profile_does_not_apply_hypertension_limit(valid_menu, profile, targets):
    """Healthy profile conforms to CDRR limit (2300 mg) and passes with valid menu (~1411 mg)."""
    profile.medical_conditions = ["healthy"]
    targets["sodium_mg"] = 2300.0
    issues = validate_menu(valid_menu, profile, targets)
    assert not any("sodium_mg" in msg for msg in issues)


def test_healthy_profile_rejects_sodium_above_general_ceiling(valid_menu, profile, targets):
    """Healthy profile rejects sodium exceeding the general CDRR / target limit."""
    profile.medical_conditions = ["healthy"]
    targets["sodium_mg"] = 1000.0
    issues = validate_menu(valid_menu, profile, targets)
    assert any("sodium_mg" in msg and "exceeds" in msg for msg in issues)


def test_sodium_default_ceiling_when_unspecified_in_targets(valid_menu, profile, targets):
    """When targets dictionary lacks sodium_mg, default CDRR ceiling (2300 mg) is enforced."""
    profile.medical_conditions = ["healthy"]
    targets.pop("sodium_mg", None)
    issues = validate_menu(valid_menu, profile, targets)
    assert not any("sodium_mg" in msg for msg in issues)


def test_hypertension_caps_sodium_at_1500_even_when_targets_specifies_higher(valid_menu, profile, targets, food_map):
    """Hypertension profile must clamp sodium at 1500 mg even if targets has general 2300 mg."""
    profile.medical_conditions = ["hypertension"]
    targets["sodium_mg"] = 2300.0  # Common default from daily_all_targets
    # valid_menu sodium is ~1411 mg; add extra salty item to push it to ~1800 mg (>1500, <2300)
    extra = item_from_map(food_map, "VN_1004", 50)
    extra.food_id = "EXTRA_SALT"
    extra.sodium_mg = 400.0
    valid_menu.meals[MealType.SNACK].add_item(extra)
    profile.meal_counts["snack"] = 3
    issues = validate_menu(valid_menu, profile, targets)
    assert any("sodium_mg" in msg and "exceeds 1500.0" in msg for msg in issues)


def test_hypertension_honors_stricter_clinical_target(valid_menu, profile, targets):
    """If clinician specifies stricter target (<1500 mg, e.g. 1200 mg), it is respected."""
    profile.medical_conditions = ["hypertension"]
    targets["sodium_mg"] = 1200.0
    issues = validate_menu(valid_menu, profile, targets)
    assert any("sodium_mg" in msg and "exceeds 1200.0" in msg for msg in issues)


def test_healthy_profile_caps_sodium_at_upper_tolerance_ceiling(valid_menu, profile, targets, food_map):
    """Even if targets specifies an excessive sodium allowance (e.g. 5000 mg), upper tolerance ceiling (3000 mg) is enforced."""
    profile.medical_conditions = ["healthy"]
    targets["sodium_mg"] = 5000.0
    extra = item_from_map(food_map, "VN_1004", 100)
    extra.food_id = "VERY_SALTY"
    extra.food_name = "Muối biển"
    extra.meal_type = "snack"
    extra.sodium_mg = 4000.0  # 4000 mg per 100g -> 4000 mg sodium
    valid_menu.meals[MealType.SNACK].add_item(extra)
    profile.meal_counts["snack"] = 3
    # Total sodium is ~1411 + 4000 = ~5411 mg (> 3000 mg ceiling, but < 5000 mg target)
    issues = validate_menu(valid_menu, profile, targets)
    assert any("sodium_mg" in msg and "exceeds 3000.0" in msg for msg in issues)

