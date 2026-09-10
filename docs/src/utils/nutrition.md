# `src/utils/nutrition.py`

## Mục đích

Tính toán nhu cầu dinh dưỡng hàng ngày từ hồ sơ người dùng:
- BMR (Basal Metabolic Rate)
- TDEE (Total Daily Energy Expenditure)
- Calo mục tiêu theo goal
- Macro targets (protein, carbs, fat, fiber)
- Micro targets theo DRI (sodium, calcium, iron, vitamin C)

## Các hàm chính

### `calc_bmr(profile) -> float`

Công thức Mifflin-St Jeor:
- Nam: `10 * weight + 6.25 * height - 5 * age + 5`
- Nữ: `10 * weight + 6.25 * height - 5 * age - 161`

### `calc_tdee(profile) -> float`

```python
TDEE = BMR * activity_level.value
```

### `calc_calorie_target(profile) -> float`

- `LOSE_WEIGHT`: TDEE - 500 kcal
- `GAIN_WEIGHT`: TDEE + 300 kcal
- `MAINTAIN`: TDEE

### `calc_macro_targets(calorie_target, goal) -> dict`

Phân bổ macro theo goal:
- `LOSE_WEIGHT`: 30% protein / 40% carbs / 30% fat
- `GAIN_WEIGHT`: 25% protein / 50% carbs / 25% fat
- `MAINTAIN`: 20% protein / 50% carbs / 30% fat

### `daily_targets(profile) -> dict`

Kết hợp `calc_calorie_target` + `calc_macro_targets` + fiber theo giới tính:
- Nữ: 25g fiber
- Nam: 38g fiber

### `daily_micro_targets(profile) -> dict`

Theo khuyến nghị DRI cho người trưởng thành (age >= 18):
- Sodium: ≤ 2300 mg
- Calcium: 1000 mg (18-50), 1200 mg (nữ > 50 hoặc nam > 70)
- Iron: 18 mg (nữ 18-50), 8 mg (nam hoặc nữ > 50)
- Vitamin C: 90 mg (nam), 75 mg (nữ)

Ném `ValueError` nếu `age < 18`.

### `daily_all_targets(profile) -> dict`

Gộp macro + micro targets thành 1 dict (9 chỉ số).

## Kiểm thử (`tests/test_nutrition.py`)

22 bài unit test bao phủ:
- Constructor mặc định và custom (`DietType`, `medical_conditions`)
- Thứ tự positional args không bị ảnh hưởng bởi trường mới
- BMR nam/nữ đúng giá trị chuẩn Mifflin-St Jeor
- TDEE theo hệ số vận động
- Calorie target theo goal (lose/maintain/gain)
- Macro distribution đúng tỷ lệ
- Fiber target đúng giới tính (nam 38g, nữ 25g)
- Micro targets theo DRI: sodium, calcium, iron, vitamin C theo tuổi/giới
- `daily_all_targets()` trả đủ 9 chỉ số
