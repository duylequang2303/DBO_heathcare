# Báo Cáo Thực Nghiệm Chẩn Đoán & Ablation: DBO vs IDBO

## 1. Mục Tiêu Thực Nghiệm

Thực nghiệm này được thiết kế để giải quyết dứt điểm câu hỏi khoa học cốt lõi:
**Vì sao DBO và IDBO cho kết quả hoàn toàn giống nhau trên bài toán tối ưu thực đơn 2 tầng?**

Cụ thể, chúng tôi kiểm tra:
1. Cơ chế ngẫu nhiên hóa của IDBO (`random_perturbation` và `random_restart`) có thực sự được kích hoạt trong quá trình chạy hay không?
2. Khi thay đổi cấu hình chẩn đoán (tăng số vòng lặp `max_iter`, giảm cửa sổ phát hiện trì trệ `stagnation_window`, tăng ngưỡng sụp đổ đa dạng `diversity_threshold`), cơ chế cải tiến có bắt đầu kích hoạt không?
3. Sự khác biệt giữa DBO và IDBO có ý nghĩa thống kê trên cùng hạt giống ngẫu nhiên (paired seeds 8001–8010) hay không?

## 2. Thiết Kế Đối Chuẩn Paired (3 Cấu Hình)

Thực nghiệm chạy trên Profile P1 (Duy, Nam 22 tuổi, 65kg, 170cm, TDEE=2491.6 kcal) với 10 seed độc lập (8001..8010):

| Cấu hình | Mục đích | Outer Max Iter | Inner Max Iter | Stagnation Window | Diversity Threshold |
|---|---|---|---|---|---|
| **A. baseline_short** | Cấu hình tuần 8 gốc | 25 | 25 | 25 | 0.001 (1e-3) |
| **B. diagnostic_balanced** | Chẩn đoán cân bằng | 100 | 25 | 10 | 0.01 |
| **C. diagnostic_activation** | Kiểm tra kích hoạt | 150 | 25 | 5 | 0.05 |

## 3. Kết Quả Tổng Hợp (Summary Statistics)

```
          config_name algorithm  runs  best_fitness  mean_fitness  median_fitness  std_fitness  worst_fitness  mean_runtime_s  total_outer_perturbations  mean_outer_perturbations  total_outer_restarts  mean_outer_restarts  total_final_inner_perturbations  total_final_inner_restarts  idbo_wins  idbo_ties  idbo_losses  mean_paired_difference
       baseline_short       dbo    10       99.5106       98.2148         98.5367       1.0663        96.3425           19.20                          0                       0.0                     0                  0.0                                0                           0          0         10            0                     0.0
       baseline_short      idbo    10       99.5106       98.2148         98.5367       1.0663        96.3425           19.60                          0                       0.0                     0                  0.0                                0                           0          0         10            0                     0.0
diagnostic_activation       dbo    10       99.6157       96.3323         97.7481       4.5525        84.0787           91.63                          0                       0.0                     0                  0.0                                0                           0          0         10            0                     0.0
diagnostic_activation      idbo    10       99.6157       96.3323         97.7481       4.5525        84.0787           91.77                          0                       0.0                     0                  0.0                                0                           0          0         10            0                     0.0
  diagnostic_balanced       dbo    10       99.6472       97.9821         97.9463       1.0948        96.3510           69.07                          0                       0.0                     0                  0.0                                0                           0          0         10            0                     0.0
  diagnostic_balanced      idbo    10       99.6472       97.9821         97.9463       1.0948        96.3510           70.63                          0                       0.0                     0                  0.0                                0                           0          0         10            0                     0.0
```

## 4. Phân Tích Khác Biệt Cặp Đôi (Paired Differences & Thống Kê)

> [!NOTE]
> **Kết quả kiểm định paired:** Không thể hiện khác biệt; mọi cặp seed (IDBO - DBO) đều có hiệu số $\Delta = 0.0000$.
> Do tất cả các cặp khác biệt đều bằng 0 tuyệt đối, việc ép chạy kiểm định Wilcoxon signed-rank là không cần thiết và vô nghĩa về mặt thống kê.

- **Số seed IDBO thắng:** 0/10
- **Số seed IDBO hòa DBO:** 10/10 (100%)
- **Số seed IDBO thua:** 0/10
- **Mean paired difference (IDBO - DBO):** 0.0000

## 5. Phân Tích Telemetry & Nguyên Nhân Cốt Lõi

