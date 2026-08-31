# Phân Công Công Việc Tuần 3 — Mô Hình Bài Toán

Nhóm: Lê Quang Duy (trưởng nhóm) · Đặng Nguyễn Minh Đăng · Hồ Trung Cương

## Mục tiêu tuần 3 (theo đề cương)
Xây dựng mô hình bài toán: biểu diễn thực đơn, xác định ràng buộc và hàm đánh giá chất lượng thực đơn.

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

## Checklist từng thành viên

### 1. Đăng — Hồ sơ & nhu cầu dinh dưỡng
- [ ] Bổ sung trường khác cần thiết cho `UserProfile` (vd: tình trạng bệnh lý).
- [ ] Công thức BMR theo Mifflin-St Jeor, TDEE theo hệ số vận động.
- [ ] Xác định ngưỡng dinh dưỡng chuẩn theo DRI cho từng đối tượng.
- [ ] Viết test: `tests/test_nutrition.py`.

### 2. Cương — Biểu diễn thực đơn
- [ ] Chuẩn hóa `Menu.decode()` tương ứng đúng cách mã hóa vector nghiệm của IDBO.
- [ ] Hỗ trợ khẩu phần theo gram; kiểm tra nạp dữ liệu `merged_food_nutrition.csv`.
- [ ] Viết test: `tests/test_menu.py` (encode rồi decode ra đúng menu).

### 3. Duy — Ràng buộc & hàm mục tiêu + tích hợp
- [ ] Hoàn thiện các ràng buộc (số món, khẩu phần, sở thích, lặp món).
- [ ] Cân chỉnh trọng số hàm mục tiêu; thêm đa dạng theo tuần nếu cần.
- [ ] Tích hợp và viết test tích hợp end-to-end: `tests/test_model.py`.
- [ ] Họp nhóm: chốt format nghiệm chung trước khi sang tuần 4 (DBO).

## Quy ước chung
- Mọi số liệu tính trên **100g** khẩu phần chuẩn (`serving_size_g = 100`).
- Kiểm thử bằng `pytest`; trước khi merge phải chạy `python -m pytest tests/`.
- Cập nhật README.md khi hoàn tất.
