"""Tests for Data Integrity and Schema Validation."""

import pytest

from src.models.dish_category import (
    DishRole,
    classify_dish_role,
    is_raw_or_industrial_junk,
    get_role_portion_bounds,
)
from src.models.food_schema import FoodItemSchema


def test_food_schema_valid():
    """Test valid FoodItemSchema creation."""
    item = FoodItemSchema(
        food_id="VN_001",
        food_name="Cơm trắng",
        calories=130.0,
        protein_g=2.7,
        carbs_g=28.2,
        fat_g=0.3,
        fiber_g=0.4,
        dish_role=DishRole.STAPLE,
    )
    assert item.food_id == "VN_001"
    assert item.dish_role == DishRole.STAPLE
    bounds = item.portion_bounds()
    assert bounds[0] <= 150.0 <= bounds[1]


def test_food_schema_negative_calories_raises():
    """Nutrients cannot be negative."""
    with pytest.raises(ValueError, match="must be non-negative"):
        FoodItemSchema(
            food_id="BAD_1",
            food_name="Bad Food",
            calories=-50.0,
            protein_g=10.0,
            carbs_g=20.0,
            fat_g=5.0,
            fiber_g=2.0,
        )


def test_food_schema_excessive_calories_raises():
    """Calories per 100g cannot exceed theoretical 1000 kcal."""
    with pytest.raises(ValueError, match="exceeds theoretical maximum"):
        FoodItemSchema(
            food_id="BAD_2",
            food_name="Super Dense Food",
            calories=1200.0,
            protein_g=10.0,
            carbs_g=20.0,
            fat_g=5.0,
            fiber_g=2.0,
        )


def test_detect_raw_industrial_junk():
    """Test filtering of raw or unpalatable items."""
    assert is_raw_or_industrial_junk("Bột trứng") is True
    assert is_raw_or_industrial_junk("Bột mì đa dụng") is True
    assert is_raw_or_industrial_junk("Sorghum grain, raw") is True
    assert is_raw_or_industrial_junk("Chicken breast, raw") is True
    assert is_raw_or_industrial_junk("Shortening, industrial") is True

    # Real edible foods must not be flagged as junk
    assert is_raw_or_industrial_junk("Cơm trắng") is False
    assert is_raw_or_industrial_junk("Thịt bò xào rau muống") is False
    assert is_raw_or_industrial_junk("Canh chua cá lóc") is False
    assert is_raw_or_industrial_junk("Trứng gà luộc") is False
    assert is_raw_or_industrial_junk("Chuối tiêu") is False


def test_classify_dish_roles():
    """Test classification of common foods into culinary roles."""
    assert classify_dish_role("Cơm tẻ chín", "Lương thực") == DishRole.STAPLE
    assert classify_dish_role("Bún tươi", "Lương thực") == DishRole.STAPLE
    assert classify_dish_role("Thịt lợn nạc luộc", "Thịt") == DishRole.MAIN_PROTEIN
    assert classify_dish_role("Cá hồi áp chảo", "Thủy hải sản") == DishRole.MAIN_PROTEIN
    assert classify_dish_role("Rau muống luộc", "Rau") == DishRole.VEGETABLE
    assert classify_dish_role("Canh cải cúc thịt băm", "Món canh") == DishRole.SOUP
    assert classify_dish_role("Táo tây", "Quả") == DishRole.FRUIT_SNACK
    assert classify_dish_role("Bột mì thô", "Nguyên liệu") == DishRole.RAW_INGREDIENT
