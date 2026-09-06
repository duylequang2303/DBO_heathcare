import pytest

from src.models.menu import MealType, Menu, MenuItem
from src.utils.data_loader import build_food_map, load_food_db


REQUIRED_COLUMNS = {
    "food_id",
    "food_name",
    "meal_type",
    "calories",
}


def test_load_food_db_has_expected_shape():
    df = load_food_db()

    assert len(df) >= 15000
    assert REQUIRED_COLUMNS.issubset(df.columns)
    assert df["food_id"].notna().all()
    assert df["food_name"].notna().all()
    assert df["calories"].notna().all()


def test_load_food_db_converts_missing_nutrients_to_zero(tmp_path):
    data = (
        "food_id,food_name,meal_type,calories,protein_g,"
        "carbs_g,fat_g,fiber_g,sodium_mg,calcium_mg,"
        "iron_mg,vitamin_c_mg\n"
        "F1,Food 1,all,,1,,2,,,,,\n"
    )

    csv_path = tmp_path / "food.csv"
    csv_path.write_text(data, encoding="utf-8")

    df = load_food_db(csv_path)

    for key in (
        "calories",
        "carbs_g",
        "fiber_g",
        "sodium_mg",
        "calcium_mg",
        "iron_mg",
        "vitamin_c_mg",
    ):
        assert df.loc[0, key] == 0.0

    assert df.loc[0, "protein_g"] == 1.0
    assert df.loc[0, "fat_g"] == 2.0


def test_build_food_map_uses_food_id_as_key():
    df = load_food_db()
    food_map = build_food_map(df)

    assert len(food_map) == len(df)

    row = food_map["VN_10009"]

    expected_name = df.loc[
        df["food_id"] == "VN_10009",
        "food_name",
    ].iloc[0]

    assert row["food_name"] == expected_name


def test_encode_decode_roundtrip_preserves_items(
    food_df,
    food_map,
):
    meal_counts = {
        "breakfast": 2,
        "lunch": 2,
        "dinner": 2,
        "snack": 2,
    }

    food_ids = [
        "VN_10009",
        "USDA_2057257",
        "VN_1004",
        "VN_7018",
        "VN_8011",
        "VN_4051",
        "VN_5007",
        "USDA_1855534",
    ]

    portions = [
        88.0,
        135.0,
        171.0,
        99.0,
        115.0,
        66.0,
        169.0,
        48.0,
    ]

    menu = Menu.decode(
        food_ids,
        portions,
        food_map,
        meal_counts=meal_counts,
    )

    encoded = menu.encode()

    decoded = Menu.decode(
        menu.food_ids(),
        encoded,
        food_map,
        meal_counts=menu.meal_counts(),
    )

    assert decoded.food_ids() == food_ids
    assert decoded.encode() == portions

    for meal_type in MealType:
        original = menu.meals[meal_type].items
        restored = decoded.meals[meal_type].items

        assert len(restored) == len(original)

        for before, after in zip(original, restored):
            assert after.food_id == before.food_id
            assert after.portion_g == before.portion_g


def test_decode_with_meal_counts_places_items_in_fixed_blocks(
    food_map,
):
    food_ids = [
        "VN_10009",
        "USDA_2057257",
        "VN_1004",
        "VN_7018",
        "VN_8011",
        "VN_4051",
        "VN_5007",
        "USDA_1855534",
    ]

    portions = [
        50.0,
        60.0,
        70.0,
        80.0,
        90.0,
        100.0,
        110.0,
        120.0,
    ]

    counts = {
        "breakfast": 2,
        "lunch": 2,
        "dinner": 2,
        "snack": 2,
    }

    menu = Menu.decode(
        food_ids,
        portions,
        food_map,
        meal_counts=counts,
    )

    assert [
        item.food_id
        for item in menu.meals[MealType.BREAKFAST].items
    ] == food_ids[0:2]

    assert [
        item.food_id
        for item in menu.meals[MealType.LUNCH].items
    ] == food_ids[2:4]

    assert [
        item.food_id
        for item in menu.meals[MealType.DINNER].items
    ] == food_ids[4:6]

    assert [
        item.food_id
        for item in menu.meals[MealType.SNACK].items
    ] == food_ids[6:8]


def test_decode_requires_meal_counts(food_map):
    food_ids = [
        "VN_10009",
        "USDA_2057257",
        "VN_1004",
        "VN_7018",
    ]

    portions = [80.0] * 4

    with pytest.raises(TypeError):
        Menu.decode(
            food_ids,
            portions,
            food_map,
        )


def test_decode_rejects_mismatched_vector_lengths(food_map):
    meal_counts = {
        "breakfast": 1,
        "lunch": 0,
        "dinner": 0,
        "snack": 0,
    }

    with pytest.raises(ValueError, match="same length"):
        Menu.decode(
            ["VN_10009"],
            [100.0, 120.0],
            food_map,
            meal_counts=meal_counts,
        )


def test_decode_rejects_wrong_meal_counts_total(food_map):
    with pytest.raises(
        ValueError,
        match=r"sum\(meal_counts\)",
    ):
        Menu.decode(
            [
                "VN_10009",
                "USDA_2057257",
            ],
            [
                100.0,
                100.0,
            ],
            food_map,
            meal_counts={
                "breakfast": 1,
                "lunch": 1,
                "dinner": 1,
                "snack": 1,
            },
        )


def test_decode_rejects_negative_meal_counts(food_map):
    with pytest.raises(
        ValueError,
        match="non-negative",
    ):
        Menu.decode(
            [
                "VN_10009",
            ],
            [
                100.0,
            ],
            food_map,
            meal_counts={
                "breakfast": 2,
                "lunch": -1,
                "dinner": 0,
                "snack": 0,
            },
        )


def test_menu_item_nutrient_scales_from_100g():
    item = MenuItem(
        food_id="F1",
        food_name="Test food",
        portion_g=250.0,
        calories=200.0,
    )

    assert item.nutrient("calories") == pytest.approx(
        500.0
    )


def test_decode_copies_meal_type_from_csv(food_map):
    food_ids = [
        "VN_10009",
        "USDA_2057257",
        "VN_1004",
        "VN_7018",
        "VN_8011",
        "VN_4051",
        "VN_5007",
        "USDA_1855534",
    ]

    portions = [100.0] * 8

    counts = {
        "breakfast": 2,
        "lunch": 2,
        "dinner": 2,
        "snack": 2,
    }

    menu = Menu.decode(
        food_ids,
        portions,
        food_map,
        meal_counts=counts,
    )

    assert all(
        item.meal_type == "breakfast"
        for item in menu.meals[
            MealType.BREAKFAST
        ].items
    )

    assert all(
        item.meal_type == "all"
        for item in menu.meals[
            MealType.LUNCH
        ].items
    )

    assert all(
        item.meal_type == "all"
        for item in menu.meals[
            MealType.DINNER
        ].items
    )

    assert all(
        item.meal_type == "snack"
        for item in menu.meals[
            MealType.SNACK
        ].items
    )