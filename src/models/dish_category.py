"""Dish Categorization and Culinary Role Taxonomy.

Classifies foods into realistic meal roles (Staple, Main Protein, Vegetable,
Soup, Fruit/Snack, or Raw Ingredient) and defines natural portion bounds.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Iterable, Tuple


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
    r"\b(dầu|mỡ)\b",
    r"\b(oil|lard|margarine|butter oil)\b",
]

RAW_JUNK_REGEX = re.compile("|".join(RAW_JUNK_PATTERNS), re.IGNORECASE)

# Patterns identifying industrial products, fats/oils, or flours that are never standalone dishes
RAW_PRODUCT_PREFIX = re.compile(
    r"^(dầu|mỡ|bột|men|phụ gia|tinh bột|shortening|oil|lard|flour|baking powder)\b",
    re.IGNORECASE,
)

# Patterns identifying prepared/cooked dishes to prevent them being treated as raw
COOKED_STATE_PATTERNS = re.compile(
    r"\b(luộc|hấp|xào|nấu|cháo|chiên|rán|kho|nướng|hầm|áp chảo|sốt|rang|om|rim|quay|trộn|nộm|gỏi|canh|súp)\b",
    re.IGNORECASE,
)

DAIRY_PATTERNS = re.compile(
    r"\b(sữa|yogurt|váng sữa|phô mai|cheese)\b",
    re.IGNORECASE,
)


def is_raw_or_industrial_junk(food_name: str, category: str = "") -> bool:
    """Return True if food item is a raw industrial ingredient or unfit for direct meal eating."""
    combined = f"{food_name} {category}".strip()
    return bool(RAW_JUNK_REGEX.search(combined))


# Keyword mappings for Vietnamese dishes & USDA
STAPLE_PATTERNS = re.compile(
    r"\b(cơm|gạo|bún|phở|mì|miến|bánh mì|khoai|ngô|kê|đậu xanh|đậu tương|đậu nành|đậu đen|đậu đỏ|yến mạch|oatmeal|rice, cooked|noodles, cooked|pasta, cooked|bread)\b",
    re.IGNORECASE,
)

PROTEIN_PATTERNS = re.compile(
    r"\b(thịt|bò|heo|lợn|gà|vịt|cá|tép|ghẹ|tôm|cua|mực|trứng|đậu phụ|chả|giò|xúc xích|sườn|beef|chicken|pork|fish|salmon|tuna|turkey|egg|tofu|shrimp)\b",
    re.IGNORECASE,
)

# "súp lơ" (bông cải) là rau chứ không phải canh/súp: nếu khớp "súp" ở đây,
# món sẽ nhận trần khẩu phần của SOUP (350g) thay vì VEGETABLE (220g).
SOUP_PATTERNS = re.compile(
    r"\b(canh|súp(?!\s*lơ)|soup|broth|cháo)\b",
    re.IGNORECASE,
)

VEGETABLE_PATTERNS = re.compile(
    r"\b(rau|cải|muống|ngót|dền|mồng tơi|xà lách|dưa leo|cà chua|bí|bầu|mướp|súp lơ|bông cải|nấm|đậu cô ve|đậu hà lan|cà|cần|củ|măng|giá đậu|su hào|vegetable|salad|spinach|broccoli|cucumber)\b",
    re.IGNORECASE,
)

SNACK_PATTERNS = re.compile(
    r"\b(quả|trái|chuối|táo|cam|bưởi|xoài|dưa|dưa hấu|nho|ổi|sữa chua|sữa tươi|sữa dê|sữa đậu|sữa bò|sữa|dứa|hồng|chanh|dâu|dâu tây|đu đủ|lê|lựu|mãng cầu|mít|mơ|na|nhãn|quít|quýt|sầu riêng|vải|bơ|khế|thanh long|chôm chôm|măng cụt|kiwi|mận|hồng xiêm|vú sữa|hạt dẻ|hạt điều|hạt sen|hạt bí|hạt dưa|hạt hướng dương|hạt macca|hạt óc chó|hạt hạnh nhân|fruit|yogurt|apple|banana|orange|milk|almond|walnut|peanut|nut|nuts)\b",
    re.IGNORECASE,
)


def classify_dish_role(food_name: str, category: str = "", source: str = "vietnamese") -> DishRole:
    """Classify a food item into its primary culinary DishRole."""
    name_clean = str(food_name or "").strip().lower()
    cat_clean = "" if category is None or str(category).lower() == "nan" else str(category).strip().lower()

    # Industrial products (oils, fats, flours) are always raw ingredients, even if containing cooked words (e.g. "Dầu rang")
    if RAW_PRODUCT_PREFIX.search(name_clean):
        return DishRole.RAW_INGREDIENT

    is_cooked = bool(COOKED_STATE_PATTERNS.search(name_clean))
    if not is_cooked and is_raw_or_industrial_junk(name_clean, cat_clean):
        return DishRole.RAW_INGREDIENT

    # Snack overrides bread/cereal in cookie and waffle product names.
    if re.search(r"\b(cookie|cookies|waffle|waffles|biscuit|biscuits|bánh quy|bánh xốp)\b", name_clean):
        return DishRole.FRUIT_SNACK

    # Sữa và các chế phẩm từ sữa là snack/beverage (tránh nhầm "bò" trong sữa bò thành protein mặn)
    if DAIRY_PATTERNS.search(name_clean):
        return DishRole.FRUIT_SNACK

    # 1. Soup / Canh
    if SOUP_PATTERNS.search(name_clean) or "soup" in cat_clean:
        return DishRole.SOUP

    # 2. Main Protein / Món mặn
    if PROTEIN_PATTERNS.search(name_clean) or any(
        k in cat_clean for k in ["beef", "poultry", "pork", "seafood", "fish", "thủy sản", "hải sản", "thịt", "gia cầm"]
    ):
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

    # Món có trạng thái nấu chín nhưng chưa khớp nhóm nào ở trên
    if is_cooked and not is_raw_or_industrial_junk(name_clean, cat_clean):
        if re.search(r"\b(xào|luộc|nộm|gỏi)\b", name_clean):
            return DishRole.VEGETABLE
        return DishRole.MAIN_PROTEIN

    # Unknown records are unsafe for a user-facing structured menu.
    # Keep them in the source database, but do not guess a culinary role.
    return DishRole.RAW_INGREDIENT


def get_role_portion_bounds(role: DishRole) -> Tuple[float, float]:
    """Retrieve natural minimum and maximum portion bounds in grams for a given role."""
    return ROLE_PORTION_BOUNDS.get(role, (50.0, 250.0))


def portion_bounds_for_food_ids(
    food_ids: Iterable[str], food_map: dict
) -> tuple[list[float], list[float]]:
    """Vector khẩu phần (lb, ub) theo vai trò ẩm thực cho từng food_id.

    Dùng chung cho inner solver và cho bước làm tròn 5g, để mọi điểm vào
    (generate, swap) tuân thủ cùng một bộ ngưỡng theo vai trò món thay vì
    khoảng vô hướng cứng [25, 350].

    Raises:
        ValueError: nếu vai trò không có khoảng khẩu phần hợp lệ (vd RAW_INGREDIENT).
    """
    lows: list[float] = []
    highs: list[float] = []
    for food_id in food_ids:
        row = food_map[food_id]
        role = classify_dish_role(
            str(row.get("food_name", "")),
            str(row.get("category", "")),
            str(row.get("source", "")),
        )
        low, high = get_role_portion_bounds(role)
        if low >= high:
            raise ValueError(
                f"Món '{food_id}' (vai trò {role.value}) không có khoảng khẩu phần hợp lệ "
                f"[{low}, {high}]"
            )
        lows.append(float(low))
        highs.append(float(high))
    return lows, highs
