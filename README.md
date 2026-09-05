# DBO_heathcare - Hệ thống đề xuất thực đơn dinh dưỡng cá nhân hóa dựa trên IDBO

Khóa luận cử nhân ngành CNTT (2025 - 2026).
Trường Đại học Công Thương TP.HCM - Khoa Công nghệ Thông tin.

## Mục tiêu đề tài

1. Nghiên cứu và xây dựng mô hình bài toán tối ưu thực đơn dinh dưỡng cá nhân hóa.
2. Xây dựng Dung Beetle Optimizer cải tiến với cơ chế ngẫu nhiên (IDBO).
3. Phát triển hệ thống web hỗ trợ tự động xây dựng và đề xuất thực đơn.
4. Đánh giá, so sánh IDBO với DBO gốc và các phương pháp cơ sở.

## Mô hình bài toán (Tuần 3)

Mỗi nghiệm IDBO biểu diễn một thực đơn 1 ngày: tập món + khẩu phần (gram) cho 4 bữa `breakfast`, `lunch`, `dinner`, `snack`.

### 1. Hồ sơ và nhu cầu

- `UserProfile`: tuổi, giới tính, chiều cao, cân nặng, mức vận động, mục tiêu, dị ứng, sở thích, số món mỗi bữa.
- BMR Mifflin-St Jeor, TDEE = BMR * hệ số vận động, calo mục tiêu theo goal.
- Macro mục tiêu (protein / carb / fat / fiber) tính từ calo và DRI.

### 2. Biểu diễn thực đơn

- `MenuItem`: food_id, tên, portion_g, chất dinh dưỡng / 100g, meal_type.
- `Meal` / `Menu`: 4 bữa; `total(key)` quy đổi theo `portion_g / 100`.
- Dữ liệu: `data/processed/merged_food_nutrition.csv` (15.929 món, USDA + VN).

### 3. Ràng buộc (`src/models/constraints.py`)

| Ràng buộc | Mô tả |
| :--- | :--- |
| Năng lượng | Tổng calo trong +-10% mục tiêu |
| Macro | protein/carb +-15%, fat +-20%, fiber +-30% |
| Số món | Đúng `profile.meal_counts` từng bữa |
| Khẩu phần | 25g - 350g / món |
| Sở thích / dị ứng | Tên món không chứa token dislike / allergy |
| Không lặp món | Không trùng `food_id` hoặc tên trong ngày |
| meal_type | breakfast/snack chỉ vào đúng bữa; lunch/dinner lấy món `all` |

### 4. Hàm mục tiêu (`src/models/objective.py`)

Fitness nằm trong [-100, 100]:

```text
fitness = 0.35*energy + 0.30*macros + 0.20*preference + 0.15*diversity
          - min(90, 12 * so_vi_pham)
```

Mỗi thành phần con nằm trong [0, 100]. Menu hợp lệ có fitness cao hơn menu ngẫu nhiên.

### 5. Format nghiệm IDBO (chốt trước Tuần 4)

Vector liên tục `x` chỉ chứa khẩu phần (gram), độ dài `n = sum(meal_counts)`:

```text
x = [p_breakfast_1, ..., p_breakfast_k,
     p_lunch_1, ...,
     p_dinner_1, ...,
     p_snack_1, ...]
```

Kèm vector rời rạc `food_ids` cùng độ dài, cùng thứ tự bữa. Giải mã:

```text
Menu.decode(food_ids, portions_g, food_map, meal_counts)
```

`Menu.encode()` trả về đúng `x`. Round-trip `encode -> decode` giữ nguyên thực đơn. Biên: `25 <= x_i <= 350`.

## Cấu trúc mã nguồn

```text
DBO_heathcare/
├── data/processed/merged_food_nutrition.csv
├── src/models/
│   ├── user_profile.py
│   ├── menu.py
│   ├── constraints.py
│   └── objective.py
├── src/utils/
│   ├── data_loader.py
│   └── nutrition.py
├── scripts/demo_week3.py
├── tests/
└── docs/TASK_WEEK3.md
```

## Cài đặt và chạy

```bash
# Cài thư viện
pip install -r requirements.txt

# Test
python -m pytest tests/

# Demo: hồ sơ -> nhu cầu -> thực đơn mẫu -> đánh giá
python scripts/demo_week3.py
```
