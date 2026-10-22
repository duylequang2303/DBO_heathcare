# Báo Cáo Tiến Độ Tuần 10 — Phần Đặng Nguyễn Minh Đăng

**Họ và tên:** Đặng Nguyễn Minh Đăng  
**MSSV:** 2001230175  
**Đề tài:** Hệ Thống Đề Xuất Thực Đơn Dinh Dưỡng Cá Nhân Hóa Dựa Trên Thuật Toán Dung Beetle Optimizer (DBO / IDBO)  
**Nhiệm vụ Tuần 10:** Xây dựng Giao diện Web (Frontend) & Trực quan hóa Dinh dưỡng  
**Nhánh Git:** `261017-feat-week10-ui`  

---

## 1. Mục Tiêu & Phạm Vi Công Việc

Theo phân công trong `docs/tasks/TASK_WEEK10.md`, giai đoạn Tuần 10 đưa hệ thống solver từ CLI sang nền tảng Web với kiến trúc một tiến trình một cổng (FastAPI mount `StaticFiles`). Phạm vi đóng góp của Đặng Nguyễn Minh Đăng tập trung vào:

1. **Khung giao diện người dùng (`app/static/index.html`, `app/static/css/styles.css`):**
   - Thiết kế giao diện hiện đại (dark theme glassmorphism), responsive, trực quan, không dùng framework nặng.
   - Bố cục 2 cột: Cột trái (Form hồ sơ + Điều khiển) và Cột phải (Kết quả thực đơn + Trực quan hóa dinh dưỡng).
2. **Xử lý logic giao diện & kết nối API (`app/static/js/api.js`, `app/static/js/app.js`):**
   - Nạp nhanh các hồ sơ mẫu chuẩn hóa (P1, P2, P3).
   - Tương tác với backend qua API `/api/targets` (tính BMR/TDEE và phân bổ macro tức thời) và `/api/menu/generate` (chạy solver 2 tầng).
   - Modal thay món (Swap UI) tương tác với `/api/menu/swap`.
3. **Trực quan hóa dinh dưỡng (`app/static/js/charts.js`):**
   - Thanh tiến độ (Progress Bars) với khoảng dung sai dinh dưỡng chuẩn (`±10%` Calo, `±15%` Protein & Carbs, `±20%` Fat, `±30%` Fiber).
   - Biểu đồ mạng nhện (Radar Chart bằng Chart.js) thể hiện tỷ lệ % đạt mục tiêu đa chiều.
   - Badge cảnh báo vi phạm dinh dưỡng và ràng buộc thực đơn từ hàm thẩm định `validate_menu()`.

---

## 2. Chi Tiết Các Thành Phần Giao Diện Đã Xây Dựng

### 2.1. Form Nhập Hồ Sơ Cá Nhân Hóa & Cấu Hình Thuật Toán
- **Preset hồ sơ:** Cung cấp 3 nút bấm nạp nhanh dữ liệu mẫu:
  - *P1:* Nam văn phòng 28 tuổi, duy trì cân nặng (TDEE ~2492 kcal).
  - *P2:* Nữ văn phòng 35 tuổi, thừa cân, giảm cân (TDEE ~1838 kcal).
  - *P3:* Nam lớn tuổi 62 tuổi, tiền đái tháo đường & tăng huyết áp.
- **Thông số cá nhân:** Tuổi, giới tính, chiều cao (cm), cân nặng (kg), mức độ vận động (5 mức), mục tiêu cân nặng (3 mức).
- **Ràng buộc khẩu vị & bệnh lý:** Chọn dị ứng (đậu phộng, hải sản, sữa, trứng,...), thực phẩm kiêng/ghét, bệnh lý kèm theo.
- **Cấu hình solver:** Cho phép chọn cấu hình (`web`, `smoke`, `full`) và nhập `seed` (mặc định 9001) nhằm bảo đảm tính tái lập kết quả.

