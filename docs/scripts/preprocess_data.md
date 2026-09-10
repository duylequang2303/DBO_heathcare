# `scripts/preprocess_data.py`

## Mục đích

Pipeline tiền xử lý dữ liệu thực phẩm thô (USDA + Việt Nam) → `merged_food_nutrition.csv`.

## Luồng xử lý

1. Đọc `data/raw/comprehensive_foods_usda.csv` và `data/raw/vietnamese_food_composition.csv`
2. Làm sạch từng nguồn:
   - **USDA**: chuyển kJ→kcal nếu calories > 900, lọc calories ≤ 1000, loại bỏ danh mục không phù hợp, loại bỏ juice/nectar, gán `meal_type`
   - **VN**: gán `meal_type` theo nhóm VN đã định nghĩa
3. Gộp 2 nguồn, dedup theo `food_name` giữ dòng đầy đủ nhất
4. Ghi ra `data/processed/merged_food_nutrition.csv`

## Cấu hình chính

### `DROP_CATEGORIES`

Set các danh mục cần loại bỏ (đồ ngọt, nước ngọt, rượu bia, snack, v.v.).

### `BREAKFAST_KEYWORDS` / `SNACK_KEYWORDS`

Từ khóa để gán `meal_type` tự động cho USDA.

### `VN_MEAL_TYPE`

Map nhóm VN → `meal_type`.

## Các hàm chính

| Hàm | Mô tả |
| :--- | :--- |
| `assign_meal_type(category) -> str` | Gán `breakfast`/`snack`/`all` theo danh mục USDA |
| `assign_vn_meal_type(group_name) -> str` | Gán `meal_type` theo nhóm VN |
| `clean_usda(usda) -> pd.DataFrame` | Làm sạch dữ liệu USDA |
| `clean_vn(vn) -> pd.DataFrame` | Làm sạch dữ liệu VN |
| `dedup_best(df, keys) -> pd.DataFrame` | Loại bỏ trùng `food_name`, giữ dòng có nhiều dữ liệu nhất |

## Chạy

```bash
python scripts/preprocess_data.py
```

## Ghi chú

- Không sửa file này khi chưa bàn trong nhóm (đảm bảo dữ liệu tái lập).
- Tất cả nutrient đều trên 100g.
