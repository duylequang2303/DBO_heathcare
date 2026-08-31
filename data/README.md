# Hướng dẫn & Quy chuẩn Cấu trúc Dữ liệu Dinh dưỡng (Tuần 2)

Theo đề cương khóa luận:
- **Nội dung Tuần 2:** Nghiên cứu nhu cầu năng lượng, các thành phần dinh dưỡng và lựa chọn nguồn dữ liệu thực phẩm phù hợp.
- **Yêu cầu dữ liệu:** Xây dựng cơ sở dữ liệu thực phẩm gồm năng lượng (calories), protein, carbohydrate, chất béo (fat), chất xơ (fiber) và một số vi chất cần thiết (sodium, calcium, iron, vitamin...).

---

## 1. Cấu trúc thư mục `data/`

```text
data/
├── raw/                      # Chứa các file CSV dữ liệu thô thu thập ban đầu
│   └── foods_nutrition_sample.csv  # File CSV mẫu với các trường chuẩn
├── processed/                # Dữ liệu CSV sau khi đã làm sạch, chuẩn hóa đơn vị
└── README.md                 # Tài liệu mô tả cấu trúc trường dữ liệu
```

---

## 2. Quy chuẩn các cột trong file CSV thực phẩm (`merged_food_nutrition.csv`)

### 2.1 Các cột chuẩn

| Tên cột | Kiểu dữ liệu | Đơn vị | Mô tả |
| :--- | :--- | :--- | :--- |
| `food_id` | String | - | Mã định danh (tiền tố `USDA_` / `VN_`) |
| `food_name` | String | - | Tên món ăn / thực phẩm (món VN dùng tiếng Việt) |
| `category` | String | - | Phân loại (theo nguồn: USDA Food Category / nhóm thực phẩm VN) |
| `meal_type` | String | - | Bữa phù hợp: `breakfast`, `snack`, `all` (tự gán theo nhóm món) |
| `serving_size_g` | Float | gram (g) | Khẩu phần chuẩn (mặc định `100` = tính trên 100g) |
| `calories` | Float | kcal | Năng lượng |
| `protein_g` | Float | g | Chất đạm (Protein) |
| `carbs_g` | Float | g | Carbohydrate (Tinh bột/Đường) |
| `fat_g` | Float | g | Tổng chất béo (Fat) |
| `fiber_g` | Float | g | Chất xơ (Fiber) |
| `sodium_mg` | Float | mg | Natri (Sodium) |
| `calcium_mg` | Float | mg | Canxi (Calcium) |
| `iron_mg` | Float | mg | Sắt (Iron) |
| `vitamin_c_mg` | Float | mg | Vitamin C |

### 2.2 Các cột bổ sung

| Tên cột | Kiểu dữ liệu | Đơn vị | Mô tả |
| :--- | :--- | :--- | :--- |
| `source` | String | - | Nguồn dữ liệu: `usda` hoặc `vietnamese` |
| `name_en` | String | - | Tên tiếng Anh gốc (USDA) / tên tham khảo (VN) |

### 2.3 Ghi chú xử lý dữ liệu

- Toàn bộ giá trị dinh dưỡng tính trên **100g** khẩu phần (`serving_size_g = 100`).
- Phần USDA: đã quy đổi năng lượng bị lưu nhầm đơn vị kJ sang kcal (÷4.184), lọc bỏ nhóm không phù hợp bữa ăn (kẹo, nước ngọt, snack, dầu, gia vị...), loại dòng nước ép & năng lượng bằng 0.
- Deduplicate theo `food_name`, giữ dòng có đầy đủ dữ liệu nhất.
- `vitamin_a_mcg`, `price_vnd`, `allergy_warnings` đã bỏ vì nguồn dữ liệu thô không có; nhóm sẽ bổ sung sau nếu cần.
- Script tái lập: `scripts/preprocess_data.py`.
