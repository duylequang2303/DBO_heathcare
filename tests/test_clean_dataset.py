"""Tests for Dataset Cleaning Pipeline (scripts/clean_dataset.py)."""

from pathlib import Path
import pandas as pd
import pytest

from scripts.clean_dataset import filter_dataset, DEFAULT_OUTPUT, DEFAULT_REPORT


def test_filter_dataset_removes_extreme_sodium():
    """Ensure sodium values exceeding physical threshold are removed."""
    mock_df = pd.DataFrame([
        {"food_id": "GOOD_1", "food_name": "Cá hấp hành gừng", "category": "Cá", "source": "vietnamese", "calories": 120.0, "protein_g": 20.0, "carbs_g": 2.0, "fat_g": 3.0, "fiber_g": 0.5, "sodium_mg": 250.0},
        {"food_id": "BAD_NA", "food_name": "Anchovies In Olive Oil", "category": "Fish", "source": "usda", "calories": 210.0, "protein_g": 28.0, "carbs_g": 0.0, "fat_g": 10.0, "fiber_g": 0.0, "sodium_mg": 4690000.0},
    ])
    clean_df, dropped = filter_dataset(mock_df, max_sodium=3000.0)
    assert len(clean_df) == 1
    assert clean_df.iloc[0]["food_id"] == "GOOD_1"
    assert "1_sodium_outliers" in dropped
    assert len(dropped["1_sodium_outliers"]) == 1


def test_filter_dataset_removes_raw_animal_meats():
    """Ensure raw/uncooked meat, poultry, quail, organs are removed."""
    mock_df = pd.DataFrame([
        {"food_id": "F1", "food_name": "Quail, breast, meat only, raw", "category": "Poultry", "source": "usda", "calories": 134.0, "protein_g": 22.0, "carbs_g": 0.0, "fat_g": 4.5, "fiber_g": 0.0, "sodium_mg": 50.0},
        {"food_id": "F2", "food_name": "Chicken, breast, raw", "category": "Poultry", "source": "usda", "calories": 120.0, "protein_g": 22.5, "carbs_g": 0.0, "fat_g": 2.6, "fiber_g": 0.0, "sodium_mg": 65.0},
        {"food_id": "F3", "food_name": "Tiết lợn sống", "category": "Thịt", "source": "vietnamese", "calories": 25.0, "protein_g": 4.5, "carbs_g": 0.2, "fat_g": 0.1, "fiber_g": 0.0, "sodium_mg": 80.0},
        {"food_id": "F4", "food_name": "Gà luộc chín", "category": "Thịt", "source": "vietnamese", "calories": 200.0, "protein_g": 25.0, "carbs_g": 0.0, "fat_g": 10.0, "fiber_g": 0.0, "sodium_mg": 70.0},
    ])
    clean_df, dropped = filter_dataset(mock_df)
    assert len(clean_df) == 1
    assert clean_df.iloc[0]["food_id"] == "F4"
    assert len(dropped["6_raw_animal_meats"]) == 3


def test_filter_dataset_preserves_raw_fruits_and_greens():
    """Raw fresh fruits and salad greens should be safely kept."""
    mock_df = pd.DataFrame([
        {"food_id": "APPLE", "food_name": "Apples, raw, with skin", "category": "Fruits and Fruit Juices", "source": "usda", "calories": 52.0, "protein_g": 0.3, "carbs_g": 13.8, "fat_g": 0.2, "fiber_g": 2.4, "sodium_mg": 1.0},
        {"food_id": "BANANA", "food_name": "Bananas, raw", "category": "Fruits and Fruit Juices", "source": "usda", "calories": 89.0, "protein_g": 1.1, "carbs_g": 22.8, "fat_g": 0.3, "fiber_g": 2.6, "sodium_mg": 1.0},
        {"food_id": "LETTUCE", "food_name": "Lettuce, iceberg, raw", "category": "Vegetables and Vegetable Products", "source": "usda", "calories": 14.0, "protein_g": 0.9, "carbs_g": 3.0, "fat_g": 0.1, "fiber_g": 1.2, "sodium_mg": 10.0},
    ])
    clean_df, dropped = filter_dataset(mock_df)
    assert len(clean_df) == 3


def test_filter_dataset_enforces_mass_conservation():
    """Macros > 100g or sum > 105g must be flagged and removed."""
    mock_df = pd.DataFrame([
        {"food_id": "M1", "food_name": "Impossible Protein Noodles", "category": "Pasta", "source": "usda", "calories": 350.0, "protein_g": 131.0, "carbs_g": 20.0, "fat_g": 2.0, "fiber_g": 1.0, "sodium_mg": 100.0},
        {"food_id": "M2", "food_name": "Impossible Dense Bar", "category": "Snack", "source": "usda", "calories": 500.0, "protein_g": 50.0, "carbs_g": 60.0, "fat_g": 40.0, "fiber_g": 5.0, "sodium_mg": 100.0},
        {"food_id": "M3", "food_name": "Normal Bread", "category": "Breads", "source": "usda", "calories": 265.0, "protein_g": 9.0, "carbs_g": 49.0, "fat_g": 3.2, "fiber_g": 2.7, "sodium_mg": 490.0},
    ])
    clean_df, dropped = filter_dataset(mock_df)
    assert len(clean_df) == 1
    assert clean_df.iloc[0]["food_id"] == "M3"
    assert len(dropped["3_mass_conservation_violations"]) == 2


def test_cleaned_dataset_file_conforms_to_specs():
    """Verify that the generated cleaned CSV satisfies all physical constraints."""
    assert DEFAULT_OUTPUT.exists(), "Cleaned dataset CSV must exist"
    assert DEFAULT_REPORT.exists(), "Cleaning report markdown must exist"

    df = pd.read_csv(DEFAULT_OUTPUT)
    assert len(df) > 10000

    # Physical checks
    assert df["sodium_mg"].max() <= 3000.0
    assert df["calories"].max() <= 900.0
    assert (df["protein_g"] > 100.0).sum() == 0
    assert (df["carbs_g"] > 100.0).sum() == 0
    assert (df["fat_g"] > 100.0).sum() == 0

    pcf = df["protein_g"].fillna(0) + df["carbs_g"].fillna(0) + df["fat_g"].fillna(0)
    assert (pcf > 105.0).sum() == 0

    # No negative values
    for col in ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sodium_mg"]:
        assert (df[col] < 0).sum() == 0
