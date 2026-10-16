"""Tests for Culinary Realism and Meal Slot Structure."""

from src.models.dish_category import DishRole
from src.models.meal_structure import create_meal_slots, build_structured_pools
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile


def test_create_meal_slots_composition():
    """Ensure meal slots enforce balanced meal composition (Staple + Protein + Veg)."""
    meal_counts = {"breakfast": 2, "lunch": 3, "dinner": 2, "snack": 1}
    slots = create_meal_slots(meal_counts)

    assert len(slots) == 8

    # Check lunch structure: 1 Staple, 1 Main Protein, 1 Vegetable
    lunch_slots = [s for s in slots if s.meal_name == "lunch"]
    assert len(lunch_slots) == 3
    assert lunch_slots[0].primary_role == DishRole.STAPLE
    assert lunch_slots[1].primary_role == DishRole.MAIN_PROTEIN
    assert lunch_slots[2].primary_role == DishRole.VEGETABLE

    # Check snack structure
    snack_slots = [s for s in slots if s.meal_name == "snack"]
    assert len(snack_slots) == 1
    assert snack_slots[0].primary_role == DishRole.FRUIT_SNACK


def test_build_structured_pools_filters_junk():
    """Ensure pools discard raw ingredients and respect slot roles."""
    mock_food_map = {
        "F_RICE": {
            "food_name": "Cơm trắng",
            "category": "Lương thực",
            "source": "vietnamese",
            "dish_role": DishRole.STAPLE,
        },
        "F_BEEF": {
            "food_name": "Thịt bò xào",
            "category": "Thịt",
            "source": "vietnamese",
            "dish_role": DishRole.MAIN_PROTEIN,
        },
        "F_SPINACH": {
            "food_name": "Rau muống luộc",
            "category": "Rau",
            "source": "vietnamese",
            "dish_role": DishRole.VEGETABLE,
        },
        "F_EGG_POWDER": {
            "food_name": "Bột trứng",
            "category": "Nguyên liệu",
            "source": "vietnamese",
            "dish_role": DishRole.RAW_INGREDIENT,
        },
    }

    profile = UserProfile(
        name="Test",
        age=20,
        gender=Gender.MALE,
        height_cm=170.0,
        weight_kg=60.0,
        activity_level=ActivityLevel.LIGHT,
        goal=Goal.MAINTAIN,
    )

    slots = create_meal_slots({"lunch": 3})
    pools = build_structured_pools(mock_food_map, slots, profile, min_pool_size=1)

    # Slot 0 (Staple) should contain rice, but NOT beef, NOT egg powder
    assert "F_RICE" in pools["lunch_0"]
    assert "F_BEEF" not in pools["lunch_0"]
    assert "F_EGG_POWDER" not in pools["lunch_0"]

    # Slot 1 (Protein) should contain beef
    assert "F_BEEF" in pools["lunch_1"]
    assert "F_EGG_POWDER" not in pools["lunch_1"]

    # Slot 2 (Vegetable) should contain spinach
    assert "F_SPINACH" in pools["lunch_2"]
    assert "F_EGG_POWDER" not in pools["lunch_2"]
