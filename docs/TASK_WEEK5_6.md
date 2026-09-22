# Phân Công Công Việc Tuần 5–6 — IDBO + Benchmark + Báo Cáo

Nhóm: Lê Quang Duy (trưởng nhóm) · Đặng Nguyễn Minh Đăng · Hồ Trung Cương

> Tuần 5 và tuần 6 **gộp một mốc**. Khung mã IDBO đã dựng sẵn. Việc còn lại của nhóm: **chạy thí nghiệm đúng protocol**, **vẽ biểu đồ**, **viết báo cáo Word**. Chưa đưa IDBO vào bài toán thực đơn (tuần 7).

## Mục tiêu (theo đề cương)

| Tuần | Nội dung đề cương | Việc nhóm làm |
| :--- | :--- | :--- |
| 5 | Cơ chế ngẫu nhiên cải tiến DBO (đa dạng quần thể, hạn chế hội tụ sớm) | Giải thích + đo diversity, perturbation |
| 6 | IDBO và đánh giá trên hàm benchmark cơ bản | So sánh DBO vs IDBO trên 6 hàm, viết báo cáo |

## Đã có sẵn (không làm lại)

Khung code tuần 5–6 đã nằm trên repo. **Không sửa** 4 hành vi DBO gốc (`behaviors.py`) và **không đổi** signature `optimize(objective, dim, lb, ub, seed)`.

| File | Việc gì |
| :--- | :--- |
| `src/algorithms/idbo.py` | IDBO: diversity, perturbation, restart |
| `src/algorithms/dbo.py` | Hook `_after_iteration` (DBO gốc vẫn no-op) |
| `tests/test_idbo.py` | Unit test cơ chế |
| `scripts/demo_week5_6.py` | Chạy 1 lần, in fitness / diversity |
| `scripts/experiment_idbo.py` | Pipeline so sánh, xuất CSV tóm tắt best_fitness |
| `docs/TASK_WEEK5_6.md` | File phân công này |

```bash
python -m pytest tests/
python scripts/demo_week5_6.py --function rastrigin --dim 10 --max-iter 200
```

Còn thiếu so với đề cương: **số liệu M=30 đầy đủ**, **biểu đồ hội tụ**, **báo cáo Word**. Ba thứ này giao bên dưới — không để “chạy benchmark” chung chung.

---

## Phân công (việc còn lại)

| Thành viên | Việc chính | Nộp gì |
| :--- | :--- | :--- |
| **Đặng Nguyễn Minh Đăng** | Thí nghiệm benchmark DBO vs IDBO (protocol chốt bên dưới) | CSV + 3 loại biểu đồ + bảng số liệu điền sẵn + mục 4–5 trong Word |
| **Hồ Trung Cương** | Lý thuyết IDBO + phân tích diversity / số lần perturb–restart | Mục 2–3 trong Word + 1 bảng thống kê perturb/restart |
| **Lê Quang Duy** | Gộp báo cáo Word, nhận xét, Git/review | File `docs/BaoCao_Tuan5_6.docx` hoàn chỉnh + merge |

---

## 1. Đăng — Benchmark (protocol bắt buộc, không tự đổi)

Đây là phần dễ bị mơ hồ. Làm **đúng** các mục dưới. Muốn đổi tham số phải báo nhóm trước.

### 1.1 Cấu hình cố định

| Tham số | Giá trị | Lý do |
| :--- | :--- | :--- |
| Thuật toán | `dbo` và `idbo` | So sánh công bằng với baseline tuần 4 |
| Hàm | đúng 6 hàm: `sphere`, `schwefel_2_22`, `rosenbrock`, `rastrigin`, `ackley`, `griewank` | Bộ tuần 4, không thêm hàm khác |
| `dim` | `2`, `10`, `30` | Đề cương: đánh giá theo số chiều |
| `n_agents` | `30` | Cùng tuần 4 |
| `max_iter` | `500` | Cùng tuần 4 |
| `M` (số lần chạy) | `30` | Mỗi (thuật toán, hàm, dim) = 30 seed khác nhau |
| Seed | **không tự bịa** — dùng seed do `scripts/experiment_idbo.py` sinh | Cùng seed thì DBO và IDBO so được |

Tổng số lần chạy: `2 × 6 × 3 × 30 = 1080`. Chạy overnight cũng được; không cắt `M` hay `max_iter` khi nộp bản chính.

