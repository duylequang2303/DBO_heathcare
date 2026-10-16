"""Dish Categorization and Culinary Role Taxonomy.

Classifies foods into realistic meal roles (Staple, Main Protein, Vegetable,
Soup, Fruit/Snack, or Raw Ingredient) and defines natural portion bounds.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Tuple


class DishRole(str, Enum):
    """Culinary role of a food item within a balanced meal."""
    STAPLE = "staple"                  # Cơm, bún, phở, mì, bánh mì, khoai, yến mạch
    MAIN_PROTEIN = "main_protein"      # Thịt, cá, tôm, trứng, đậu phụ chế biến
    VEGETABLE = "vegetable"            # Rau xào, rau luộc, dưa leo, salad
    SOUP = "soup"                      # Canh, súp
    FRUIT_SNACK = "fruit_snack"        # Trái cây, sữa chua, sữa, hạt
    RAW_INGREDIENT = "raw_ingredient"  # Nguyên liệu thô công nghiệp, không ăn trực tiếp
    BEVERAGE = "beverage"              # Đồ uống, nước ép, trà


# Natural realistic portion bounds (min_g, max_g) per role
ROLE_PORTION_BOUNDS: dict[DishRole, Tuple[float, float]] = {
    DishRole.STAPLE: (100.0, 250.0),
    DishRole.MAIN_PROTEIN: (60.0, 180.0),
    DishRole.VEGETABLE: (80.0, 220.0),
    DishRole.SOUP: (100.0, 350.0),
    DishRole.FRUIT_SNACK: (50.0, 200.0),
    DishRole.RAW_INGREDIENT: (0.0, 0.0),
    DishRole.BEVERAGE: (100.0, 300.0),
}


# Keywords that identify raw industrial ingredients or unpalatable items in daily menus
RAW_JUNK_PATTERNS = [
    r"\bbột trứng\b",
    r"\bbột (mì|năng|gạo|bắp|sắn|nở|béo|bắp|ngô)\b",
    r"\bmen\b",
    r"\bphụ gia\b",
    r"\btinh bột\b",
    r"\bshortening\b",
    r"\braw\b",
    r"\bunprepared\b",
    r"\bdried, uncooked\b",
    r"\bdry, uncooked\b",
    r"\buncooked\b",
    r"\bpowder\b",
    r"\bextract\b",
    r"\bflavoring\b",
    r"\bbaking\b",
    r"\bindustrial\b",
    r"\bgrain,.*raw\b",
    r"\bflour\b",
]

RAW_JUNK_REGEX = re.compile("|".join(RAW_JUNK_PATTERNS), re.IGNORECASE)


def is_raw_or_industrial_junk(food_name: str, category: str = "") -> bool:
    """Return True if food item is a raw industrial ingredient or unfit for direct meal eating."""
    combined = f"{food_name} {category}".strip()
    return bool(RAW_JUNK_REGEX.search(combined))


# Keyword mappings for Vietnamese dishes & USDA
STAPLE_PATTERNS = re.compile(
    r"\b(cơm|gạo|bún|phở|mì|miến|bánh mì|khoai|ngô|yến mạch|oatmeal|rice, cooked|noodles, cooked|pasta, cooked|bread)\b",
    re.IGNORECASE,
)

PROTEIN_PATTERNS = re.compile(
    r"\b(thịt|bò|heo|lợn|gà|vịt|cá|tôm|cua|mực|trứng|đậu phụ|chả|giò|xúc xích|sườn|beef|chicken|pork|fish|salmon|tuna|turkey|egg|tofu|shrimp)\b",
    re.IGNORECASE,
)

SOUP_PATTERNS = re.compile(
    r"\b(canh|súp|soup|broth|cháo)\b",
    re.IGNORECASE,
)

VEGETABLE_PATTERNS = re.compile(
    r"\b(rau|cải|muống|ngót|dền|mồng tơi|xà lách|dưa leo|cà chua|bí|bầu|mướp|súp lơ|bông cải|nấm|đậu cô ve|vegetable|salad|spinach|broccoli|cucumber)\b",
    re.IGNORECASE,
)

SNACK_PATTERNS = re.compile(
    r"\b(quả|trái|chuối|táo|cam|bưởi|xoài|dưa|nho|ổi|sữa chua|sữa chua|sữa tươi|hạt|fruit|yogurt|apple|banana|orange|milk|almond|walnut)\b",
    re.IGNORECASE,
)


def classify_dish_role(food_name: str, category: str = "", source: str = "vietnamese") -> DishRole:
    """Classify a food item into its primary culinary DishRole."""
    name_clean = food_name.strip().lower()
    cat_clean = category.strip().lower()

    if is_raw_or_industrial_junk(name_clean, cat_clean):
        return DishRole.RAW_INGREDIENT

    # 1. Soup / Canh
    if SOUP_PATTERNS.search(name_clean) or "soup" in cat_clean:
        return DishRole.SOUP

    # 2. Main Protein / Món mặn
    if PROTEIN_PATTERNS.search(name_clean) or any(k in cat_clean for k in ["beef", "poultry", "pork", "seafood", "fish"]):
        return DishRole.MAIN_PROTEIN

    # 3. Vegetables / Rau xào, rau luộc, salad
    if VEGETABLE_PATTERNS.search(name_clean) or "vegetable" in cat_clean:
        return DishRole.VEGETABLE

    # 4. Staples / Tinh bột
    if STAPLE_PATTERNS.search(name_clean) or any(k in cat_clean for k in ["rice", "bread", "cereal", "pasta"]):
        return DishRole.STAPLE

    # 5. Snack / Fruit
    if SNACK_PATTERNS.search(name_clean) or any(k in cat_clean for k in ["fruit", "dairy", "yogurt", "nuts"]):
        return DishRole.FRUIT_SNACK

    # Fallback heuristic: default to STAPLE or MAIN_PROTEIN based on source
    if source == "vietnamese":
        return DishRole.MAIN_PROTEIN
    return DishRole.STAPLE


def get_role_portion_bounds(role: DishRole) -> Tuple[float, float]:
    """Retrieve natural minimum and maximum portion bounds in grams for a given role."""
    return ROLE_PORTION_BOUNDS.get(role, (50.0, 250.0))
