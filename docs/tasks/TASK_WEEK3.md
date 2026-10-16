# Phân Công Công Việc Tuần 3 — Mô Hình Bài Toán

Nhóm: Lê Quang Duy (trưởng nhóm) · Đặng Nguyễn Minh Đăng · Hồ Trung Cương

## Mục tiêu tuần 3 (theo đề cương)
Xây dựng mô hình bài toán: biểu diễn thực đơn, xác định ràng buộc và hàm đánh giá chất lượng thực đơn.

## Trạng thái
Khung mã nguồn đã được trưởng nhóm dựng sẵn và chạy thử OK. Các thành viên hoàn thiện phần được giao + viết test tương ứng.

## Kiến trúc khung

```text
src/
├── models/
│   ├── user_profile.py   # Hồ sơ người dùng (UserProfile, giới tính, mức vận động, mục tiêu)
│   ├── menu.py           # Biểu diễn thực đơn: MenuItem, Meal, Menu + encode/decode
│   ├── constraints.py    # Các ràng buộc dinh dưỡng, năng lượng, số món, khẩu phần, sở thích
│   └── objective.py      # Hàm mục tiêu (fitness) cân bằng đáp ứng/sở thích/đa dạng
└── utils/
    ├── data_loader.py    # Nạp merged_food_nutrition.csv
    └── nutrition.py      # BMR, TDEE, nhu cầu năng lượng & ngưỡng dinh dưỡng
```

## Phân công

| Thành viên | Mô-đun | File | Nội dung chính |
| :--- | :--- | :--- | :--- |
| Đặng Nguyễn Minh Đăng | Hồ sơ & nhu cầu | `src/models/user_profile.py`, `src/utils/nutrition.py` | Hồ sơ người dùng, BMR/TDEE, ngưỡng năng lượng & macro |
| Hồ Trung Cương | Biểu diễn nghiệm | `src/models/menu.py`, `src/utils/data_loader.py` | Thực đơn, encode/decode vector ↔ thực đơn cho IDBO |
| Lê Quang Duy (trưởng) | Ràng buộc & hàm mục tiêu + tích hợp | `src/models/constraints.py`, `src/models/objective.py` | Kiểm tra ràng buộc, hàm fitness, kiểm thử tổng |

Ghi chú:
- `src/utils/data_loader.py` thuộc quyền Cương nhưng dùng chung; nếu cần sửa phải báo trong nhóm.
- Format nghiệm IDBO đã chốt ở mục **Hướng dẫn cho Cương** bên dưới. Cương bám spec đó khi viết `encode`/`decode` và `tests/test_menu.py`.

## Checklist từng thành viên (kèm tiêu chí nghiệm thu)

### 1. Đăng — Hồ sơ & nhu cầu dinh dưỡng
- [x] Bổ sung trường cần thiết cho `UserProfile` (tình trạng bệnh lý, mục tiêu giảm mỡ/tăng cơ, vùng ăn chay...).
- [x] Hoàn thiện BMR theo Mifflin-St Jeor, TDEE theo hệ số vận động.
- [x] Xác định ngưỡng dinh dưỡng theo DRI: calories, protein, carb, fat, fiber, sodium, calcium, iron, vitamin C.
- [x] Viết test `tests/test_nutrition.py`.

**Nghiệm thu:** BMR nam/nữ đúng giá trị chuẩn Mifflin-St Jeor cho bộ số test mẫu; mỗi hàm trả số dương hợp lý; 22/22 test passed.

#### Chi tiết triển khai phần Đăng (Hồ sơ & Nhu cầu dinh dưỡng)

**1. Mở rộng `UserProfile` (`src/models/user_profile.py`)**
- Bổ sung Enum `DietType`: `STANDARD` (mặc định), `VEGETARIAN`, `VEGAN`, `KETO`.
- Đặt `medical_conditions: list[str]` (default: `[]`) và `diet_type: DietType` (default: `DietType.STANDARD`) **sau** `meal_counts` để giữ nguyên thứ tự đối số vị trí (positional constructor), đảm bảo 100% tương thích ngược.

**2. Hoàn thiện tính toán dinh dưỡng & chuẩn DRI (`src/utils/nutrition.py`)**
- **BMR (Mifflin-St Jeor):**
  - Nam: `BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5`
  - Nữ: `BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161`
