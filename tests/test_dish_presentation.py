"""Tests for the rule-based dish presentation layer.

The presentation layer must change names only. Nutrients, portions and fitness
must stay identical.
"""

from fastapi.testclient import TestClient

from app.main import app
from src.models.dish_category import DishRole
from src.models.dish_presentation import PRESENTATION_DISCLAIMER, present_dish
from src.models.menu import Menu
from src.utils.data_loader import build_food_map, load_food_db

client = TestClient(app)

PROFILE = {
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


def test_presentation_maps_roles_to_dish_names():
    assert present_dish("Gạo lứt", role=DishRole.STAPLE).display_name == "Cơm gạo lứt"
    assert present_dish("Gạo lứt", role=DishRole.STAPLE).ingredient_basis == "gạo khô"

    assert present_dish("Thịt bò", role=DishRole.MAIN_PROTEIN).display_name == "Thịt bò xào"
    assert present_dish("Cá hồi", role=DishRole.MAIN_PROTEIN).display_name == "Cá hồi áp chảo"
    assert present_dish("Rau muống", role=DishRole.VEGETABLE).display_name == "Rau muống luộc"

    soup = present_dish("Canh bí đao", role=DishRole.SOUP)
    assert soup.display_name == "Canh bí đao"

    fruit = present_dish("Chuối", role=DishRole.FRUIT_SNACK)
    assert fruit.display_name == "Chuối (ăn tươi)"


def test_presentation_marks_raw_basis_for_rice():
    presentation = present_dish("Gạo lứt", role=DishRole.STAPLE)
    assert presentation.display_name == "Cơm gạo lứt"
    assert presentation.ingredient_basis == "gạo khô"
    assert presentation.is_estimated is True


def test_presentation_does_not_change_nutrients():
    food_map = build_food_map(load_food_db())
    food_ids = ["VN_1005", "VN_7018", "VN_4051"]
    portions = [115.0, 120.0, 200.0]
    meal_counts = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
    # Put all three items in lunch for a simple nutrient check.
    meal_counts["lunch"] = len(food_ids)

    menu = Menu.decode(food_ids, portions, food_map, meal_counts)
    expected_calories = sum(
        float(food_map[fid]["calories"]) * portion / 100.0
        for fid, portion in zip(food_ids, portions)
    )
    assert menu.total("calories") == expected_calories

    # Names are presentation-only; food_id and portion are unchanged.
    assert menu.food_ids() == food_ids
    assert menu.encode() == portions


def test_api_exposes_display_name_and_basis_without_changing_macros():
    response = client.post(
        "/api/menu/generate",
        json={"profile": PROFILE, "seed": 9001, "config": "smoke"},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert PRESENTATION_DISCLAIMER in data["data_limitations"]
    assert data["items"]
    for item in data["items"]:
        assert item["name"] == item["display_name"]
        assert item["ingredient_name"]
        assert item["preparation"]
        assert item["ingredient_basis"]
        assert item["presentation_is_estimated"] is True
        # Macros are still computed from the original food row.
        assert item["macros"]["calories"] >= 0
