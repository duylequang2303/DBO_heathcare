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

Ghi chú: `src/utils/data_loader.py` thuộc quyền Cương nhưng được cả nhóm dùng chung; nếu cần sửa phải báo trong nhóm.

## Checklist từng thành viên (kèm tiêu chí nghiệm thu)

### 1. Đăng — Hồ sơ & nhu cầu dinh dưỡng
- [ ] Bổ sung trường cần thiết cho `UserProfile` (tình trạng bệnh lý, mục tiêu giảm mỡ/tăng cơ, vùng ăn chay...).
- [ ] Hoàn thiện BMR theo Mifflin-St Jeor, TDEE theo hệ số vận động.
- [ ] Xác định ngưỡng dinh dưỡng theo DRI: calories, protein, carb, fat, fiber, sodium, calcium, iron, vitamin C.
- [ ] Viết test `tests/test_nutrition.py`.

**Nghiệm thu:** BMR nam/nữ đúng giá trị chuẩn Mifflin-St Jeor cho bộ số test mẫu; mỗi hàm trả số dương hợp lý.

### 2. Cương — Biểu diễn thực đơn
- [ ] Chuẩn hóa `Menu.decode()` khớp đúng cách mã hóa vector nghiệm của IDBO (chốt format với trưởng nhóm).
- [ ] Thêm ràng buộc `meal_type` của món với bữa tương ứng (món `breakfast`/`snack` chỉ vào đúng bữa đó; bữa trưa/tối lấy từ nhãn `all`).
- [ ] Hỗ trợ khẩu phần theo gram; kiểm tra nạp `merged_food_nutrition.csv` (15.929 món).
- [ ] Viết test `tests/test_menu.py`.

**Nghiệm thu:** Round-trip `encode() → decode()` trả đúng menu ban đầu; nạp đủ dữ liệu không lỗi.

### 3. Duy — Ràng buộc & hàm mục tiêu + tích hợp
- [ ] Hoàn thiện các ràng buộc (số món, khẩu phần, sở thích, không lặp món trong ngày).
- [ ] Cân chỉnh trọng số hàm mục tiêu; đảm bảo fitness nằm trong khoảng ổn định.
- [ ] Tích hợp và viết test end-to-end `tests/test_model.py` (nạp dữ liệu thật → dựng menu → đánh giá).
- [ ] Chủ trì họp nhóm chốt format nghiệm chung trước tuần 4 (DBO).

**Nghiệm thu:** Menu hợp lệ có fitness cao hơn menu ngẫu nhiên; test end-to-end chạy qua với dữ liệu thật.

## Đầu ra cuối tuần 3
- [ ] Tất cả module hoàn thiện + test xanh (`python -m pytest tests/`).
- [ ] Demo: nhập hồ sơ người dùng → tính nhu cầu → dựng 1 thực đơn mẫu → đánh giá.
- [ ] Cập nhật README.md mô tả mô hình bài toán.

## Quy trình làm việc (Git)
1. Mỗi thành viên tạo nhánh riêng: `git checkout -b 310826-feat-week3-<tên-chức-năng>`.
2. Commit rõ ràng, ví dụ: `feat(nutrition): add DRI thresholds`.
3. Push và tạo Merge Request (MR) về `main`.
4. Trưởng nhóm review + merge; trước khi merge chạy `python -m pytest tests/`.

## Quy ước chung
- Mọi số liệu tính trên **100g** khẩu phần chuẩn (`serving_size_g = 100`).
- Không chỉnh sửa `scripts/preprocess_data.py` khi chưa bàn trong nhóm (đảm bảo dữ liệu tái lập được).
- Mọi giá trị thiếu xem như 0 khi tính toán.