- **TDEE & Năng lượng mục tiêu:**
  - `TDEE = BMR * ActivityLevel` (`SEDENTARY`: 1.2, `LIGHT`: 1.375, `MODERATE`: 1.55, `ACTIVE`: 1.725, `VERY_ACTIVE`: 1.9).
  - Mục tiêu calo: `LOSE_WEIGHT` (-500 kcal), `GAIN_WEIGHT` (+300 kcal), `MAINTAIN` (giữ nguyên TDEE).
- **Phân bổ đa lượng (Macros):**
  - `LOSE_WEIGHT`: 30% Protein / 40% Carbs / 30% Fat
  - `GAIN_WEIGHT`: 25% Protein / 50% Carbs / 25% Fat
  - `MAINTAIN`: 20% Protein / 50% Carbs / 30% Fat
- **Sửa lỗi tính chất xơ (`fiber_g`):** So sánh `profile.gender == Gender.FEMALE` để trả đúng 25g cho nữ và 38g cho nam.
- **Ngưỡng vi chất theo khuyến nghị DRI theo độ tuổi & giới tính (`daily_micro_targets`):**
  - Kiểm tra độ tuổi: chặn hồ sơ dưới 18 tuổi (`ValueError`).
  - Sodium (Na): $\le 2300$ mg/ngày (mức giới hạn UL cho người trưởng thành).
  - Calcium (Ca): 1000 mg/ngày (18-50 tuổi); 1200 mg/ngày cho nữ > 50 tuổi và người cao tuổi > 70 tuổi.
  - Iron (Fe): 18 mg/ngày cho nữ 18-50 tuổi; 8 mg/ngày cho nam và nữ > 50 tuổi (sau mãn kinh).
  - Vitamin C: 90 mg/ngày cho nam, 75 mg/ngày cho nữ.
- **Hàm tích hợp (`daily_all_targets`):** Gộp toàn bộ 9 chỉ số (5 macros + 4 micros) phục vụ bài toán tối ưu.

**3. Bộ kiểm thử (`tests/test_nutrition.py`)**
- 22 bài unit test bao phủ toàn bộ: BMR, TDEE, Calorie targets, Macro distribution, Fiber gender check, Micro DRI theo tuổi/giới tính, validation tuổi, positional constructor order, All targets.

### 2. Cương — Biểu diễn thực đơn
- [ ] Chuẩn hóa `Menu.decode()` khớp đúng cách mã hóa vector nghiệm của IDBO (format đã chốt bên dưới).
- [ ] Gắn `meal_type` vào từng `MenuItem` khi decode/nạp từ CSV. Ràng buộc bữa (breakfast/snack đúng bữa; lunch/dinner lấy `all`) do Duy kiểm tra ở `constraints.py` — Cương chỉ cần dữ liệu món mang đúng nhãn.
- [ ] Hỗ trợ khẩu phần theo gram; kiểm tra nạp `merged_food_nutrition.csv` (15.929 món) trong `data_loader.py`.
- [ ] Viết test `tests/test_menu.py`.

**Nghiệm thu:** Round-trip `encode() → decode()` trả đúng menu ban đầu; nạp đủ dữ liệu không lỗi.

#### Hướng dẫn cho Cương (format nghiệm đã chốt)

Trưởng nhóm đã chốt format trước tuần 4. Làm đúng spec này, không đổi cách xếp vector.

**Vector nghiệm IDBO**

- `x` (liên tục): khẩu phần gram, độ dài `n = sum(meal_counts)`.
- `food_ids` (rời rạc): cùng độ dài, cùng thứ tự.
- Thứ tự bữa cố định: `breakfast → lunch → dinner → snack`.
- Mỗi bữa một **khối liên tục**, không xen kẽ `i::4`.

```text
x = [p_bf_1, ..., p_bf_k, p_lunch_1, ..., p_dinner_1, ..., p_snack_1, ...]
food_ids = [id_bf_1, ..., id_bf_k, id_lunch_1, ..., ...]
```

Biên khẩu phần: `25 <= x_i <= 350`. Dinh dưỡng tính trên 100g: `nutrient * portion_g / 100`.

**API phải giữ**

```python
Menu.encode() -> list[float]          # vector khau phan, thu tu all_items()
Menu.food_ids() -> list[str]
Menu.meal_counts() -> dict[str, int]  # so mon moi bua, dung khi decode
Menu.decode(food_ids, portions_g, food_map, meal_counts) -> Menu
```

`meal_counts` bat buoc, vi du `{"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 2}`. Khong uoc luong khi thieu. Round-trip phai giu bien bua (ke ca [1, 2, 3, 0]). Gia tri am bi reject.