### 2.2. Bảng Thực Đơn Chi Tiết & Quy Định Khẩu Phần
- Bảng thực đơn chia rõ theo các bữa ăn trong ngày (Sáng, Trưa, Tối, Bữa phụ).
- **Tuân thủ quy định khẩu phần (AGENTS.md):**
  - Hiển thị song song hai cột: **Gram liên tục (gốc từ solver)** và **Gram làm tròn 5g** (`portion_g_rounded`).
  - Mọi số liệu calo, protein, carbs, fat, fiber, natri hiển thị trên bảng đều được tính toán lại chính xác dựa trên khối lượng thực tế.
- **Tương tác thay món:** Mỗi dòng món ăn tích hợp nút bấm "Đổi món" mở modal để người dùng chọn món mới trong danh mục bữa hoặc để hệ thống tự động lấy mẫu thay thế hợp lệ.

### 2.3. Trực Quan Hóa Dinh Dưỡng Đa Chiều
- **Thanh tiến độ (Nutrient Progress Bars):**
  - Tính toán tỷ lệ phần trăm thực tế so với mục tiêu (`actual / target * 100%`).
  - Phân màu chỉ báo trực quan theo dải dung sai nghiêm ngặt:
    - Xanh lục: Đạt chuẩn trong dải dung sai cho phép.
    - Vàng: Lệch nhẹ (cận biên).
    - Đỏ: Vượt quá hoặc thiếu hụt nghiêm trọng.
- **Biểu đồ Radar (Chart.js):**
  - Trực quan hóa 6 trục dinh dưỡng: Năng lượng, Protein, Carbohydrate, Lipid, Chất xơ và Natri.
  - Vùng mục tiêu chuẩn (100%) hiển thị dưới dạng đường tham chiếu, vùng thực đơn thực tế chồng phủ giúp người dùng dễ dàng đánh giá độ cân đối của bữa ăn.
- **Hệ thống cảnh báo vi phạm:**
  - Danh sách lỗi và cảnh báo được render dưới dạng các thẻ (badges) đỏ/vàng rõ ràng, giúp người dùng nắm bắt ngay lập tức nếu thực đơn vi phạm ràng buộc natri, calo hay tỷ lệ dinh dưỡng.

---

## 3. Kết Quả Kiểm Thử & Nghiệm Thu Giao Diện

1. **Khả năng hoạt động:**
   - Ứng dụng chạy mượt mà trên môi trường trình duyệt thông qua FastAPI server tại `http://localhost:8000/`.
   - Kết nối hai chiều với solver thành công, dữ liệu JSON được parse và hiển thị đúng quy cách.
2. **Tính tái lập và toàn vẹn dữ liệu:**
   - Khi cùng nhập Profile P1 và Seed `9001`, giao diện hiển thị kết quả đồng nhất với kết quả benchmark CLI.
   - Không xuất hiện giá trị `NaN`, số âm hay sai lệch định dạng.
3. **Kiểm thử hồi quy:**
   - Toàn bộ bộ kiểm thử của dự án (`205 passed`) được duy trì nguyên vẹn, không xảy ra xung đột hay phá vỡ logic cũ.

---

## 4. Kết Luận & Hướng Tiếp Tục Tuần 11

Phần việc của Đặng Nguyễn Minh Đăng trong Tuần 10 đã hoàn thành 100% các mục tiêu về giao diện web và trực quan hóa dinh dưỡng theo đúng kế hoạch đề ra trong `TASK_WEEK10.md` và tuân thủ các quy tắc bất biến trong `AGENTS.md`.

Trong Tuần 11, tôi sẽ phối hợp cùng Lê Quang Duy và Hồ Trung Cương để:
- Thực hiện kiểm thử đầu cuối (E2E testing) toàn bộ luồng Người dùng -> UI -> API -> Solver -> Cập nhật Menu.
- Tối ưu hóa trải nghiệm người dùng trên các thiết bị di động (mobile responsiveness).
- Đóng góp số liệu và biểu đồ vào Báo cáo tổng kết toàn diện của nhóm.