Smoke test (không tính là kết quả nộp):

```bash
python scripts/experiment_idbo.py --runs 3 --dims 2 10 --max-iter 80 --functions sphere rastrigin
```

Bản chính:

```bash
python scripts/experiment_idbo.py --runs 30 --dims 2 10 30 --max-iter 500 --n-agents 30
```

CSV ra `experiments/week5_6/` (đã gitignore). **Không commit CSV/PNG.** Nộp qua Google Drive / đính kèm báo cáo.

### 1.2 Việc phải code thêm (Đăng)

`experiment_idbo.py` hiện **chỉ** ghi `best_fitness` cuối run. Đăng bổ sung, không phá cột CSV cũ:

1. Lưu **lịch sử hội tụ** mỗi run: file `experiments/week5_6/idbo_vs_dbo_history.csv`  
   Cột bắt buộc: `algorithm,function,dim,run,iteration,best_fitness`  
   `iteration` từ `0` đến `max_iter` (khớp `result.history`).
2. Với IDBO, lưu thêm `experiments/week5_6/idbo_diversity.csv`  
   Cột: `function,dim,run,iteration,diversity` (`iteration` từ `1` đến `max_iter`).
3. Thêm `matplotlib` vào `requirements.txt` (chỉ Đăng làm, commit cùng script vẽ).
4. Script vẽ `scripts/plot_week5_6.py` — chạy **sau** khi CSV đã có, không gắn plot vào vòng optimize.

Lệnh vẽ (Đăng tự wire trong script, nhưng **đủ 3 hình** dưới):

| Mã hình | Nội dung bắt buộc | File xuất |
| :--- | :--- | :--- |
| F1 | Hội tụ trung bình dim=10, trục Y log, 6 subplot (mỗi hàm), 2 đường DBO / IDBO | `experiments/week5_6/fig_convergence_dim10.png` |
| F2 | Boxplot `best_fitness` DBO vs IDBO, dim=10, 6 hàm | `experiments/week5_6/fig_boxplot_dim10.png` |
| F3 | Diversity trung bình IDBO dim=10: `sphere` (unimodal) và `rastrigin` (multimodal) trên cùng khung | `experiments/week5_6/fig_diversity_dim10.png` |

Trục / chú thích tiếng Việt hoặc English đều được, nhưng phải có legend `DBO` / `IDBO`, tên hàm, `dim=10`.

Nếu 1080 run × lưu full history quá nặng: được phép **chỉ lưu history cho dim=10** (6 hàm × 2 thuật toán × 30 run). Summary best/mean/std vẫn phải đủ **mọi dim**.

### 1.3 Bảng số liệu phải điền (copy vào Word)

Với **mỗi** `(hàm, dim)` điền đúng 8 số + cột thắng:

| Hàm | Dim | DBO best | DBO mean | DBO std | IDBO best | IDBO mean | IDBO std | Thắng (mean) |
| :--- | ---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| sphere | 2 | | | | | | | |
| sphere | 10 | | | | | | | |
| sphere | 30 | | | | | | | |
| schwefel_2_22 | 2 | | | | | | | |
| … đủ 6 hàm × 3 dim = 18 dòng | | | | | | | | |

Quy tắc cột **Thắng (mean)** — so sánh **fixed-iteration** (`max_iter` giống nhau), **không** phải equal-evaluation-budget. IDBO gọi thêm objective khi perturb/restart nên `n_evaluations` thường lớn hơn DBO.

- `IDBO` nếu `mean_IDBO < mean_DBO`
- `DBO` nếu ngược lại
- `hòa` nếu `|mean_IDBO - mean_DBO| / max(|mean_DBO|, 1e-30) < 0.01` (chênh < 1%)

Kèm bảng `n_evaluations` trung bình (lấy từ `idbo_vs_dbo_runs.csv` / summary) cho từng `(hàm, dim)`:

| Hàm | Dim | DBO mean n_evaluations | IDBO mean n_evaluations |
| :--- | ---: | :--- | :--- |
| sphere | 2 | | |
| … đủ 6 hàm × 3 dim | | | |

Không viết “IDBO tốt hơn” nếu bảng chưa có số. Không mô tả kết quả như so sánh cùng ngân sách đánh giá.

### 1.4 Câu hỏi Đăng phải trả lời trong Word (mục 5)

Trả lời **từng câu**, dựa trên bảng + hình, không chung chung:

1. Unimodal (`sphere`, `schwefel_2_22`, `rosenbrock`): IDBO có làm **xấu hơn** DBO không? Nếu có, ở dim nào?
2. Multimodal (`rastrigin`, `ackley`, `griewank`): IDBO thắng mean ở bao nhiêu / 9 ô (3 hàm × 3 dim)?
3. Dim 30 có còn hội tụ không, hay std nổ? Nêu 1 hàm tệ nhất.
4. Hình F3: diversity `rastrigin` có tụt xuống ngưỡng rồi nhích lại không (dấu hiệu restart/perturb)?
5. Thời gian: IDBO chậm hơn DBO khoảng bao nhiêu % (lấy cột `runtime_s` trung bình dim=10)?

### 1.5 Nghiệm thu Đăng

- [ ] Chạy đủ bản chính (hoặc giải thích nếu máy không kịp: tối thiểu **dim=10, M=30, đủ 6 hàm, cả DBO và IDBO**).
- [ ] Có 2 CSV summary/runs + history dim=10.
- [ ] Có đủ 3 file PNG F1, F2, F3.
- [ ] Bảng 18 dòng điền hết, không ô trống.
- [ ] 5 câu mục 1.4 có câu trả lời cụ thể (có số).

---

## 2. Cương — Lý thuyết IDBO + diversity (viết Word + 1 bảng)

Cương **không** viết lại `behaviors.py`. Đọc `src/algorithms/idbo.py` và viết cho người chưa đọc code hiểu được.

### 2.1 Mục 2–3 trong Word (Cương soạn)

**Mục 2 — Nhược điểm DBO gốc (khoảng 1–1.5 trang)**

- DBO hội tụ nhanh trên hàm đơn điệu nhưng dễ mất đa dạng.
- Nêu đúng 4 hành vi tuần 4 (tên + 1 câu mỗi loại). Không chép nguyên bài báo.
- Chốt: vì sao cần nhiễu / restart trước khi sang thực đơn (tuần 7).

**Mục 3 — Hai cơ chế IDBO (khoảng 2 trang)**

Viết **đúng** như code, không bịa công thức khác:

1. Diversity: trung bình `std` từng chiều, chia `(ub - lb)`. Ngưỡng mặc định `1e-3`.
2. Perturbation: Gauss trên agent không-elite; `scale_t = 0.1 * (1 - (t-1)/max_iter)`; `rate = 0.2`; elite `n_elite = 1` không bị đụng.
3. Restart: chỉ khi diversity thấp **và** best đứng `stagnation_window = 25` vòng; thay `25%` agent tệ nhất bằng mẫu đều trong `[lb, ub]`.
4. Một iteration: restart **hoặc** perturb, không cả hai.
5. Kèm 1 sơ đồ (vẽ Word / PowerPoint xuất ảnh): vòng DBO 4 hành vi → đo diversity → nhánh perturb/restart.

### 2.2 Bảng Cương phải tính từ CSV của Đăng

Khi Đăng có `idbo_vs_dbo_runs.csv`, Cương lọc `algorithm=idbo`, dim=10, tính trung bình `n_perturbations` và `n_restarts` theo hàm:

| Hàm | Mean n_perturbations (dim=10) | Mean n_restarts (dim=10) |
| :--- | :--- | :--- |
| sphere | | |
| schwefel_2_22 | | |
| rosenbrock | | |
| rastrigin | | |
| ackley | | |
| griewank | | |

Nhận xét 4–6 câu: hàm nào gần như không restart (quần thể chưa sụp) vs hàm nào restart nhiều.

### 2.3 Nghiệm thu Cương

- [ ] Mục 2 và mục 3 Word đủ ý trên, có sơ đồ.
- [ ] Bảng perturb/restart dim=10 đủ 6 hàm.
- [ ] Không tự ý đổi tham số mặc định trong `idbo.py` trừ khi nhóm đồng ý trên chat/MR.

---

## 3. Duy — Báo cáo Word tổng hợp + Git

### 3.1 File nộp

`docs/BaoCao_Tuan5_6.docx`

Bìa: tên đề tài, mã **CNTT-KLCN142**, 3 thành viên + MSSV, GVHD, mốc **Tuần 5–6**.

### 3.2 Mục lục bắt buộc (không thiếu mục)

