# Báo cáo Thực nghiệm Đối chuẩn Khắc phục Hạn chế KLCN142

- **Ngày thực hiện**: 2026-11-08 20:58:42
- **Mục tiêu**: Đối chuẩn công bằng Paired runs giữa **DBO**, **IDBO**, và **Random Search Baseline** trên cùng ngân sách đánh giá.
- **Hồ sơ đánh giá**: P1 (Duy trì - Nam trẻ), P2 (Tiểu đường mô phỏng), P3 (Tăng huyết áp mô phỏng).
- **Số lượt chạy**: 15 paired runs (3 hồ sơ x 5 seed).

---

## 1. Bảng Tổng hợp Hiệu Năng

| Thuật toán | Fitness Liên tục (Mean ± Std) | Fitness Làm tròn 5g (Mean ± Std) | Median | Min - Max | Thời gian (s) | Evals TB | Restarts (Outer / Inner) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Search** | 83.32 ± 17.21 | 82.27 ± 17.65 | 86.06 | [49.72, 98.93] | 34.65s | 30625 | 0 / 0 |
| **DBO** | 97.24 ± 4.04 | 96.41 ± 7.06 | 98.53 | [71.19, 99.43] | 28.97s | 25920 | 0 / 0 |
| **IDBO** | 95.32 ± 6.38 | 95.21 ± 6.36 | 98.05 | [82.48, 99.51] | 33.09s | 30755 | 2.5 / 0.8 |

---

## 2. Kiểm định Thống kê & Phân tích Paired

1. **DBO vs Random Search Baseline**:
   - Chênh lệch điểm fitness trung bình: **+14.13 điểm** (DBO vượt trội rõ rệt so với tìm kiếm ngẫu nhiên).
   - Kiểm định Wilcoxon: p-value = **2.6245e-03** (p < 0.05, có ý nghĩa thống kê cao).
   - **Kết luận**: Chứng minh thuật toán metaheuristic thực sự tìm kiếm và hội tụ hiệu quả, không phải ngẫu nhiên.

2. **IDBO vs DBO (Paired)**:
   - Chênh lệch điểm fitness trung bình (IDBO - DBO): **-1.1987 điểm**.
   - Khoảng tin cậy Bootstrap 95% CI: **[-4.4767, +1.6832]**.
   - Tỷ lệ Thắng / Hòa / Thua: **4 Thắng / 0 Hòa / 11 Thua**.
   - Kiểm định Wilcoxon signed-rank: W-stat = **42.0**, p-value = **0.3303**.
   - **Kích hoạt Telemetry**: IDBO ghi nhận trung bình **2.5 restarts tầng ngoài** và **0.8 restarts tầng trong**.
   - **Kết luận Trung thực**: Trong cấu hình thử nghiệm hiện tại, các cơ chế cải tiến của IDBO (random restart và perturbation) đã kích hoạt đúng thiết kế khi phát hiện quần thể suy giảm đa dạng; tuy nhiên chất lượng thực đơn cuối cùng tương đương DBO (chưa ghi nhận sự vượt trội có ý nghĩa thống kê của IDBO so với DBO).