**`meal_type` trên món (CSV)**

| Nhãn CSV | Bữa được xếp |
| :--- | :--- |
| `breakfast` | chỉ breakfast |
| `snack` | chỉ snack |
| `all` | lunch và dinner |

Khi tạo `MenuItem` từ `food_map`, copy `row["meal_type"]`. Giá trị thiếu coi như `""` (constraints sẽ bỏ qua).

**`data_loader.py`**

- `load_food_db()` nạp `data/processed/merged_food_nutrition.csv`.
- `build_food_map(df)` → `dict[food_id, row]`.
- NaN dinh dưỡng → `0`. Không sửa `scripts/preprocess_data.py`.

**Test `tests/test_menu.py` (bắt buộc)**

1. Nạp CSV: `len(df) == 15929`, có cột `food_id`, `food_name`, `meal_type`, `calories`.
2. Round-trip: dựng menu → `encode()` + `food_ids()` → `decode(...)` → cùng `food_id` và `portion_g` từng bữa.
3. `decode(..., meal_counts=...)` xếp đúng số món mỗi bữa.
4. `MenuItem.nutrient("calories")` đúng công thức `calories * portion_g / 100`.
5. `meal_type` sau decode khớp CSV (`breakfast`/`snack`/`all`).

Nhánh gợi ý: `git checkout -b 260905-feat-week3-menu-encode`. File được phép sửa: `src/models/menu.py`, `src/utils/data_loader.py`, `tests/test_menu.py`. Không đụng `constraints.py` / `objective.py`.

### 3. Duy — Ràng buộc & hàm mục tiêu + tích hợp
- [x] Hoàn thiện các ràng buộc (số món, khẩu phần, sở thích, không lặp món trong ngày).
- [x] Cân chỉnh trọng số hàm mục tiêu; đảm bảo fitness nằm trong khoảng ổn định.
- [x] Tích hợp và viết test end-to-end `tests/test_model.py` (nạp dữ liệu thật → dựng menu → đánh giá).
- [x] Chủ trì họp nhóm chốt format nghiệm chung trước tuần 4 (DBO).

**Nghiệm thu:** Menu hợp lệ có fitness cao hơn menu ngẫu nhiên; test end-to-end chạy qua với dữ liệu thật.

## Đầu ra cuối tuần 3
- [x] Phần Duy (ràng buộc, hàm mục tiêu, tích hợp e2e) hoàn thiện + test xanh (`python -m pytest tests/`).
- [x] Phần Đăng (`user_profile.py`, `nutrition.py`, `tests/test_nutrition.py`) hoàn thiện + test xanh.
- [x] Phần Cương (`menu.py` encode/decode, `data_loader.py`, `tests/test_menu.py`) hoàn thiện + test xanh.
- [x] Demo: nhập hồ sơ người dùng → tính nhu cầu → dựng 1 thực đơn mẫu → đánh giá.
- [x] Cập nhật README.md mô tả mô hình bài toán.

## Kết quả kiểm thử tuần 3

```text
============================= 111 passed in 0.78s ==============================
```

| File test | Số test | Nội dung chính |
| :--- | :--- | :--- |
| `tests/test_nutrition.py` | 22 | BMR/TDEE, macro/micro targets, DRI theo tuổi/giới |
| `tests/test_menu.py` | 11 | Load CSV, encode/decode round-trip, meal_counts, meal_type |
| `tests/test_model.py` | 14 | End-to-end: nạp dữ liệu thật → menu → ràng buộc → fitness |
| `tests/test_objective.py` | 4 | Trọng số, fitness range, preference, diversity |

### Lệnh chạy test tuần 3

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Quy trình làm việc (Git)
1. Mỗi thành viên tạo nhánh riêng: `git checkout -b 310826-feat-week3-<tên-chức-năng>`.
2. Commit rõ ràng, ví dụ: `feat(nutrition): add DRI thresholds`.
3. Push và tạo Merge Request (MR) về `main`.
4. Trưởng nhóm review + merge; trước khi merge chạy `python -m pytest tests/`.

## Quy ước chung
- Mọi số liệu tính trên **100g** khẩu phần chuẩn (`serving_size_g = 100`).
- Không chỉnh sửa `scripts/preprocess_data.py` khi chưa bàn trong nhóm (đảm bảo dữ liệu tái lập được).
- Mọi giá trị thiếu xem như 0 khi tính toán.
