# Báo Cáo Tiến Độ Tuần 11 — Phần Đặng Nguyễn Minh Đăng

**Họ và tên:** Đặng Nguyễn Minh Đăng  
**MSSV:** 2001230175  
**Đề tài:** Hệ Thống Đề Xuất Thực Đơn Dinh Dưỡng Cá Nhân Hóa Dựa Trên Thuật Toán Dung Beetle Optimizer (DBO / IDBO)  
**Nhiệm vụ Tuần 11:** Chuẩn hóa Giao diện Web (UI Hardening), Đồng bộ Hợp đồng API & Trực quan hóa Dinh dưỡng Bệnh lý  
**Nhánh Git:** `fix/c4-role-slot-hardening` (tiếp quản từ `fix/c4-c6-takeover`)  

---

## 1. Mục Tiêu & Phạm Vi Công Việc

Theo phân công trong `docs/tasks/TASK_WEEK11_DEMO_HARDENING.md` và nhiệm vụ tiếp quản `docs/project_notes/TASK_C3_C4.md` (TASK C4):

### Giai đoạn 1 (TASK 3 — UI Hardening):
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

### Giai đoạn 2 (TASK C4 — Phân loại vai trò món & cơ cấu bữa ăn):
4. **Sửa các sai lệch vai trò ẩm thực (`DishRole`):**
   - Tách nhóm sữa / chế phẩm sữa (`DAIRY_PATTERNS`) khỏi `PROTEIN_PATTERNS` để tránh `Sữa bò tươi`, `Sữa chua (từ sữa bò)` bị nhận nhầm thành `MAIN_PROTEIN` do từ "bò".
   - Tách từ "hạt" chung chung trong `SNACK_PATTERNS` thành các loại hạt ăn vặt cụ thể (`hạt dẻ`, `hạt điều`, `hạt sen`...), ngăn `Đậu hà lan (hạt)` bị gán sai thành `FRUIT_SNACK`.
   - Bổ sung `đậu hà lan` vào `VEGETABLE_PATTERNS` và các loại đậu chín (`đậu nành`, `đậu đen`, `đậu đỏ`) vào `STAPLE_PATTERNS`.
   - Bổ sung `COOKED_STATE_PATTERNS` (`luộc`, `hấp`, `xào`, `nấu`, `kho`...) để bảo đảm các món đã chế biến không bao giờ bị rơi vào `RAW_INGREDIENT`.
   - Nhận diện nhóm thủy sản / thịt Việt Nam theo category để `Tép gạo` luôn là `MAIN_PROTEIN`.

5. **Siết chính sách cơ cấu bữa ăn (Slot Policy) cho menu 2-2-2-1:**
   - Khóa slot 0 của mọi bữa chính (`breakfast_0`, `lunch_0`, `dinner_0`) luôn là `STAPLE`.
   - `breakfast_1` chỉ nhận `{MAIN_PROTEIN, VEGETABLE}`, loại bỏ hoàn toàn `FRUIT_SNACK` và `BEVERAGE` khỏi bữa sáng chính.
   - Các slot tiếp theo của bữa trưa và tối chỉ nhận `{MAIN_PROTEIN, VEGETABLE, SOUP}`.
   - Bữa phụ (`snack_0`) dành riêng cho `{FRUIT_SNACK, BEVERAGE}`.

---

## 2. Chi Tiết Các Tệp Tin Đã Cập Nhật

| Tệp tin | Loại thay đổi | Chi tiết nội dung |
|:---|:---|:---|
| `src/models/dish_category.py` | Logic nghiệp vụ | Bổ sung `COOKED_STATE_PATTERNS`, `DAIRY_PATTERNS`, tinh chỉnh `SNACK_PATTERNS`, `VEGETABLE_PATTERNS`, `STAPLE_PATTERNS` và override thủy sản. |
| `src/models/food_selector.py` | Thuật toán selector | Siết `_roles_for_slot`: `breakfast_1` chuyển thành `{MAIN_PROTEIN, VEGETABLE}`, loại bỏ `FRUIT_SNACK`. |
| `tests/test_dish_role_c4.py` | Kiểm thử mới | Bổ sung 21 bài unit test kiểm tra phân loại vai trò món, chống misclassification và kiểm tra ngưỡng pool. |
| `tests/test_food_selector.py` | Kiểm thử | Đồng bộ kỳ vọng `breakfast_1` trong `test_real_database_slots_have_expected_roles`. |
| `tests/test_api_swap.py` | Kiểm thử | Cập nhật kiểm tra chống trùng món xuyên bữa (C6) tương thích với tổ hợp thực đơn tối ưu mới. |
| `app/static/index.html` | Cập nhật UI | Thay thẻ nhập bệnh lý bằng `<select id="medicalCondition">`; thêm cột `Thao tác` trong bảng thực đơn. |
| `app/static/js/api.js` | Mở rộng API | Cập nhật hàm `apiSwapMenu` hỗ trợ tham số `old_portions_g`. |
| `app/static/js/app.js` | Logic Frontend | Thêm `MEAL_LABELS` tiếng Việt; ẩn `food_id`; thêm handler `handleSwap()`; đồng bộ dropdown bệnh lý. |
| `app/static/css/styles.css` | Phong cách CSS | Thêm style hiện đại cho `.btn-swap` (dark glassmorphism, hover glow). |
| `tests/test_frontend_contract.py` | Kiểm thử hợp đồng | Thêm 4 bài test kiểm tra cấu trúc DOM, nhãn tiếng Việt, ràng buộc natri và biên độ delta đổi món. |

---

## 3. Kết Quả Kiểm Thử & Nghiệm Thu

1. **Phân loại vai trò món chuẩn xác (C4):**
   - `Cơm gạo lứt`, `Cơm kê`, `Cơm tẻ trắng`, `Khoai tây luộc`, `Khoai lang luộc` $\to$ `STAPLE`.
   - `Đậu hà lan luộc`, `Rau muống luộc`, `Măng tre luộc` $\to$ `VEGETABLE`.
   - `Tép gạo`, `Trứng vịt lộn luộc` $\to$ `MAIN_PROTEIN`.
   - `Sữa bò tươi`, `Sữa đậu nành`, `Mãng cầu xiêm`, `Cookies, oatmeal` $\to$ `FRUIT_SNACK`.
   - Không còn bất kỳ món chín nào bị rơi vào `RAW_INGREDIENT`.

2. **Cơ cấu bữa ăn & độ sâu ứng viên (Candidate Pools):**
   - Slot 0 bữa chính: 100% `STAPLE`.
   - Mọi slot trong menu 2-2-2-1 trên cả 3 profile chuẩn (P1, P2, P3) đều thỏa mãn `len(pool) >= MIN_ROLE_POOL_SIZE = 3`.
   - Demo P1 chạy mượt mà, đạt điểm fitness cao ($97.83$), 0 vi phạm ràng buộc dinh dưỡng và cấu trúc món.

3. **Toàn vẹn kiểm thử tự động:**
   - Kiểm thử C4 mới (`tests/test_dish_role_c4.py`): `21/21 PASSED`.
   - Kiểm thử hợp đồng frontend: `8/8 PASSED`.
   - Toàn bộ test suite hệ thống (`pytest tests/ -q`): `423/423 PASSED` (100% xanh, không lỗi hồi quy).
