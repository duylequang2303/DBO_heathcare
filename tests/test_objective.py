from src.models.menu import Meal, MealType, Menu
from src.models.objective import FITNESS_MAX, FITNESS_MIN, WEIGHTS, evaluate, evaluate_breakdown
from src.models.user_profile import ActivityLevel, Gender, Goal, UserProfile
from tests.conftest import item_from_map


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_fitness_range_on_valid_and_random(valid_menu, profile, targets, food_map):
    valid = evaluate(valid_menu, profile, targets)
    random_menu = Menu()
    ids = list(food_map.keys())[:8]
    for i, meal_type in enumerate(MealType):
        items = [
            item_from_map(food_map, ids[i * 2], 10.0),
            item_from_map(food_map, ids[i * 2 + 1], 500.0),
        ]
        random_menu.meals[meal_type] = Meal(meal_type, items)
    random_score = evaluate(random_menu, profile, targets)
    assert FITNESS_MIN <= valid <= FITNESS_MAX
    assert FITNESS_MIN <= random_score <= FITNESS_MAX
    assert valid > random_score


def test_preference_drops_when_disliked(valid_menu, profile, targets):
    before = evaluate_breakdown(valid_menu, profile, targets)["preference"]
    profile.dislikes = ["lợn", "bagel"]
    after = evaluate_breakdown(valid_menu, profile, targets)["preference"]
    assert after < before


def test_diversity_perfect_when_unique(valid_menu, profile, targets):
    breakdown = evaluate_breakdown(valid_menu, profile, targets)
    assert breakdown["diversity"] == 100.0


def test_likes_on_user_profile_raise_preference(valid_menu, targets):
    counts = {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 2}
    unmatched = UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        height_cm=170,
        weight_kg=65,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        likes=["pizza"],
        meal_counts=counts,
    )
    matched = UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        height_cm=170,
        weight_kg=65,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        likes=["ca hoi", "chuoi"],
        meal_counts=counts,
    )
    matched.likes = ["cá hồi", "chuối"]
    unmatched_score = evaluate_breakdown(valid_menu, unmatched, targets)["preference"]
    matched_score = evaluate_breakdown(valid_menu, matched, targets)["preference"]
    assert matched_score > unmatched_score