Dữ liệu telemetry ghi nhận từ toàn bộ các lượt chạy xác nhận:
- `outer_perturbations`: **0** trên toàn bộ 3 cấu hình.
- `outer_restarts`: **0** trên toàn bộ 3 cấu hình.
- `final_inner_perturbations`: **0** trên toàn bộ 3 cấu hình.
- `final_inner_restarts`: **0** trên toàn bộ 3 cấu hình.

### Vì sao cơ chế cải tiến của IDBO hoàn toàn không kích hoạt?

1. **Bản chất tính toán của `population_diversity`:**
   Hàm đo độ phân tán quần thể được định nghĩa:
   $$\text{diversity}(X) = \frac{1}{D} \sum_{d=1}^D \frac{\sigma(X_{*, d})}{ub_d - lb_d}$$
   Đối với các cá thể được khởi tạo ngẫu nhiên đều trong $[lb, ub]$, độ lệch chuẩn lý thuyết là $\frac{1}{\sqrt{12}} \approx 0.2887$. Thực tế với kích thước quần thể $N=10$, giá trị này dao động trong khoảng $0.24 - 0.34$.

2. **Cơ chế Greedy Acceptance của DBO:**
   Trong DBO, một cá thể chỉ được cập nhật vị trí nếu vector đề xuất mới có fitness tốt hơn vị trí cũ (`improved = new_f < group_f`). Trên không gian tổ hợp rời rạc (tầng Outer ánh xạ $z \in [0, 1)$ sang món ăn qua hàm bậc thang), đa số các bước dịch chuyển không làm cải thiện nghiệm. Do đó, các cá thể không cải thiện **giữ nguyên vị trí ban đầu**, khiến độ lệch chuẩn của đàn luôn duy trì trên mức $0.24$.

3. **Ngưỡng sụp đổ quá nhỏ so với không gian bài toán:**
   Cả 3 cấu hình đặt ngưỡng `diversity_threshold` lần lượt là $0.001$, $0.01$, và $0.05$. Vì độ đa dạng thực tế của đàn không bao giờ giảm xuống dưới $0.20$, điều kiện kích hoạt `diversity < diversity_threshold` **luôn luôn False** trong suốt quá trình chạy.

4. **Cơ chế Stagnation Window không đủ điều kiện đơn lẻ:**
   Trong mã nguồn `src/algorithms/idbo.py`:
   ```python
   collapsed = diversity < self.diversity_threshold
   do_restart = (collapsed and self.restart_rate > 0.0 and self._stagnation >= self.stagnation_window)
   ```
   Cơ chế restart đòi hỏi ĐỒNG THỜI cả hai điều kiện: vừa phải trì trệ (`_stagnation >= stagnation_window`), vừa phải sụp đổ đa dạng (`collapsed = True`). Vì `collapsed` luôn False, `do_restart` không bao giờ được gọi.

5. **Hệ quả tất yếu:**
   Khi không có perturbation và không có restart nào được kích hoạt, IDBO tiêu thụ chuỗi số ngẫu nhiên hoàn toàn trùng khớp với DBO trên cùng seed, dẫn đến nghiệm, lịch sử hội tụ và chỉ số dinh dưỡng đầu ra giống nhau 100%.

## 6. Kết Luận Khoa Học Lựa Chọn

> [!IMPORTANT]
> ### KẾT LUẬN LỰA CHỌN: KẾT LUẬN C
> **Các cơ chế cải tiến của IDBO vẫn không kích hoạt ngay cả trong cấu hình chẩn đoán (0 perturbations, 0 restarts across all configs). Kết quả thực nghiệm chỉ ra rằng điều kiện kích hoạt liên quan đến ngưỡng sụp đổ đa dạng (`diversity_threshold`) chưa tương thích với đặc tính phân tán của bài toán rời rạc; do đó chưa thể dùng benchmark hiện tại để tuyên bố lợi thế của IDBO so với DBO.**

## 7. Khuyến Nghị Kỹ Thuật

1. **Minh bạch học thuật:** Trình bày trung thực trong báo cáo và slide tuần 8-9 rằng DBO và IDBO tương đương vì cơ chế cải tiến chưa kích hoạt trong phạm vi thử nghiệm.
2. **Cải tiến điều kiện kích hoạt cho IDBO:** Nếu muốn IDBO phát huy tác dụng trên bài toán tổ hợp thực đơn, cần tách rời điều kiện restart khỏi `diversity_threshold` (cho phép restart khi chỉ có trì trệ), hoặc chuẩn hóa độ đo đa dạng dựa trên khoảng cách Hamming/Jaccard giữa các tổ hợp món ăn thay vì khoảng cách Euclid trên vector liên tục $z$.