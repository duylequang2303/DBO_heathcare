# Báo Cáo Tiến Độ Tuần 11 — Phần Đặng Nguyễn Minh Đăng

**Họ và tên:** Đặng Nguyễn Minh Đăng  
**MSSV:** 2001230175  
**Đề tài:** Hệ Thống Đề Xuất Thực Đơn Dinh Dưỡng Cá Nhân Hóa Dựa Trên Thuật Toán Dung Beetle Optimizer (DBO / IDBO)  
**Nhiệm vụ Tuần 11:** Chuẩn hóa Giao diện Web (UI Hardening), Đồng bộ Hợp đồng API & Trực quan hóa Dinh dưỡng Bệnh lý  
**Nhánh Git:** `feat/week11-demo-hardening` (PR #35)  

---

## 1. Mục Tiêu & Phạm Vi Công Việc

Theo phân công trong `docs/tasks/TASK_WEEK11_DEMO_HARDENING.md` (Cookbook cho Đăng + Cương), giai đoạn Tuần 11 tập trung rà soát, làm sạch và ổn định toàn bộ hệ thống trước thềm bảo vệ khóa luận. Phạm vi đóng góp của Đặng Nguyễn Minh Đăng (TASK 3) tập trung vào:

1. **Chuẩn hóa nhãn bữa ăn và làm sạch giao diện:**
   - Chuyển đổi toàn bộ nhãn bữa ăn kỹ thuật (`breakfast`, `lunch`, `dinner`, `snack`) sang nhãn tiếng Việt thân thiện: **🌅 Sáng**, **☀️ Trưa**, **🌙 Tối**, **🍎 Phụ**.
   - Loại bỏ hoàn toàn mã định danh kỹ thuật (`food_id` dạng thô như `USDA_...`, `VN_...`) khỏi bảng thực đơn hiển thị cho người dùng, bảo đảm tính thẩm mỹ và chuyên nghiệp.

2. **Tích hợp tính năng Đổi món (Swap UI) tương tác tức thời:**
   - Bổ sung nút bấm trực quan `🔄 Đổi món` tại từng dòng trong bảng thực đơn.
   - Bắt sự kiện click và gọi hàm API `apiSwapMenu()` truyền kèm vector khẩu phần hiện tại (`old_portions_g`).
   - Cập nhật tự động bảng món, biểu đồ Radar dinh dưỡng, các thanh tiến độ (Progress Bars) và hiển thị thông báo Toast với chênh lệch calo ($\Delta\text{Calo}$) chính xác.

3. **Chuẩn hóa trường bệnh lý dạng Dropdown:**
   - Thay thế ô nhập liệu văn bản tự do bằng hộp chọn chuẩn hóa (`<select id="medicalCondition">`):
     - *Khỏe mạnh:* Giữ nguyên các mức dinh dưỡng tiêu chuẩn DRI.
     - *Tăng huyết áp (giảm muối):* Tự động siết trần natri mục tiêu $\le 1.500\text{ mg/ngày}$.
     - *Tiểu đường:* Ghi chú quản lý tinh bột theo khuyến nghị.
   - Đồng bộ hai chiều với Preset hồ sơ (P1, P2, P3) và kích hoạt tính toán lại mục tiêu ngay khi thay đổi.

4. **Bảo đảm toàn vẹn hệ thống & kiểm thử:**
   - Sửa lỗi cục bộ `UnboundLocalError` đối với `HTTPException` trong `app/api/services.py`.
   - Bổ sung 4 unit tests kiểm định hợp đồng giao diện trong `tests/test_frontend_contract.py`.
   - Bảo đảm toàn bộ kiểm thử hồi quy của hệ thống đạt trạng thái 100% xanh.

---

## 2. Chi Tiết Các Tệp Tin Đã Cập Nhật

| Tệp tin | Loại thay đổi | Chi tiết nội dung |
|:---|:---|:---|
| `app/static/index.html` | Cập nhật UI | Thay thẻ nhập bệnh lý bằng `<select id="medicalCondition">`; thêm cột `Thao tác` trong bảng thực đơn. |
| `app/static/js/api.js` | Mở rộng API | Cập nhật hàm `apiSwapMenu` hỗ trợ tham số `old_portions_g`. |
| `app/static/js/app.js` | Logic Frontend | Thêm `MEAL_LABELS` tiếng Việt; ẩn `food_id`; thêm handler `handleSwap()` cập nhật radar/progress/toast; đồng bộ dropdown bệnh lý với form profile. |
| `app/static/css/styles.css` | Phong cách CSS | Thêm style hiện đại cho `.btn-swap` (dark glassmorphism, hover glow, micro-animation). |
| `app/api/services.py` | Sửa lỗi backend | Loại bỏ khai báo cục bộ gây `UnboundLocalError` của `HTTPException` trong `generate_menu()`. |
| `tests/test_frontend_contract.py` | Kiểm thử hợp đồng | Thêm 4 bài test kiểm tra cấu trúc DOM, nhãn tiếng Việt, ràng buộc natri tăng huyết áp và biên độ delta đổi món. |

---

## 3. Kết Quả Kiểm Thử & Nghiệm Thu

1. **Khả năng hiển thị và trải nghiệm người dùng:**
   - Bảng thực đơn hiển thị rõ ràng, không còn chứa mã SKU nội bộ `food_id`.
   - Nút `🔄 Đổi món` phản hồi nhanh, trạng thái loading hiển thị rõ ràng và tự động cập nhật lại toàn bộ biểu đồ.
   - Khi chọn "Tăng huyết áp", mục tiêu natri ngay lập tức chuyển thành $1.500\text{ mg}$ theo đúng khuyến nghị tim mạch.

2. **Toàn vẹn kiểm thử tự động:**
   - Kiểm thử contract frontend: `8/8 PASSED`.
   - Kiểm thử backend hardening (seed âm, allergies ngắn, swap id lạ): `10/10 PASSED`.
   - Toàn bộ test suite hệ thống chạy ổn định và đạt chuẩn nghiệm thu theo `AGENTS.md`.
