# KẾ HOẠCH FIX TOÀN DIỆN CHO NGÀY MAI (DỰA TRÊN AUDIT TUẦN 11)

Tài liệu này tổng hợp **5 hạt sạn lớn nhất** được phát hiện từ đợt kiểm thử thực tế (422 HTTP requests, 219 thực đơn) của bot phản biện và đợt test tay của bạn trên giao diện web.

---

## 📌 DANH SÁCH 5 VIỆC CẦN FIX CHI TIẾT

### 1. Siết biên khẩu phần theo vai trò món (Role Bounds) & Truyền `food_map`
- **Vấn đề hiện tại:** 29.7% thực đơn có món bị solver đẩy chạm trần kỹ thuật **350g** (ví dụ: ăn 350g sữa chua hoặc 350g rau/măng một bữa). Nguyên nhân: Hàm `generate_menu` chưa truyền `food_map` vào `validate_menu`, và inner solver vẫn dùng bounds chung `[25, 350]` cho mọi loại thực phẩm.
- **Hành động cần làm:**
  - Truyền `food_map` vào `validate_menu` trong `app/api/services.py`.
  - Giới hạn `lb/ub` của inner solver theo vai trò món (`staple`: 80-250g, `main_dish`: 60-200g, `side_dish/soup`: 50-250g, `dessert/snack`: 50-150g).

### 2. Xây dựng từ điển Dị ứng (Allergen Dictionary)
- **Vấn đề hiện tại:** Bộ lọc dị ứng chỉ so khớp chuỗi ký tự con (`substring match`). Khi người dùng gõ *"hải sản"*, hệ thống không chặn được *"tôm"*, *"cua"*, *"cá"*, *"mực"*.
- **Hành động cần làm:**
  - Bổ sung bảng ánh xạ nhóm dị ứng (`ALLERGEN_TAXONOMY`):
    - `hải sản` $\rightarrow$ `['tôm', 'cua', 'cá', 'mực', 'nghêu', 'sò', 'ốc', 'hàu', 'bạch tuộc']`.
    - `đậu` $\rightarrow$ `['đậu phộng', 'đậu nành', 'đậu phụ', 'đỗ']`.
    - `sữa` $\rightarrow$ `['sữa bò', 'sữa dê', 'phô mai', 'sữa chua', 'bơ']`.
  - Thêm unit test kiểm tra từ khóa nhóm dị ứng trong `tests/test_constraints.py`.

### 3. Sửa lỗi hiển thị Điểm số khi Đổi món (Swap UI & Backend)
- **Vấn đề hiện tại:** Sau khi bấm Đổi món, frontend giữ lại điểm `fitness` cũ (`res.fitness = res.fitness ?? state.menu?.fitness`) do schema `SwapOut` của backend không tính lại điểm fitness.
- **Hành động cần làm:**
  - Trong `app/api/swap.py`: Sau khi decode menu mới, tính toán lại điểm fitness (`calculate_fitness(menu_new, profile, targets)`) và gán vào `SwapOut`.
  - Cập nhật schema `SwapOut` trong `app/api/schemas.py` có thêm trường `fitness: float`.
  - Trên frontend `app.js`: Cập nhật trực tiếp số điểm fitness mới lên góc trên cùng.

### 4. Bổ sung Khối Cảnh báo Y tế & Giới hạn Dữ liệu (Medical Warnings)
- **Vấn đề hiện tại:** Khi chọn Tiểu đường, backend chưa trả về cảnh báo nào trong JSON response (chỉ có dòng chữ tĩnh trên web).
- **Hành động cần làm:**
  - Bổ sung trường `warnings: list[str]` và `data_limitations: list[str]` vào schema `MenuResponse` và `SwapOut`.
  - Khi `diabetes` được chọn: Trả cảnh báo *"Dữ liệu chưa có chỉ số đường tổng (sugar), thực đơn này chỉ hỗ trợ kiểm soát calo và tinh bột, không bảo đảm an toàn lâm sàng cho bệnh nhân tiểu đường."*
  - Gắn disclaimer chính thức: *"Sản phẩm là prototype kỹ thuật hỗ trợ quyết định, không phải thiết bị y tế."*

### 5. Tinh chỉnh Trải nghiệm Người dùng (UX & Việt hóa Lỗi)
- **Vấn đề hiện tại:** Một số lỗi nhập liệu trả về tiếng Anh kỹ thuật của Pydantic (`Field required`, `Input should be a valid integer`).
- **Hành động cần làm:**
  - Thêm exception handler trong `app/main.py` để map lỗi 422 sang tiếng Việt thân thiện theo từng trường.
  - Ẩn phần chọn `Seed` và cấu hình solver `Smoke / Web / Full` vào nút "Tùy chọn nâng cao" (Advanced settings) để người dùng phổ thông không bị bối rối.
  - Đổi nhãn `Fitness: 87.4 / 100` thành `Độ phù hợp mục tiêu: 87.4%`.

---
*Tài liệu chi tiết đầy đủ 422 request kiểm thử nằm tại: `docs/reports/BAO_CAO_THAM_DINH_HOI_DONG_TUAN_11.md`.*

