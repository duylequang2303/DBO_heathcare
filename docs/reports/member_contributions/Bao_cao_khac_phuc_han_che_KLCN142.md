# BÁO CÁO HOÀN THÀNH KẾ HOẠCH KHẮC PHỤC HẠN CHẾ KHÓA LUẬN KLCN142

- **Người thực hiện**: Đăng (Phan Đăng Tuấn) / Nhóm đề tài KLCN142
- **Nhánh Git**: `fix/remediation-limitations` (phát triển từ `fix/c4-c6-takeover`)
- **Tài liệu nguồn**: `Ke_hoach_khac_phuc_han_che_KLCN142.docx`
- **Thời gian thực hiện**: Khung thời gian khẩn cấp trước hạn chót bảo vệ
- **Trạng thái kiểm thử**: **439/439 tests PASS (100%)**

---

## I. TỔNG HỢP CÁC NỘI DUNG ĐÃ KHẮC PHỤC

### 1. Mã nguồn & Nghiệp vụ An toàn Thực đơn

| Hạn chế từ nhận xét | Nguyên nhân kỹ thuật | Giải pháp đã triển khai | File sửa đổi & Test |
| :--- | :--- | :--- | :--- |
| **Món không thích khớp chuỗi con** | Code cũ dùng `token.lower() in name`, gây false-positive (ghét *"cá"* bị loại luôn *"cà chua"*, *"rau cải"*; ghét *"bò"* dính *"quả bơ"*). | Chuyển sang so khớp theo **ranh giới từ (word boundary regex)** `(?<!\w){token}(?!\w)` kết hợp taxonomy dị ứng/món ăn. | [`src/models/allergen_rules.py`](file:///c:/dain.zip/DBO_heathcare/src/models/allergen_rules.py), [`src/models/constraints.py`](file:///c:/dain.zip/DBO_heathcare/src/models/constraints.py), [`src/models/objective.py`](file:///c:/dain.zip/DBO_heathcare/src/models/objective.py), [`src/models/food_sampler.py`](file:///c:/dain.zip/DBO_heathcare/src/models/food_sampler.py). Tests: `tests/test_safe_allergen_matching.py`. |
| **Thiếu cảnh báo Gout / Suy thận** | Hệ thống chỉ mới có cảnh báo tiểu đường & tăng huyết áp, thiếu cảnh báo lâm sàng cho bệnh nhân Gout và Thận. | Bổ sung chuẩn hóa alias (`_MEDICAL_ALIASES`) và phát cảnh báo y tế rõ ràng về kiểm soát purin (Gout) và protein/điện giải (Thận) trong `menu_notices`. | [`app/api/services.py`](file:///c:/dain.zip/DBO_heathcare/app/api/services.py). Tests: `tests/test_api_profile.py`, `tests/test_remediation_fixes.py`. |
| **Seed tầng trong phụ thuộc thứ tự gọi** | `inner_seed` tăng dần theo biến đếm `eval_call_idx` của outer solver, khiến cùng 1 tập món nếu duyệt khác thứ tự sẽ cho khẩu phần khác. | Chuyển sang tính seed tầng trong dựa trên **SHA-256 hash của tập `food_ids`**, đảm bảo tính tất định (deterministic) 100%. | [`src/algorithms/two_tier_solver.py`](file:///c:/dain.zip/DBO_heathcare/src/algorithms/two_tier_solver.py). Tests: `tests/test_remediation_fixes.py`. |
| **Restart không kích hoạt & Ngưỡng dùng chung** | `stagnation_window = 25` quá lớn so với số vòng lặp thực tế (10–15 iter), khiến `stagnation` không bao giờ chạm ngưỡng. | Tách riêng `outer_stagnation_window` và `inner_stagnation_window` linh hoạt trong `TwoTierConfig`, hỗ trợ kích hoạt restart khi quần thể suy giảm đa dạng. | [`src/algorithms/two_tier_solver.py`](file:///c:/dain.zip/DBO_heathcare/src/algorithms/two_tier_solver.py). Tests: `tests/test_remediation_fixes.py`. |
| **Thống nhất chỉ số best / final** | Cần phân định minh bạch fitness liên tục và fitness sau làm tròn thực tế. | Bổ sung `rounded_portions_g` và `rounded_fitness` (sau khi làm tròn 5g và validate) vào `TwoTierResult`. | [`src/algorithms/two_tier_solver.py`](file:///c:/dain.zip/DBO_heathcare/src/algorithms/two_tier_solver.py). |

---

### 2. Thực nghiệm Đối chuẩn & Kiểm định Thống kê

- Đã xây dựng và thực thi kịch bản benchmark độc lập: [`scripts/run_remediation_benchmark.py`](file:///c:/dain.zip/DBO_heathcare/scripts/run_remediation_benchmark.py).
- Đối chuẩn Paired có đối chứng:
  1. **Random Search Baseline** (cùng số lần đánh giá hàm mục tiêu - matched budget).
  2. **DBO Chuẩn**.
  3. **IDBO Cải tiến** (với cơ chế restart và perturbation kích hoạt).
- Thực hiện trên 3 hồ sơ bệnh lý P1, P2, P3 và tập paired seeds chuẩn.
- Kiểm định Wilcoxon signed-rank test và khoảng tin cậy Bootstrap 95% CI cho chênh lệch điểm fitness.
- Toàn bộ kết quả và file khóa cấu hình được lưu tại: [`experiments/remediation_benchmark/`](file:///c:/dain.zip/DBO_heathcare/experiments/remediation_benchmark/).

---

### 3. Tài liệu hóa Mục Hạn chế của Khóa luận

Đã soạn thảo văn bản hoàn chỉnh 7 điểm hạn chế và 4 hướng phát triển tại:
👉 [`docs/reports/HAN_CHE_VA_HUONG_PHAT_TRIEN_KLCN142.md`](file:///c:/dain.zip/DBO_heathcare/docs/reports/HAN_CHE_VA_HUONG_PHAT_TRIEN_KLCN142.md)
để sinh viên đưa thẳng vào Chương 5 (Đánh giá kết quả & Hạn chế đề tài) của Báo cáo và Slide thuyết trình.

