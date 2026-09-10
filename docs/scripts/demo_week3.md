# `scripts/demo_week3.py`

## Mục đích

Demo minh họa **tuần 3**: nhập hồ sơ người dùng → tính nhu cầu dinh dưỡng → dựng thực đơn mẫu → đánh giá.

## Luồng chạy

1. Tạo `UserProfile` cứng (hardcoded): Nam 22 tuổi, 170cm/65kg, vận động vừa, duy trì cân nặng, 2 món/bữa.
2. Tính BMR, TDEE, calo mục tiêu, macro targets.
3. Nạp `merged_food_nutrition.csv` (15.929 món) qua `load_food_db()` + `build_food_map()`.
4. Dựng thực đơn mẫu từ 8 món đã chọn sẵn (`SAMPLE`).
5. Kiểm tra ràng buộc (`validate_menu`).
6. Tính fitness chi tiết (`evaluate_breakdown`).

## Dữ liệu mẫu

| Bữa | Món | Khẩu phần |
| :--- | :--- | :--- |
| Breakfast | Phở mát, ALL-NATURAL BAGELS | 88g, 135g |
| Lunch | Gạo tẻ máy, Thịt lợn nửa nạc nửa mỡ | 171g, 99g |
| Dinner | Cá hồi, Măng khô | 115g, 66g |
| Snack | Chuối tiêu, AMPORT FLAX SEEDS | 169g, 48g |

## Kết quả demo

```
BMR: 1607.5 kcal
TDEE: 2491.6 kcal
Calo mục tieu: 2491.6 kcal
protein_g: 124.6, carbs_g: 311.5, fat_g: 83.1, fiber_g: 38.0

Thuc don mau: 2253.3 kcal
Khong vi pham rang buoc.
fitness=92.9
```

## Chạy

```bash
python scripts/demo_week3.py
```