| Mục | Người soạn nháp | Duy làm gì |
| :--- | :--- | :--- |
| 1. Mục tiêu tuần 5–6 và phạm vi (không đụng thực đơn) | Duy | Viết |
| 2. Nhược điểm DBO gốc | Cương | Biên tập |
| 3. IDBO: diversity, perturbation, restart | Cương | Biên tập, đối chiếu code |
| 4. Thiết kế thí nghiệm (lặp lại protocol 1.1, lệnh chạy) | Đăng | Kiểm tra đúng tham số |
| 5. Kết quả: bảng 18 dòng + hình F1 F2 F3 + 5 câu trả lời | Đăng | Kiểm tra số liệu vs CSV |
| 6. Thảo luận: IDBO phù hợp hàm nào; rủi ro khi sang tuần 7 | Duy (dựa Đăng + Cương) | Viết |
| 7. Kết luận và việc tuần 7 (fitness thực đơn) | Duy | Viết |
| Phụ lục: lệnh chạy, môi trường Python/NumPy, số test pytest | Duy | Viết |

Độ dài gợi ý: **8–12 trang** (kể hình), không nhồi screenshot IDE.

### 3.3 Mục 6 gợi ý (Duy)

- Unimodal: giữ chất lượng DBO (không được phá Sphere).
- Multimodal: IDBO có ích nếu bảng Đăng cho thấy mean giảm.
- Tuần 7: `objective` đổi sang `src/models/objective.py`; vector khẩu phần 25–350 g; chưa làm ở tuần này.

### 3.4 Git

```text
git checkout -b 260919-feat-week5-6-idbo-report      # Duy — Word + README
git checkout -b 260919-feat-week5-6-experiment-plots  # Đăng — history CSV + plot script
git checkout -b 260919-feat-week5-6-idbo-writeup      # Cương — nếu sửa docs/công thức
```

Trước merge: `python -m pytest tests/`. Không commit `experiments/week5_6/*.csv` hay `*.png`.

### 3.5 Nghiệm thu Duy

- [ ] Word đủ 7 mục + phụ lục.
- [ ] Số trong Word khớp CSV (spot-check ít nhất 3 ô).
- [ ] README có lệnh demo / experiment tuần 5–6 (đã có thì rà lại cho đúng protocol M=30).
- [ ] Test vẫn xanh.

---

## Hai cơ chế (tham chiếu nhanh — đừng viết khác trong báo cáo)

Cả hai chỉ chạy khi `diversity < 1e-3`. Elite (`n_elite = 1`) không bị sửa.

| Tham số | Mặc định | Ý nghĩa |
| :--- | :--- | :--- |
| `diversity_threshold` | `1e-3` | Ngưỡng sụp quần thể |
| `perturbation_rate` | `0.2` | Tỉ lệ agent bị nhiễu |
| `perturbation_scale` | `0.1` | Biên độ (theo span), giảm theo `t` |
| `stagnation_window` | `25` | Số vòng best đứng trước restart |
| `restart_rate` | `0.25` | Tỉ lệ agent tệ bị khởi tạo lại |
| `n_elite` | `1` | Cá thể giữ nguyên |

API không đổi so với DBO:

```python
optimize(objective, dim, lb, ub, seed=42) -> IDBOResult
```

---

## Đầu ra cuối tuần 5–6 (checklist nhóm)

- [x] Khung `idbo.py` + unit test trên repo.
- [ ] Bản chạy benchmark theo protocol mục 1 (Đăng).
- [ ] 3 hình F1 F2 F3 (Đăng).
- [ ] Bảng 18 dòng + 5 câu nhận xét (Đăng).
- [ ] Mục 2–3 Word + bảng perturb/restart (Cương).
- [ ] `docs/BaoCao_Tuan5_6.docx` đủ 7 mục (Duy gộp).

Tuần 7: gắn `objective` sang fitness thực đơn. Không làm trong mốc này.

## Quy ước

- Không đổi signature 4 hành vi tuần 4.
- Mọi ngẫu nhiên qua `np.random.Generator`.
- So sánh DBO vs IDBO cùng `n_agents`, `max_iter`, cùng công thức seed.
- CSV/PNG thí nghiệm không commit.

## Tài liệu tham khảo

1. J. Xue and B. Shen, "Dung beetle optimizer: a new meta-heuristic algorithm for global optimization," The Journal of Supercomputing, vol. 79, pp. 7305-7336, 2023.
2. IEEE CEC: Sphere, Rastrigin, Rosenbrock, Ackley, Griewank, Schwefel 2.22.
