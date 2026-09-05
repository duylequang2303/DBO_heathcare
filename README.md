# DBO_heathcare

Hệ thống đề xuất thực đơn dinh dưỡng cá nhân hóa dựa trên thuật toán Dung Beetle Optimizer cải tiến với cơ chế ngẫu nhiên (IDBO).

**Mã đề tài:** CNTT-KLCN142
**Khóa luận cử nhân ngành CNTT (2025 - 2026)**
Trường Đại học Công Thương TP.HCM - Khoa Công nghệ Thông tin
GVHD: Đinh Nguyễn Trọng Nghĩa (`nghiadnt@huit.edu.vn`)

| Thành viên | MSSV | Vai trò tuần 3 |
| :--- | :--- | :--- |
| Lê Quang Duy | 2001230123 | Trưởng nhóm — ràng buộc, hàm mục tiêu, tích hợp |
| Đặng Nguyễn Minh Đăng | 2001230175 | Hồ sơ người dùng, BMR/TDEE, ngưỡng dinh dưỡng |
| Hồ Trung Cương | 2001230070 | Biểu diễn thực đơn, encode/decode nghiệm IDBO |

Đề cương chi tiết: `docs/CNTT-KLCN142 - ing.docx`. Phân công tuần 3: `docs/TASK_WEEK3.md`.

## Mục tiêu

1. Nghiên cứu và xây dựng mô hình bài toán tối ưu thực đơn dinh dưỡng cá nhân hóa.
2. Xây dựng Dung Beetle Optimizer cải tiến với cơ chế ngẫu nhiên (IDBO) nhằm nâng cao khả năng tìm kiếm.
3. Phát triển hệ thống web hỗ trợ tự động xây dựng và đề xuất thực đơn phù hợp với từng người dùng.
4. Đánh giá IDBO trên hàm benchmark và so sánh với DBO gốc về chất lượng thực đơn, mức đáp ứng dinh dưỡng và thời gian thực thi.

## Phạm vi nghiên cứu (theo đề cương)

- Cơ sở dữ liệu thực phẩm: năng lượng, protein, carbohydrate, chất béo, chất xơ và vi chất (sodium, calcium, iron, vitamin C).
- Hồ sơ người dùng: tuổi, giới tính, chiều cao, cân nặng, mức vận động, mục tiêu dinh dưỡng.
- Thực đơn theo ngày: các bữa ăn và khẩu phần từng món.
- Ràng buộc: dinh dưỡng, tổng năng lượng, số món, khẩu phần, sở thích / thực phẩm không phù hợp.
- Thuật toán: cài DBO gốc, đề xuất IDBO (random perturbation / random restart), biểu diễn nghiệm và hàm mục tiêu.
- Website: nhập thông tin, thiết lập mục tiêu, tạo thực đơn, xem dinh dưỡng, thay món.
- Đánh giá: sai lệch dinh dưỡng, mức đáp ứng nhu cầu, chất lượng nghiệm, độ ổn định, thời gian thực thi.

## Môi trường kỹ thuật

| Thành phần | Lựa chọn |
| :--- | :--- |
| Ngôn ngữ | Python |
| Web | FastAPI / Flask / Django |
| Tính toán | NumPy, Pandas, SciPy |
| CSDL | SQLite / PostgreSQL |
| Giao diện | HTML, CSS, JavaScript |
| Trực quan hóa | Matplotlib, thư viện biểu đồ web |
| Công cụ | VS Code, Git |

## Lộ trình 12 tuần (17/08/2026 – 08/11/2026)

| Tuần | Nội dung |
| :--- | :--- |
| 1 | Tổng quan bài toán lập thực đơn, dinh dưỡng cá nhân hóa, phương pháp tối ưu |
| 2 | Nhu cầu năng lượng, thành phần dinh dưỡng, nguồn dữ liệu thực phẩm |
| 3 | Mô hình bài toán: biểu diễn thực đơn, ràng buộc, hàm đánh giá |
| 4 | Nghiên cứu, cài đặt và kiểm thử DBO |
| 5 | Cơ chế ngẫu nhiên cải tiến DBO (đa dạng quần thể, hạn chế hội tụ sớm) |
| 6 | IDBO và đánh giá trên hàm benchmark cơ bản |
| 7 | Chuyển IDBO sang tối ưu thực đơn; biểu diễn nghiệm, xử lý ràng buộc |
| 8 | Hoàn thiện hàm mục tiêu; thử nghiệm theo nhóm nhu cầu / mức vận động |
| 9 | So sánh IDBO vs DBO vs phương pháp cơ sở; backend API + giao diện nhập liệu |
| 10 | Tích hợp IDBO; tạo thực đơn, hiển thị dinh dưỡng, thay món |
| 11 | Kiểm thử hệ thống, tổng hợp thực nghiệm, chỉnh báo cáo |
| 12 | Hoàn thiện báo cáo, hướng dẫn, demo, chuẩn bị bảo vệ |

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

Chi tiết API cho module biểu diễn: mục **Hướng dẫn cho Cương** trong `docs/TASK_WEEK3.md`.

## Cấu trúc dự án

```text
DBO_heathcare/
├── data/
│   ├── raw/                         # USDA + bảng thành phần VN
│   └── processed/merged_food_nutrition.csv
├── src/
│   ├── models/                      # UserProfile, Menu, ràng buộc, fitness
│   ├── utils/                       # data_loader, BMR/TDEE
│   ├── algorithms/                  # DBO / IDBO (tuần 4+)
│   └── api/                         # Backend web (tuần 9+)
├── web/                             # Giao diện (tuần 9+)
├── scripts/
│   ├── preprocess_data.py
│   └── demo_week3.py
├── tests/
├── docs/
│   ├── CNTT-KLCN142 - ing.docx      # Đề cương
│   └── TASK_WEEK3.md
├── requirements.txt
└── README.md
```

## Cài đặt và chạy

```bash
# Cài thư viện
pip install -r requirements.txt

# Test
python -m pytest tests/

# Demo tuần 3: hồ sơ -> nhu cầu -> thực đơn mẫu -> đánh giá
python scripts/demo_week3.py
```

## Tài liệu tham khảo

1. J. Xue and B. Shen, "Dung beetle optimizer: a new meta-heuristic algorithm for global optimization," The Journal of Supercomputing, vol. 79, pp. 7305-7336, 2023.
2. M. Amiri, J. Li, and W. Hasan, "Personalized Flexible Meal Planning for Individuals With Diet-Related Health Concerns," JMIR Formative Research, vol. 7, e46434, 2023.
3. National Academies of Sciences, Engineering, and Medicine, Dietary Reference Intakes for Energy, 2023.
4. FastAPI Documentation, https://fastapi.tiangolo.com.
