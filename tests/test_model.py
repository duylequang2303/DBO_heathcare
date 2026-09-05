import random

from src.models.constraints import (
    PORTION_RANGE,
    is_feasible,
    validate_menu,
)
from src.models.menu import Meal, MealType, Menu
from src.models.objective import FITNESS_MAX, FITNESS_MIN, evaluate, evaluate_breakdown
from tests.conftest import SAMPLE_ITEMS, build_menu, item_from_map


def test_load_real_food_db(food_df):
    assert len(food_df) >= 15000
    assert "food_id" in food_df.columns
    assert food_df["calories"].notna().all()


def test_valid_sample_menu_is_feasible(valid_menu, profile, targets):
    violations = validate_menu(valid_menu, profile, targets)
    assert violations == []
    assert is_feasible(valid_menu, profile, targets)


def test_valid_menu_nutrition_in_range(valid_menu, targets):
    calories = valid_menu.total("calories")
    assert targets["calories"] * 0.9 <= calories <= targets["calories"] * 1.1
    assert valid_menu.total("protein_g") > 0
    assert valid_menu.total("fiber_g") > 0


def test_fitness_is_clamped(valid_menu, profile, targets):
    fitness = evaluate(valid_menu, profile, targets)
    assert FITNESS_MIN <= fitness <= FITNESS_MAX


def test_valid_menu_outperforms_random_menu(valid_menu, profile, targets, food_map):
    valid_score = evaluate(valid_menu, profile, targets)
    random_menu = _random_menu(food_map, seed=7)
    random_score = evaluate(random_menu, profile, targets)
    assert valid_score > random_score
    assert valid_score > 0
    assert random_score < valid_score - 20


def test_duplicate_food_is_violation(valid_menu, profile, targets, food_map):
    item = item_from_map(food_map, "VN_10009", 50)
    valid_menu.meals[MealType.LUNCH].add_item(item)
    profile.meal_counts["lunch"] = 3
    issues = validate_menu(valid_menu, profile, targets)
    assert any("duplicate" in msg for msg in issues)


def test_dislike_is_violation(valid_menu, profile, targets):
    profile.dislikes = ["lợn"]
    issues = validate_menu(valid_menu, profile, targets)
    assert any("disliked" in msg for msg in issues)


def test_allergy_is_violation(valid_menu, profile, targets):
    profile.allergies = ["pho mát"]
    issues = validate_menu(valid_menu, profile, targets)
    assert any("allergen" in msg for msg in issues)


def test_portion_out_of_range(valid_menu, profile, targets):
    valid_menu.meals[MealType.SNACK].items[0].portion_g = PORTION_RANGE["max"] + 20
    issues = validate_menu(valid_menu, profile, targets)
    assert any("portion" in msg for msg in issues)


def test_wrong_item_count(valid_menu, profile, targets):
    profile.meal_counts["breakfast"] = 1
    issues = validate_menu(valid_menu, profile, targets)
    assert any("breakfast" in msg and "expected 1" in msg for msg in issues)


def test_meal_type_mismatch(food_map, profile, targets):
    snack_id = "VN_5007"
    menu = build_menu(
        food_map,
        [
            (MealType.BREAKFAST, snack_id, 100.0),
            (MealType.BREAKFAST, "VN_10009", 80.0),
            (MealType.LUNCH, "VN_1004", 150.0),
            (MealType.LUNCH, "VN_7018", 120.0),
            (MealType.DINNER, "VN_8011", 120.0),
            (MealType.DINNER, "VN_4051", 60.0),
            (MealType.SNACK, "USDA_1855534", 40.0),
            (MealType.SNACK, "VN_5007", 120.0),
        ],
    )
    issues = validate_menu(menu, profile, targets)
    assert any("not allowed in breakfast" in msg for msg in issues)


def test_encode_decode_roundtrip(valid_menu, food_map):
    food_ids = [item.food_id for item in valid_menu.all_items()]
    portions = valid_menu.encode()
    decoded = Menu.decode(food_ids, portions, food_map)
    assert [i.food_id for i in decoded.all_items()] == food_ids
    assert decoded.encode() == portions


def test_objective_breakdown_keys(valid_menu, profile, targets):
    breakdown = evaluate_breakdown(valid_menu, profile, targets)
    for key in ("energy", "macros", "preference", "diversity", "penalty", "fitness"):
        assert key in breakdown
    assert breakdown["penalty"] == 0
    assert breakdown["n_violations"] == 0
    assert 0 <= breakdown["weighted"] <= 100


def test_empty_menu_has_low_fitness(profile, targets):
    empty = Menu()
    profile.meal_counts = {k: 0 for k in profile.meal_counts}
    score = evaluate(empty, profile, targets)
    assert score < 0


def test_end_to_end_profile_to_score(food_df, food_map, profile, targets):
    assert len(food_df) > 0
    assert daily_targets_positive(targets)
    menu = build_menu(food_map, SAMPLE_ITEMS)
    assert menu.all_items()
    fitness = evaluate(menu, profile, targets)
    assert FITNESS_MIN <= fitness <= FITNESS_MAX
    assert is_feasible(menu, profile, targets)


def daily_targets_positive(targets: dict[str, float]) -> bool:
    required = ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g")
    return all(targets.get(key, 0) > 0 for key in required)


def _random_menu(food_map: dict, seed: int = 0) -> Menu:
    rng = random.Random(seed)
    ids = list(food_map.keys())
    menu = Menu()
    for meal_type in MealType:
        items = []
        for _ in range(2):
            food_id = rng.choice(ids)
            portion = rng.uniform(10.0, 500.0)
            items.append(item_from_map(food_map, food_id, portion))
        menu.meals[meal_type] = Meal(meal_type, items)
    return menu
