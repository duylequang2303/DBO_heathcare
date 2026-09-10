# `src/utils/data_loader.py`

## Mục đích

Nạp và chuẩn bị cơ sở dữ liệu thực phẩm từ file CSV đã tiền xử lý.

## Các hàm chính

### `load_food_db(path=DATA_PATH) -> pd.DataFrame`

Đọc `merged_food_nutrition.csv` từ `data/processed/`.

Xử lý:
- `food_name` NaN → `""`
- Tất cả nutrient keys NaN → `0.0`, cast sang `float`

Trả về DataFrame với các cột:
`food_id`, `food_name`, `category`, `meal_type`, `serving_size_g`, `calories`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g`, `sodium_mg`, `calcium_mg`, `iron_mg`, `vitamin_c_mg`, `source`, `name_en`

### `build_food_map(df) -> dict[str, dict]`

Chuyển DataFrame thành dict tra cứu nhanh:
```python
{
    "VN_10009": {"food_name": "...", "calories": ..., ...},
    "USDA_2057257": {...},
}
```

Khóa: `food_id`. Dùng trong `Menu.decode()` và demo scripts.

## Hằng số

```python
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "merged_food_nutrition.csv"
NUTRIENT_KEYS = ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g",
                 "sodium_mg", "calcium_mg", "iron_mg", "vitamin_c_mg"]
```

## Ghi chú

- Không sửa `scripts/preprocess_data.py` để đảm bảo dữ liệu tái lập được.
- Tất cả giá trị dinh dưỡng đều tính trên **100g** khẩu phần.

## Kiểm thử (`tests/test_model.py` + `tests/test_menu.py`)

- Nạp `merged_food_nutrition.csv` đúng shape: `15929` dòng, có đủ cột bắt buộc (`food_id`, `food_name`, `meal_type`, `calories`)
- `build_food_map()` dùng `food_id` làm key, tra cứu `O(1)`
- Missing nutrient values → `0.0` (float)
- `food_name` NaN → `""`
