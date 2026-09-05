import pytest

from src.models.menu import Meal, MealType, Menu, MenuItem
from src.models.user_profile import ActivityLevel, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_targets


SAMPLE_ITEMS = [
    (MealType.BREAKFAST, "VN_10009", 88.0),
    (MealType.BREAKFAST, "USDA_2057257", 135.0),
    (MealType.LUNCH, "VN_1004", 171.0),
    (MealType.LUNCH, "VN_7018", 99.0),
    (MealType.DINNER, "VN_8011", 115.0),
    (MealType.DINNER, "VN_4051", 66.0),
    (MealType.SNACK, "VN_5007", 169.0),
    (MealType.SNACK, "USDA_1855534", 48.0),
]


def item_from_map(food_map: dict, food_id: str, portion_g: float) -> MenuItem:
    row = food_map[food_id]
    return MenuItem(
        food_id=food_id,
        food_name=row["food_name"],
        portion_g=portion_g,
        calories=float(row.get("calories") or 0.0),
        protein_g=float(row.get("protein_g") or 0.0),
        carbs_g=float(row.get("carbs_g") or 0.0),
        fat_g=float(row.get("fat_g") or 0.0),
        fiber_g=float(row.get("fiber_g") or 0.0),
        sodium_mg=float(row.get("sodium_mg") or 0.0),
        calcium_mg=float(row.get("calcium_mg") or 0.0),
        iron_mg=float(row.get("iron_mg") or 0.0),
        vitamin_c_mg=float(row.get("vitamin_c_mg") or 0.0),
        meal_type=str(row.get("meal_type") or ""),
    )


def build_menu(food_map: dict, spec: list[tuple[MealType, str, float]] | None = None) -> Menu:
    spec = spec or SAMPLE_ITEMS
    menu = Menu()
    grouped: dict[MealType, list[MenuItem]] = {meal_type: [] for meal_type in MealType}
    for meal_type, food_id, portion_g in spec:
        grouped[meal_type].append(item_from_map(food_map, food_id, portion_g))
    for meal_type, items in grouped.items():
        menu.meals[meal_type] = Meal(meal_type, items)
    return menu


@pytest.fixture(scope="session")
def food_df():
    return load_food_db()


@pytest.fixture(scope="session")
def food_map(food_df):
    return build_food_map(food_df)


@pytest.fixture
def profile():
    return UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        height_cm=170,
        weight_kg=65,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        allergies=[],
        dislikes=[],
        meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 2},
    )


@pytest.fixture
def targets(profile):
    return daily_targets(profile)


@pytest.fixture
def valid_menu(food_map):
    return build_menu(food_map)
