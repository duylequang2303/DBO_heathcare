# `src/models/menu.py`

## Mục đích

Biểu diễn thực đơn (Menu) gồm 4 bữa ăn, cung cấp API để:
- Tính tổng dinh dưỡng (`total`)
- Mã hóa thực đơn thành vector khẩu phần (`encode`)
- Giải mã vector về thực đơn (`decode`)

## Các thành phần chính

### `MealType` (Enum)

4 bữa ăn: `BREAKFAST`, `LUNCH`, `DINNER`, `SNACK`.

### `MenuItem` (dataclass)

Đại diện cho 1 món ăn trong thực đơn.

| Trường | Kiểu | Mô tả |
| :--- | :--- | :--- |
| `food_id` | `str` | ID món ăn (khóa trong `food_map`) |
| `food_name` | `str` | Tên món ăn |
| `portion_g` | `float` | Khẩu phần (gram) |
| `calories` | `float` | Năng lượng / 100g |
| `protein_g` | `float` | Protein / 100g |
| `carbs_g` | `float` | Carb / 100g |
| `fat_g` | `float` | Fat / 100g |
| `fiber_g` | `float` | Chất xơ / 100g |
| `sodium_mg` | `float` | Sodium / 100g |
| `calcium_mg` | `float` | Calcium / 100g |
| `iron_mg` | `float` | Iron / 100g |
| `vitamin_c_mg` | `float` | Vitamin C / 100g |
| `meal_type` | `str` | Nhãn bữa ăn (`breakfast`/`snack`/`all`) |

**Phương thức:**
- `nutrient(key) -> float`: Tính giá trị dinh dưỡng thực tế = `per_100g * portion_g / 100`.

### `Meal`

Đại diện cho 1 bữa ăn, chứa list `MenuItem`.

- `total(key) -> float`: Tổng dinh dưỡng của bữa.
- `add_item(item)`: Thêm món vào bữa.

### `Menu`

Đại diện cho thực đơn 1 ngày (4 bữa).

| Phương thức | Kiểu trả về | Mô tả |
| :--- | :--- | :--- |
| `total(key)` | `float` | Tổng dinh dưỡng cả ngày |
| `all_items()` | `list[MenuItem]` | Tất cả món ăn (bất kể bữa) |
| `encode()` | `list[float]` | Vector khẩu phần gram (thứ tự `all_items()`) |
| `food_ids()` | `list[str]` | Vector `food_id` (thứ tự `all_items()`) |
| `meal_counts()` | `dict[str, int]` | Số món mỗi bữa |
| `decode(food_ids, portions_g, food_map, meal_counts)` | `Menu` | Giải mã vector về Menu |

### `Menu.decode()` (classmethod)

- **Bắt buộc** truyền `meal_counts` (dict có 4 key: `breakfast`, `lunch`, `dinner`, `snack`).
- Thứ tự bữa cố định: `breakfast → lunch → dinner → snack`.
- Kiểm tra:
  - `len(food_ids) == len(portions_g)`
  - `sum(meal_counts) == len(food_ids)`
  - `meal_counts` >= 0, kiểu int

### Hàm nội bộ

- `_item_from_row(food_id, portion_g, row) -> MenuItem`: Tạo `MenuItem` từ dòng CSV trong `food_map`.
- `_meal_type_str(value) -> str`: Chuẩn hóa `meal_type` về lowercase, loại bỏ `None`/`nan`/`none`.
- `_num(value) -> float`: Chuyển giá trị dinh dưỡng sang float, `None`/NaN → `0.0`.

## Kiểm thử (`tests/test_menu.py`)

11 bài test:
- Nạp CSV đúng shape (`15929` dòng), có đủ cột bắt buộc
- `build_food_map()` dùng `food_id` làm key
- `encode()`/`decode()` round-trip giữ nguyên `food_id` và `portion_g`
- `decode()` xếp đúng số món mỗi bữa theo `meal_counts`
- `decode()` báo lỗi nếu thiếu `meal_counts`, độ dài vector sai, `meal_counts` âm
- `MenuItem.nutrient("calories")` đúng công thức `calories * portion_g / 100`
- `meal_type` sau decode khớp CSV (`breakfast`/`snack`/`all`)
- Missing nutrient values → `0.0`
