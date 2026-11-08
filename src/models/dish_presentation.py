"""Rule-based dish presentation for the food-based menu prototype.

This module only changes *how* a food row is presented. It never changes the
food_id, portion, nutrient values, objective function, or solver result.

The data source is a nutrient table per 100 g of the original ingredient, not a
quantitative recipe database. Therefore the display name must state the
ingredient basis explicitly (for example, "Cơm gạo lứt" is made from dry rice,
not from cooked rice). The demo does not model cooking yield or water loss.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.models.dish_category import COOKED_STATE_PATTERNS, DishRole, classify_dish_role


PRESENTATION_DISCLAIMER = (
    "Tên món là lớp ghép món demo theo quy tắc, không phải công thức định lượng; "
    "khẩu phần và dinh dưỡng vẫn tính trên nguyên liệu gốc, chưa quy đổi "
    "hao hụt/nước khi nấu."
)


@dataclass(frozen=True)
class DishPresentation:
    """Display-only description of a food item."""

    display_name: str
    preparation: str
    ingredient_basis: str
    is_estimated: bool = True


def _has_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def present_dish(
    food_name: str,
    category: str = "",
    source: str = "vietnamese",
    role: DishRole | None = None,
) -> DishPresentation:
    """Return a dish-like display name for a food row.

    The mapping is deliberately conservative and rule-based. It is a
    presentation layer for the demo, not a recipe database.

    Raises:
        ValueError: if the name is empty.
    """
    name = str(food_name or "").strip()
    if not name:
        raise ValueError("Không thể ghép tên món cho thực phẩm không có tên.")

    actual_role = role or classify_dish_role(name, category, source)
    lower = name.lower()

    if actual_role == DishRole.RAW_INGREDIENT:
        # Pools must already exclude RAW_INGREDIENT. If an unknown/fake row is
        # decoded directly (for example in a unit test), keep the original name
        # instead of inventing a dish or crashing the solver.
        return DishPresentation(name, "chưa xác định", "chưa phân loại")

    if actual_role in {DishRole.STAPLE, DishRole.MAIN_PROTEIN} and COOKED_STATE_PATTERNS.search(lower):
        return DishPresentation(name, "món chín", "món chín")

    if actual_role == DishRole.STAPLE:
        if lower.startswith("gạo"):
            rice_name = name[0].lower() + name[1:]
            return DishPresentation(f"Cơm {rice_name}", "nấu cơm", "gạo khô")
        if lower.startswith("bánh phở") or lower in {"bún", "mì", "miến"}:
            return DishPresentation(f"{name} luộc", "luộc", "nguyên liệu khô")
        # Already a prepared dish: keep the name, do not invent a second preparation.
        if _has_any(
            lower,
            ("cơm", "cháo", "xôi", "phở", "bún", "miến", "mì"),
        ):
            return DishPresentation(name, "món chín", "nguyên liệu khô")
        if "bánh mì" in lower:
            return DishPresentation(name, "ăn kèm", "bánh mì")
        if _has_any(lower, ("khoai", "ngô", "bắp")):
            return DishPresentation(f"{name} luộc", "luộc", "củ/quả tươi")
        if lower.startswith("kê") or "yến mạch" in lower:
            return DishPresentation(f"Cơm {name.lower()}", "nấu chín", "nguyên liệu khô")
        if _has_any(lower, ("đậu xanh", "đậu tương", "đậu nành", "đậu đen", "đậu hà lan")):
            return DishPresentation(f"{name} hấp", "hấp", "nguyên liệu khô")
        return DishPresentation(f"{name} (món bột)", "chế biến", "nguyên liệu khô")

    if actual_role == DishRole.MAIN_PROTEIN:
        if "trứng" in lower:
            return DishPresentation(f"{name} luộc", "luộc", "nguyên liệu tươi")
        if "đậu phụ" in lower:
            return DishPresentation("Đậu phụ sốt cà", "sốt", "nguyên liệu tươi")
        if _has_any(lower, ("tôm", "cua", "ghẹ", "mực", "tép", "nghêu", "sò", "ốc")):
            return DishPresentation(f"{name} hấp", "hấp", "nguyên liệu tươi")
        if _has_any(lower, ("cá", "fish", "salmon", "tuna")):
            return DishPresentation(f"{name} áp chảo", "áp chảo", "nguyên liệu tươi")
        if _has_any(lower, ("sườn", "lưỡi", "dạ dày", "mề", "đuôi")):
            return DishPresentation(f"{name} hầm", "hầm", "nguyên liệu tươi")
        if _has_any(lower, ("thịt", "bò", "heo", "lợn", "gà", "vịt", "chả", "giò")):
            return DishPresentation(f"{name} xào", "xào", "nguyên liệu tươi")
        return DishPresentation(f"{name} chế biến", "chế biến", "nguyên liệu tươi")

    if actual_role == DishRole.VEGETABLE:
        if _has_any(lower, ("xào", "luộc", "nộm", "salad")):
            return DishPresentation(name, "rau chín", "nguyên liệu tươi")
        return DishPresentation(f"{name} luộc", "luộc", "nguyên liệu tươi")

    if actual_role == DishRole.SOUP:
        if _has_any(lower, ("canh", "súp", "soup")):
            return DishPresentation(name, "nấu", "nguyên liệu tươi")
        return DishPresentation(f"Canh {name}", "nấu", "nguyên liệu tươi")

    if actual_role == DishRole.FRUIT_SNACK:
        return DishPresentation(f"{name} (ăn tươi)", "ăn tươi", "quả/sữa")

    if actual_role == DishRole.BEVERAGE:
        return DishPresentation(name, "uống", "đồ uống")

    return DishPresentation(name, "chế biến", "nguyên liệu")
