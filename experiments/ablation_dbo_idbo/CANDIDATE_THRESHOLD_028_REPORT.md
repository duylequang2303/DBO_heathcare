# Báo Cáo Đánh Giá Ngưỡng Ứng Viên: diversity_threshold = 0.28

## 1. Thông Tin Chung & Provenance

- **Mục tiêu:** Kiểm tra thực nghiệm hành vi và hiệu quả của cơ chế cải tiến IDBO khi áp dụng ngưỡng ứng viên `diversity_threshold = 0.28` trên không gian thực đơn rời rạc.
- **Git Commit Hash:** `339051c5cc42203a415c234ac773658777ebf23c`
- **Nhánh:** `fix/integrated-menu-realism`
- **Tệp dữ liệu gốc:**
  - `candidate_threshold_028_eval.csv` (toàn bộ 20 lượt chạy paired DBO–IDBO)
  - `candidate_threshold_028_diffs.csv` (bảng đối chuẩn hiệu số từng seed)
  - `threshold_calibration_2seeds.csv` (dữ liệu rà soát ngưỡng 0.25, 0.28, 0.32)

---

## 2. Cấu Hình Thử Nghiệm Khóa (Locked Configuration)

Cả DBO và IDBO được chạy trên cùng điều kiện cấu hình:

| Tham số | Giá trị |
|---|---|
| Hồ sơ đánh giá | Profile P1 (Duy, Nam 22 tuổi, 65kg, 170cm, TDEE=2491.6 kcal) |
| Cấu trúc bữa ăn | 2+2+2+1 (Sáng: 2, Trưa: 2, Tối: 2, Phụ: 1) |
| Outer Solvers | DBO vs IDBO (10 agents, `outer_max_iter = 100`) |
| Inner Solvers | DBO vs IDBO (10 agents, `inner_max_iter = 25`) |
| `stagnation_window` | 10 vòng |
| `diversity_threshold` | **0.28** (chỉ định là **ngưỡng ứng viên**, chưa gọi là tối ưu) |
| `perturbation_rate` | 0.20 |
| `restart_rate` | 0.25 |
| Khẩu phần bounds | Dynamic role-based bounds theo từng vai trò ẩm thực |

---

## 3. Thiết Kế Đánh Giá Hai Tập Độc Lập

Để đảm bảo tính khách quan khoa học, 10 hạt giống (seeds) được phân tách rõ ràng:
1. **Tập hiệu chỉnh (Calibration set, N=2):** Seeds `8001`, `8002` — Dùng để thăm dò độ nhạy và chọn ra ngưỡng ứng viên 0.28.
2. **Tập đánh giá độc lập (Independent Evaluation set, N=8):** Seeds `8003`, `8004`, `8005`, `8006`, `8007`, `8008`, `8009`, `8010` — Giữ nguyên ngưỡng 0.28 và đánh giá mù (hold-out) mà không điều chỉnh tham số.

---

## 4. Bảng Kết Quả Đối Chuẩn Paired (All 10 Seeds)

| Seed | Phân loại | DBO Fitness | IDBO Fitness | Hiệu số (IDBO - DBO) | DBO Runtime (s) | IDBO Runtime (s) | DBO Evals | IDBO Evals | Collapse Events | Outer Pert | Outer Rest | Inner Pert Total | Inner Rest Total | Kết quả |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 8001 | Hiệu chỉnh | 97.6494 | 99.5489 | +1.8995 | 34.69 | 54.16 | 263.870 | 289.470 | 11 | 9 | 2 | 14.722 | 85 | IDBO_WIN |
| 8002 | Hiệu chỉnh | 99.4758 | 99.1439 | -0.3319 | 35.26 | 54.09 | 263.870 | 289.434 | 0 | 0 | 0 | 14.621 | 86 | DBO_WIN |
| 8003 | Độc lập | 99.0691 | 97.9416 | -1.1275 | 52.36 | 57.28 | 263.870 | 288.766 | 31 | 28 | 3 | 14.733 | 88 | DBO_WIN |
| 8004 | Độc lập | 97.2465 | 99.1396 | +1.8931 | 48.80 | 57.57 | 263.870 | 288.948 | 4 | 4 | 0 | 14.542 | 92 | IDBO_WIN |
| 8005 | Độc lập | 99.1117 | 99.7556 | +0.6439 | 53.79 | 65.07 | 263.870 | 289.924 | 76 | 69 | 7 | 14.869 | 89 | IDBO_WIN |
| 8006 | Độc lập | 99.3151 | 98.9199 | -0.3952 | 53.68 | 58.54 | 263.870 | 289.704 | 49 | 44 | 5 | 14.789 | 90 | DBO_WIN |
| 8007 | Độc lập | 99.5862 | 99.6609 | +0.0747 | 55.81 | 64.73 | 263.870 | 294.404 | 0 | 0 | 0 | 15.183 | 71 | IDBO_WIN |
| 8008 | Độc lập | 99.4844 | 98.4347 | -1.0497 | 54.45 | 56.97 | 263.870 | 293.826 | 0 | 0 | 0 | 14.878 | 94 | DBO_WIN |
| 8009 | Độc lập | 98.5132 | 99.6530 | +1.1398 | 37.58 | 54.09 | 263.870 | 291.682 | 64 | 58 | 6 | 15.011 | 91 | IDBO_WIN |
| 8010 | Độc lập | 99.6185 | 99.7668 | +0.1483 | 38.62 | 38.65 | 263.870 | 292.838 | 35 | 33 | 2 | 15.017 | 78 | IDBO_WIN |

