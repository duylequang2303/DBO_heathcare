import numpy as np

from src.models.food_sampler import sample_food_ids
from src.models.menu import Menu, MealType
from src.models.user_profile import (
    UserProfile,
    Gender,
    ActivityLevel,
    Goal,
)


def make_profile(
    allergies=None,
    dislikes=None,
    meal_counts=None,
):
    """Tạo profile P1 dùng cho test."""
    return UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        height_cm=170,
        weight_kg=65,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        allergies=allergies or [],
        dislikes=dislikes or [],
        likes=[],
        meal_counts=meal_counts or {
            "breakfast": 2,
            "lunch": 2,
            "dinner": 2,
            "snack": 2,
        },
    )


def make_food_map():
    """
    Food map giả lập để test sampler.
    Có đủ món cho breakfast, lunch/dinner và snack.
    """
    return {
        "B1": {
            "food_name": "Egg Toast",
            "meal_type": "breakfast",
        },
        "B2": {
            "food_name": "Oatmeal",
            "meal_type": "breakfast",
        },
        "B3": {
            "food_name": "Peanut Pancake",
            "meal_type": "breakfast",
        },

        "A1": {
            "food_name": "Chicken Rice",
            "meal_type": "all",
        },
        "A2": {
            "food_name": "Beef Rice",
            "meal_type": "all",
        },
        "A3": {
            "food_name": "Fish Rice",
            "meal_type": "all",
        },
        "A4": {
            "food_name": "Vegetable Rice",
            "meal_type": "all",
        },
        "A5": {
            "food_name": "Chicken Pasta",
            "meal_type": "all",
        },

        "S1": {
            "food_name": "Apple",
            "meal_type": "snack",
        },
        "S2": {
            "food_name": "Banana",
            "meal_type": "snack",
        },
        "S3": {
            "food_name": "Yogurt",
            "meal_type": "snack",
        },
    }


def test_length_matches_meal_counts():
    """1. P1 phải có tổng cộng 8 food_ids."""
    food_map = make_food_map()
    profile = make_profile()

    rng = np.random.default_rng(7000)

    food_ids = sample_food_ids(
        food_map,
        profile.meal_counts,
        profile,
        rng,
    )

    assert len(food_ids) == sum(profile.meal_counts.values())
    assert len(food_ids) == 8


def test_same_seed_same_food_ids():
    """2. Cùng seed phải cho cùng kết quả."""
    food_map = make_food_map()
    profile = make_profile()

    result_1 = sample_food_ids(
        food_map,
        profile.meal_counts,
        profile,
        np.random.default_rng(7000),
    )

    result_2 = sample_food_ids(
        food_map,
        profile.meal_counts,
        profile,
        np.random.default_rng(7000),
    )

    assert result_1 == result_2


def test_no_duplicate_food_ids():
    """3. Không được trùng food_id trong một ngày."""
    food_map = make_food_map()
    profile = make_profile()

    food_ids = sample_food_ids(
        food_map,
        profile.meal_counts,
        profile,
        np.random.default_rng(7000),
    )

    assert len(food_ids) == len(set(food_ids))


def test_allergy_food_is_excluded():
    """4. Profile dị ứng peanut không được chọn món peanut."""
    food_map = make_food_map()

    profile = make_profile(
        allergies=["peanut"],
        meal_counts={
            "breakfast": 2,
            "lunch": 1,
            "dinner": 1,
            "snack": 1,
        },
    )

    food_ids = sample_food_ids(
        food_map,
        profile.meal_counts,
        profile,
        np.random.default_rng(7000),
    )

    selected_names = [
        food_map[food_id]["food_name"].lower()
        for food_id in food_ids
    ]

    assert all(
        "peanut" not in name
        for name in selected_names
    )


def test_breakfast_and_snack_meal_types():
    """5. Breakfast và snack phải lấy đúng meal_type."""
    food_map = make_food_map()
    profile = make_profile()

    food_ids = sample_food_ids(
        food_map,
        profile.meal_counts,
        profile,
        np.random.default_rng(7000),
    )

    # P1 có 2 breakfast đầu tiên.
    breakfast_ids = food_ids[0:2]

    # Sau breakfast(2), lunch(2), dinner(2)
    # thì 2 phần tử cuối là snack.
    snack_ids = food_ids[6:8]

    for food_id in breakfast_ids:
        assert (
            food_map[food_id]["meal_type"]
            == "breakfast"
        )

    for food_id in snack_ids:
        assert (
            food_map[food_id]["meal_type"]
            == "snack"
        )


def test_snack_zero_round_trip_decode():
    """
    6. meal_counts có snack=0 vẫn phải decode
    thành Menu được.
    """
    food_map = make_food_map()

    meal_counts = {
        "breakfast": 2,
        "lunch": 2,
        "dinner": 2,
        "snack": 0,
    }

    profile = make_profile(
        meal_counts=meal_counts,
    )

    food_ids = sample_food_ids(
        food_map,
        meal_counts,
        profile,
        np.random.default_rng(7000),
    )

    portions_g = [100.0] * len(food_ids)

    menu = Menu.decode(
        food_ids=food_ids,
        portions_g=portions_g,
        food_map=food_map,
        meal_counts=meal_counts,
    )

    assert len(food_ids) == 6

    assert menu.food_ids() == food_ids

    assert len(
        menu.meals[MealType.SNACK].items
    ) == 0

    assert menu.meal_counts() == meal_counts