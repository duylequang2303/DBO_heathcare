# `src/models/constraints.py`

## Mục đích

Kiểm tra thực đơn có thỏa tất cả ràng buộc dinh dưỡng và thực tế không.

## Hàm chính

### `validate_menu(menu, profile, targets) -> list[str]`

Chạy toàn bộ kiểm tra ràng buộc, trả về **list các lỗi** (rỗng = hợp lệ).

### `is_feasible(menu, profile, targets) -> bool`

Trả về `True` nếu không có lỗi vi phạm nào.

## Các ràng buộc được kiểm tra

| Ràng buộc | Hàm kiểm tra | Mô tả |
| :--- | :--- | :--- |
| Năng lượng | `_check_energy` | Tổng calo trong `±10%` mục tiêu |
| Macro | `_check_macros` | protein/carb ±15%, fat ±20%, fiber ±30% |
| Số món | `_check_meal_count` | Đúng `profile.meal_counts` từng bữa |
| Khẩu phần | `_check_portion` | Mỗi món `25g ≤ portion ≤ 350g` |
| Sở thích | `_check_dislikes` | Tên món không chứa token trong `dislikes` |
| Dị ứng | `_check_allergies` | Tên món không chứa token trong `allergies` |
| Không lặp | `_check_duplicates` | Không trùng `food_id` hoặc `food_name` |
| meal_type | `_check_meal_type` | `breakfast`/`snack` đúng bữa; `lunch`/`dinner` chỉ nhận `all` |

## Hằng số cấu hình

```python
PORTION_RANGE = {"min": 25.0, "max": 350.0}
ENERGY_TOLERANCE = 0.10       # ±10%
MACRO_TOLERANCE = {
    "protein_g": 0.15,        # ±15%
    "carbs_g": 0.15,          # ±15%
    "fat_g": 0.20,            # ±20%
    "fiber_g": 0.30,          # ±30%
}
MEAL_TYPE_ALLOWED = {
    MealType.BREAKFAST: {"breakfast"},
    MealType.SNACK: {"snack"},
    MealType.LUNCH: {"all"},
    MealType.DINNER: {"all"},
}
```

## Ghi chú

- Kiểm tra **case-insensitive** cho sở thích/dị ứng.
- `meal_type` thiếu (`None`/`""`) được bỏ qua.

## Kiểm thử (`tests/test_constraints.py`)

5 bài test:
- Menu hợp lệ → `is_feasible()` trả `True`
- Menu hợp lệ không có trùng `food_id`/`food_name`
- Portion trong khoảng `[25, 350]` inclusive
- Trùng `food_name` cùng ngày → vi phạm
- `lunch` không nhận món `breakfast` (`meal_type` mismatch)
