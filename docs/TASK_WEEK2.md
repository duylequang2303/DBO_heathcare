# Phân Công Công Việc Tuần 2 — Nhu Cầu Năng Lượng, Dinh Dưỡng & Nguồn Dữ Liệu

Nhóm: Lê Quang Duy (trưởng nhóm) · Đặng Nguyễn Minh Đăng · Hồ Trung Cương

> File hồi tố ghi nhận tiến độ tuần 2 (24/08/2026 – 30/08/2026). Toàn bộ nội dung đã thực hiện, lưu làm hồ sơ theo lộ trình đề cương.

## Mục tiêu tuần 2 (theo đề cương)
Nghiên cứu nhu cầu năng lượng và các thành phần dinh dưỡng; lựa chọn, làm sạch và chuẩn hóa nguồn dữ liệu thực phẩm phục vụ bài toán thực đơn.

## Trạng thái
Đã chốt quy chuẩn cột dữ liệu và pipeline tiền xử lý. Sản phẩm chính: dữ liệu sạch `data/processed/merged_food_nutrition.csv`, tài liệu quy chuẩn `data/README.md` và script tái lập `scripts/preprocess_data.py`.

## Nội dung đã thực hiện

### 1. Nhu cầu năng lượng
- [x] Nghiên cứu BMR theo Mifflin-St Jeor (nam/nữ) và TDEE theo hệ số vận động.
- [x] Chốt mô hình mục tiêu calo theo goal: giảm cân / duy trì / tăng cân.
- [x] Xác định công thức ước lượng macro từ calo (protein/carb/fat theo tỉ lệ mục tiêu) — sẽ hiện thực ở tuần 3.

### 2. Thành phần dinh dưỡng
- [x] Chốt bộ chất dinh dưỡng cần theo dõi: `calories`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g`, `sodium_mg`, `calcium_mg`, `iron_mg`, `vitamin_c_mg`.
- [x] Quy ước toàn bộ giá trị tính trên **100g** khẩu phần (`serving_size_g = 100`).
- [x] Lưu ý phương pháp luận: chuyển đổi đơn vị kJ→kcal (÷4.184) là chuẩn hóa đơn vị, không phải suy bù dinh dưỡng theo công thức 4-4-9.

### 3. Nguồn dữ liệu thực phẩm
- [x] Khảo sát và chọn 2 nguồn:
  - USDA FoodData Central (`data/raw/comprehensive_foods_usda.csv`, ~40k dòng).
  - Bảng thành phần thực phẩm Việt Nam (`data/raw/vietnamese_food_composition.csv`).
- [x] Thiết kế quy chuẩn cột chung `merged_food_nutrition.csv` (xem `data/README.md`).

### 4. Tiền xử lý dữ liệu
- [x] Xây `scripts/preprocess_data.py`: đọc 2 nguồn → chuẩn hóa đơn vị → gán nhãn `meal_type` (breakfast/snack/all) → lọc nhóm không phù hợp bữa ăn → dedup theo `food_name` giữ dòng đầy đủ nhất.
- [x] Chạy pipeline tạo `merged_food_nutrition.csv` (15.929 món).
- [x] Viết tài liệu `data/README.md` mô tả cấu trúc cột, đơn vị và ghi chú xử lý.

## Phân công (ghi nhận)

| Thành viên | Mô-đun | Nội dung chính |
| :--- | :--- | :--- |
| Đặng Nguyễn Minh Đăng | Nhu cầu năng lượng | Nghiên cứu BMR/TDEE, macro theo goal, DRI |
| Hồ Trung Cương | Dữ liệu & chuẩn hóa | Khảo sát nguồn USDA/VN, thiết kế schema cột, đánh giá dữ liệu |
| Lê Quang Duy (trưởng) | Pipeline & quy chuẩn | `scripts/preprocess_data.py`, `data/README.md`, chốt quy ước 100g |

## Đầu ra cuối tuần 2
- [x] `data/raw/` chứa đủ dữ liệu gốc USDA + VN.
- [x] `scripts/preprocess_data.py` chạy được, tái lập dữ liệu sạch.
- [x] `data/processed/merged_food_nutrition.csv` (15.929 món) sẵn sàng cho tuần 3.
- [x] `data/README.md` là tài liệu quy chuẩn cột/đơn vị để cả nhóm dùng chung.

## Quy ước chung
- Mọi giá trị thiếu xem như 0 khi tính toán.
- Không sửa file `scripts/preprocess_data.py` khi chưa bàn trong nhóm (đảm bảo dữ liệu tái lập được).

## Tài liệu tham khảo
1. National Academies of Sciences, Engineering, and Medicine, Dietary Reference Intakes for Energy, 2023.
2. USDA FoodData Central, https://fdc.nal.usda.gov.
3. Bảng thành phần thực phẩm Việt Nam — Viện Dinh dưỡng.
