"""Báo cáo thực đơn bằng tiếng Việt dễ hiểu.

Dịch tên thức phẩm kỹ thuật (tiếng Anh USDA, mã food_id) sang tên tiếng Việt
để người dùng không chuyên môn có thể đọc và hiểu rõ món ăn là gì, ăn như thế
nào, khẩu phần bao nhiêu.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from src.models.dish_category import classify_dish_role, get_role_portion_bounds
from src.models.menu import Menu


# Ánh xạ từ tên thức phẩm tiếng Anh (USDA) sang tên tiếng Việt dễ hiểu.
# Dùng cho các thực phẩm USDA không có tên tiếng Việt sẵn có.
USDA_TO_VI: dict[str, str] = {
    r"\bbacon\b": "Xông xô",
    r"\bsalmon\b": "Cá hồi",
    r"\btuna\b": "Cá ngừ",
    r"\bchicken\b": "Thịt gà",
    r"\bturkey\b": "Thịt gà tây",
    r"\bbeef\b": "Thịt bò",
    r"\bpork\b": "Thịt lợn",
    r"\blamb\b": "Thịt cừu",
    r"\bduck\b": "Thịt vịt",
    r"\bbread\b": "Bánh mì",
    r"\bric(e|es)\b": "Cơm",
    r"\bpasta\b": "Mì Ý / pasta",
    r"\bnoodl(e|es)\b": "Mì",
    r"\bcereal\b": "Đậu bình sinh / ngũ cốc",
    r"\boatmeal\b": "Cháo yến mạch",
    r"\begg(s)?\b": "Trứng",
    r"\bcheese\b": "Phô mai",
    r"\byogurt\b": "Sữa chua",
    r"\bmilk\b": "Sữa",
    r"\bbutter\b": "Bơ",
    r"\boil\b": "Dầu ăn",
    r"\bsugar\b": "Đường",
    r"\bhoney\b": "Mật ong",
    r"\bfruit\b": "Trái cây",
    r"\bapple\b": "Táo",
    r"\bbanana\b": "Chuối",
    r"\borange\b": "Cam",
    r"\bgrape(s)?\b": "Nho",
    r"\bberry(ies)?\b": "Dâu tây / berry",
    r"\bpotato(es)?\b": "Khoai tây",
    r"\btomato(es)?\b": "Cà chua",
    r"\bonion(s)?\b": "Hành tây",
    r"\bgarlic\b": "Tỏi",
    r"\bcarrot(s)?\b": "Cà rốt",
    r"\bbroccoli\b": "Bông cải xanh",
    r"\bspinach\b": "Rau cải xoăn",
    r"\bcabbage\b": "Cải bắp",
    r"\blettuce\b": "Salad",
    r"\bcucumber\b": "Dưa chuột",
    r"\bpea(s)?\b": "Đậu",
    r"\bbean(s)?\b": "Đậu",
    r"\bcorn\b": "Ngô",
    r"\bnut(s)?\b": "Hạt",
    r"\balmond(s)?\b": "Hạt điều",
    r"\bpeanut(s)?\b": "Đậu phong",
    r"\bseafood\b": "Hải sản",
    r"\bshrimp\b": "Tôm",
    r"\bcrab\b": "Cua",
    r"\bfish\b": "Cá",
    r"\bsoup\b": "Canh / súp",
    r"\bsalad\b": "Salad",
    r"\bsandwich\b": "Bánh kẹp",
    r"\bpizza\b": "Pizza",
    r"\bburger\b": "Burger",
    r"\bfried\b": "Chiên",
    r"\broast(ed)?\b": "Nướng",
    r"\bgrilled\b": "Nướng",
    r"\bsteamed\b": "Hấp",
    r"\bbaked\b": "Nướng",
    r"\braw\b": "Sơ chế / chưa chế biến",
    r"\bcooked\b": "Đã nấu chín",
    r"\bprepared\b": "Đã chế biến sẵn",
}


def _translate_usda_name(food_name: str) -> str:
    """Dịch tên thức phẩm tiếng Anh sang tiếng Việt dễ hiểu.

    Nếu không khớp từ khóa nào, trả về tên gốc gọn gàng (loại bỏ ký hiệu lạ).
    """
    name = str(food_name or "").strip()
    name = name.strip('"').strip()
    name_l = name.lower()

    for pattern, vi in USDA_TO_VI.items():
        if re.search(pattern, name_l, re.IGNORECASE):
            return vi

    # Fallback: lấy từ đầu tiên có ý nghĩa, loại bỏ ký hiệu
    cleaned = re.sub(r'[",()\[\]{}]', " ", name)
    tokens = [t for t in cleaned.split() if len(t) > 2 and t.isalpha()]
    if tokens:
        return tokens[0].capitalize()
    return "Thức phẩm"


def get_vietnamese_food_name(row: dict) -> str:
    """Lấy tên tiếng Việt dễ hiểu cho một dòng thức phẩm trong food_map.

    - Nếu source == 'vietnamese': dùng food_name có sẵn (đã tiếng Việt).
    - Nếu source == 'usda': dịch sang tiếng Việt qua từ khóa.
    """
    source = str(row.get("source", "")).strip().lower()
    food_name = str(row.get("food_name", "")).strip()

    if source == "vietnamese" and food_name:
        return food_name

    return _translate_usda_name(food_name)


def get_food_description(row: dict, role: str) -> str:
    """Sinh mô tả ngắn gọn cách ăn/chế biến món ăn bằng tiếng Việt."""
    role_vi = {
        "staple": "món chính (cơm, mì, bánh mì, khoai)",
        "main_protein": "món protein chính (thịt, cá, trứng, đậu phụ)",
        "vegetable": "món rau / canh rau",
        "soup": "món canh / súp",
        "fruit_snack": "trái cây / bữa phụ",
        "beverage": "đồ uống",
        "raw_ingredient": "nguyên liệu thô (không nên ăn đơn lẻ)",
    }.get(role, "món ăn")

    source = str(row.get("source", "")).strip().lower()
    if source == "vietnamese":
        return f"{role_vi} (nguồn Việt Nam)"

    return f"{role_vi} (dịch từ dữ liệu quốc tế)"


@dataclass
class MenuItemReport:
    """Thông tin báo cáo cho một món ăn trong thực đơn."""
    stt: int
    meal_name: str
    food_name_vi: str
    food_name_raw: str
    food_id: str
    portion_g: float
    role: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float
    description: str


@dataclass
class MenuReport:
    """Báo cáo toàn bộ thực đơn."""
    profile_name: str
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    total_sodium_mg: float
    target_calories: float
    violations: list[str]
    items: list[MenuItemReport]


def build_menu_report(
    menu: Menu,
    food_map: dict,
    profile_name: str = "Người dùng",
    targets: Optional[dict] = None,
    violations: Optional[list[str]] = None,
) -> MenuReport:
    """Xây dựng báo cáo thực đơn tiếng Việt từ Menu và food_map."""
    targets = targets or {}
    violations = violations or []

    items: list[MenuItemReport] = []
    stt = 0
    meal_names = {
        "breakfast": "Bữa sáng",
        "lunch": "Bữa trưa",
        "dinner": "Bữa tối",
        "snack": "Bữa phụ",
    }

    for meal_type_enum, meal in menu.meals.items():
        meal_name = meal_names.get(meal_type_enum.value, meal_type_enum.value)
        for item in meal.items:
            stt += 1
            row = food_map.get(item.food_id, {})
            role = classify_dish_role(
                str(item.food_name), str(row.get("category", "")), str(row.get("source", ""))
            )
            food_name_vi = get_vietnamese_food_name(row)
            description = get_food_description(row, role.value)

            items.append(
                MenuItemReport(
                    stt=stt,
                    meal_name=meal_name,
                    food_name_vi=food_name_vi,
                    food_name_raw=str(item.food_name),
                    food_id=item.food_id,
                    portion_g=float(item.portion_g),
                    role=role.value,
                    calories=float(item.nutrient("calories")),
                    protein_g=float(item.nutrient("protein_g")),
                    carbs_g=float(item.nutrient("carbs_g")),
                    fat_g=float(item.nutrient("fat_g")),
                    fiber_g=float(item.nutrient("fiber_g")),
                    sodium_mg=float(item.nutrient("sodium_mg")),
                    description=description,
                )
            )

    return MenuReport(
        profile_name=profile_name,
        total_calories=float(menu.total("calories")),
        total_protein_g=float(menu.total("protein_g")),
        total_carbs_g=float(menu.total("carbs_g")),
        total_fat_g=float(menu.total("fat_g")),
        total_fiber_g=float(menu.total("fiber_g")),
        total_sodium_mg=float(menu.total("sodium_mg")),
        target_calories=float(targets.get("calories", 0)),
        violations=violations,
        items=items,
    )


def format_menu_report(report: MenuReport) -> str:
    """Định dạng báo cáo thực đơn thành chuỗi văn bản tiếng Việt dễ đọc."""
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("BÁO CÁO THỰC ĐƠN ĐỀ XUẤT")
    lines.append("=" * 60)
    lines.append(f"Người dùng: {report.profile_name}")
    lines.append("")

    lines.append("THỰC ĐƠN THEO BỮA:")
    for item in report.items:
        lines.append("")
        lines.append(f"  {item.stt}. [{item.meal_name}] {item.food_name_vi}")
        lines.append(f"      Loại món: {item.description}")
        lines.append(f"      Khẩu phần: {item.portion_g:.0f} g")
        lines.append(f"      Dinh dưỡng: {item.calories:.0f} kcal | "
                     f"Protein {item.protein_g:.1f}g | "
                     f"Carbs {item.carbs_g:.1f}g | "
                     f"Béo {item.fat_g:.1f}g | "
                     f"Xơ {item.fiber_g:.1f}g | "
                     f"Natri {item.sodium_mg:.0f}mg")

    lines.append("")
    lines.append("-" * 60)
    lines.append("TỔNG KẾT NGÀY:")
    lines.append(f"  Năng lượng:   {report.total_calories:.0f} kcal "
                 f"(mục tiêu: {report.target_calories:.0f} kcal)")
    lines.append(f"  Protein:      {report.total_protein_g:.1f} g")
    lines.append(f"  Carbohydrate: {report.total_carbs_g:.1f} g")
    lines.append(f"  Chất béo:     {report.total_fat_g:.1f} g")
    lines.append(f"  Chất xơ:      {report.total_fiber_g:.1f} g")
    lines.append(f"  Natri:        {report.total_sodium_mg:.0f} mg")
    lines.append("-" * 60)

    if report.violations:
        lines.append("")
        lines.append("CẢNH BÁO VẪN ĐỀ:")
        for v in report.violations:
            lines.append(f"  - {v}")
    else:
        lines.append("")
        lines.append("KẾT LUẬN: Thực đơn đáp ứng các ràng buộc dinh dưỡng đã cấu hình.")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