---

## 5. Tổng Hợp Thống Kê Trên Tập Đánh Giá Độc Lập (Seeds 8003–8010, N=8)

- **Số cặp Thắng / Hòa / Thua:** 5 Thắng / 0 Hòa / 3 Thua cho IDBO.
- **Chênh lệch Fitness trung bình (Mean Paired Diff):** `+0.1659` điểm.
- **Chênh lệch Fitness trung vị (Median Paired Diff):** `+0.1115` điểm.
- **Thời gian thực thi trung bình:**
  - DBO: `49.39` giây (làm tròn `49.4s`).
  - IDBO: `56.61` giây (làm tròn `56.6s`).
  - Thời gian tăng thêm: `+7.22` giây (**`+14.6%`**).
- **Số lần đánh giá hàm mục tiêu (Evaluations):**
  - DBO: Cố định `263.870` lần đánh giá trên mọi seed.
  - IDBO: Trung bình `291.262` lần đánh giá (tăng thêm khoảng `+27.392` lượt đánh giá, tương đương `+10.4%` do các cú hích perturbation/restart).
- **Kiểm định thống kê:**
  - Wilcoxon signed-rank test: $p = 0.640625$ ($> 0.05$).
  - Sign test: $p = 0.7265625$ ($> 0.05$).
  $\rightarrow$ **Kết luận thống kê:** Khác biệt chưa đạt mức ý nghĩa thống kê ở ngưỡng $\alpha = 0.05$.
- **Ràng buộc kỹ thuật:** Cả DBO và IDBO đều ghi nhận **0 vi phạm** trong bộ ràng buộc kỹ thuật của thử nghiệm.

---

## 6. Phân Tích Hiện Tượng Kỹ Thuật: Hạt Giống 8007 & 8008

Ở hai hạt giống 8007 và 8008, tầng ngoài không ghi nhận sự kiện suy giảm độ đa dạng nào (`outer_pert = 0, outer_rest = 0`), tuy nhiên kết quả nghiệm của DBO và IDBO vẫn có sự chênh lệch (+0.0747 và -1.0497).

**Nguyên nhân xác định:**
- Tham số `diversity_threshold = 0.28` được áp dụng chung cho cả hai tầng.
- Tầng trong (Inner solver — tối ưu khẩu phần gram liên tục) vẫn ghi nhận sự kiện suy giảm độ đa dạng và kích hoạt khoảng 15.000 lần perturbation cùng 70–94 lần restart.
- Sự can thiệp ở tầng trong làm dịch chuyển nhẹ giá trị gram tối ưu trả về cho tầng ngoài, dẫn đến điểm fitness cuối cùng có khác biệt.
- Hiện tượng này chứng minh sự khác biệt xuất phát từ hoạt động nội tại của tầng trong, không phải do rò rỉ RNG hay sai lệch thứ tự gọi hàm.

---

## 7. Kết Luận Khoa Học Chuẩn Hóa

1. **Về hành vi tìm kiếm:** IDBO đã tạo ra hành vi tìm kiếm khác biệt thực tế so với DBO thông qua các sự kiện suy giảm độ đa dạng, xáo trộn (perturbation) và khởi động lại (restart).
2. **Về ngưỡng ứng viên:** Ngưỡng `0.28` được xác định là một **ngưỡng ứng viên khả thi**, tạo mức can thiệp vừa phải hơn so với ngưỡng `0.32` (vốn can thiệp quá dồn dập ở ~82% số vòng).
3. **Về xu hướng hiệu năng:** Trên tập đánh giá độc lập 8 hạt giống, IDBO thắng 5/8 lượt và có xu hướng cải thiện nhẹ (trung bình +0.1659 điểm), đổi lại thời gian thực thi tăng khoảng 14.6%.
4. **Về ý nghĩa thống kê:** Do cỡ mẫu hiện tại nhỏ ($N=8$) và các kiểm định thống kê đều có $p > 0.05$, **chưa đủ bằng chứng để khẳng định IDBO tốt hơn DBO một cách ổn định**.
5. **Hướng tiếp theo:** Giữ nguyên kết quả này làm bằng chứng chẩn đoán; chuyển trọng tâm sang hoàn thiện và ổn định hệ thống Web ở Tuần 10. Các benchmark đối chuẩn cùng ngân sách đánh giá (budget-matched) sẽ được thực hiện ở vòng đánh giá cuối cùng nếu cần thiết.
