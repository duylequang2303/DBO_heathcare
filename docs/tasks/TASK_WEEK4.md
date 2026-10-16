# Phân Công Công Việc Tuần 4 — DBO Gốc Trên Hàm Benchmark

Nhóm: Lê Quang Duy (trưởng nhóm) · Đặng Nguyễn Minh Đăng · Hồ Trung Cương

## Mục tiêu tuần 4 (theo đề cương)
Nghiên cứu, cài đặt và kiểm thử **Dung Beetle Optimizer (DBO) gốc** (Xue & Shen, 2023). Tuần này DBO chạy trên **hàm benchmark chuẩn** để xác minh cài đặt đúng thuật toán (hội tụ về điểm tối ưu đã biết, sai lệch nhỏ) trước khi sang tuần 5–6 (cơ chế ngẫu nhiên cải tiến và IDBO).

> Ranh giới phạm vi: tuần 4 **chưa** đưa DBO vào bài toán thực đơn. Fitness thực đơn sẽ ghép vào từ tuần 7. Tuần 4 chỉ test trên hàm benchmark liên tục (Sphere, Rastrigin, Rosenbrock, Ackley, Griewank, Schwefel 2.22).

## Trạng thái đầu tuần
- Tuần 3: `src/models/*`, `src/utils/*` hoàn thiện; 28 test xanh (`python3 -m pytest tests/`).
- Một số đầu ra tuần 3 (test của Đăng/Cương, các nhánh chưa merge) có thể còn mở — nhóm rà `git status`, `git log` và **đóng dứt điểm trước khi nhận việc tuần 4**.
- `src/algorithms/` chưa tồn tại; trưởng nhóm dựng khung trước.

## Kiến trúc khung

```text
src/
├── algorithms/
│   ├── __init__.py
│   ├── dbo.py            # DBO gốc: khởi tạo quần thể, vòng lặp chính, chọn lọc (Duy)
│   ├── behaviors.py      # 4 hành vi DBO: ball-rolling, reproduction, foraging, thieving (Cương)
│   └── benchmarks.py     # Bộ hàm benchmark chuẩn + optimum/toạ độ đã biết (Đăng)
scripts/
│   ├── demo_week4.py     # Demo: chạy DBO 1 lần trên 1 hàm, in kết quả
│   └── experiment_dbo.py # Thí nghiệm: M lần lặp độc lập -> thống kê best/mean/std, xuất CSV
tests/
│   ├── test_dbo.py       # Kiểm thử tính đúng của DBO
│   └── test_benchmarks.py# Kiểm thử giá trị hàm benchmark tại optimum đã biết
experiments/week4/        # CSV + biểu đồ hội tụ (gitignore, không commit dữ liệu lớn)
```

DBO được tách **thuật toán ↔ bài toán**: thuật toán chỉ nhận một callable
`objective(x: np.ndarray) -> float` cùng `dim`, `lb`, `ub`, không biết gì về nguồn gốc hàm mục tiêu.
Nhờ vậy tuần 7 chỉ cần đổi callable sang fitness thực đơn mà không sửa khung DBO.

## Phân công

| Thành viên | Mô-đun | File | Nội dung chính |
| :--- | :--- | :--- | :--- |
| Lê Quang Duy (trưởng) | Khung DBO & tích hợp | `src/algorithms/dbo.py`, `tests/test_dbo.py` | Vòng lặp chính, khởi tạo quần thể, ghép 4 hành vi, lưu lịch sử hội tụ, review + merge |
| Hồ Trung Cương | 4 hành vi DBO | `src/algorithms/behaviors.py` | Ball-rolling, reproduction, foraging, thieving theo đúng công thức bài báo |
| Đặng Nguyễn Minh Đăng | Benchmark & thí nghiệm | `src/algorithms/benchmarks.py`, `tests/test_benchmarks.py`, `scripts/experiment_dbo.py` | Hàm benchmark, thống kê hội tụ M lần chạy, biểu đồ + CSV |

Ghi chú:
- `dbo.py` thuộc quyền Duy nhưng 4 hành vi trong `behaviors.py` thuộc Cương; **hợp đồng hàm** (signature) chốt tại mục **Hướng dẫn chung** bên dưới, không tự ý đổi.
- Đăng cần bộ benchmark sớm để Cương/Duy test hành vi; làm theo thứ tự: khung (Duy) → benchmark (Đăng) → behaviors (Cương) → tích hợp + thí nghiệm.

## Checklist từng thành viên (kèm tiêu chí nghiệm thu)

### 1. Duy — Khung DBO & tích hợp
- [x] Tạo package `src/algorithms/` với `__init__.py`.
- [x] Định nghĩa `DBOResult` (dataclass): `best_x`, `best_fitness`, `history` (list fitness tốt nhất theo iteration), `n_evaluations`, `runtime_s`, `seed`.
- [x] Viết lớp `DBO` với API `optimize(objective, dim, lb, ub, seed=42) -> DBOResult`.
- [x] Khởi tạo quần thể `n_agents` ngẫu nhiên đều trong `[lb, ub]` theo seed; đánh giá fitness ban đầu.
- [x] Vòng lặp chính `max_iter`: lần lượt gọi 4 nhóm hành vi (tỉ lệ quần thể mỗi nhóm theo bài báo), cập nhật `best` toàn cục, ghi `history`.
- [x] Chặn biên (`clip`) nghiệm sau mỗi hành vi về `[lb, ub]`.
- [x] Viết `tests/test_dbo.py`: (a) chạy seed cố định cho kết quả lặp lại được; (b) `best_fitness` không tăng (history không thoái lui); (c) `best_x` nằm trong biên; (d) hội tụ Sphere 10D dưới `1e-4`.

**Nghiệm thu:** `optimize()` chạy đủ `max_iter`, trả về `DBOResult` đầy đủ; test (a)–(d) xanh; chạy lại cùng seed ra cùng kết quả.

#### Hướng dẫn cho Duy (hợp đồng hàm — chốt trước khi Cương/Đăng code)
```python
# behaviors.py — mỗi hàm nhận vị trí hiện tại, trả về vị trí mới (không sửa in-place)
def ball_rolling(X, f, best, rng, **cfg) -> np.ndarray
def reproduction(X, best, lb, ub, t, max_iter, rng, **cfg) -> np.ndarray
def foraging(X, best, lb, ub, t, max_iter, rng, **cfg) -> np.ndarray
def thieving(X, best, rng, **cfg) -> np.ndarray
```
- `X`: `(n_agents, dim)` vị trí hiện tại của nhóm; `best`: vị trí tốt nhất toàn cục (`(dim,)`).
- `cfg`: tham số đọc từ bài báo (λ, S, k, b, α...) — Cương đặt giá trị mặc định theo Xue & Shen (2023), mở để chỉnh.
- `dbo.py` tự `clip` kết quả về `[lb, ub]`; behaviors **không** cần chặn biên.

### 2. Cương — 4 hành vi DBO
- [x] Đọc kỹ bài báo Xue & Shen (2023) mục 3 (DBO): công thức 4 hành vi + ý nghĩa tham số.
- [x] Cài **ball-rolling**: cuộn phân không vật cản (hệ số lệch α, k, b) và nhảy múa khi gặp vật cản (dùng `tan(θ)`, `θ ~ U(0, π)`).
- [x] Cài **reproduction**: vùng đẻ trứng co dần quanh best hiện tại, sinh cá thể con.
- [x] Cài **foraging**: vùng tìm kiếm co dần quanh best cục bộ, bọ nhỏ đi kiếm ăn.
- [x] Cài **thieving**: bọ trộm bám quanh best toàn cục (hệ số S, phân phối Gaussian).
- [x] Mỗi hành vi nhận `rng` (numpy `Generator`) để tái lập ngẫu nhiên.
- [x] Ghi chú ngắn cuối file: dòng công thức gốc trong bài báo tương ứng từng hành vi.

**Nghiệm thu:** 4 hàm đủ signature đã chốt; kết quả nhất quán khi dùng cùng `rng`/`seed`; giá trị đầu ra nằm trong khoảng hợp lý khi test đơn lẻ bằng snippet trong `scripts/demo_week4.py`.

#### Hướng dẫn cho Cương
- Bám **đúng tham số gốc** của bài báo cho bản DBO chuẩn (đây là baseline để tuần 6 so sánh IDBO vs DBO). Ghi nguồn tham số vào comment.
- Tỉ lệ quần thể chia 4 nhóm hành vi là hằng số cấu hình của `DBO`, không nằm trong `behaviors.py`.
- Không dùng vòng lặp Python cho vector quần thể; vector hoá bằng NumPy.
- Tham khảo benchmark cần số chiều cố định — đọc từ `X.shape[1]`, không hardcode.

### 3. Đăng — Benchmark & thí nghiệm
- [x] Cài `src/algorithms/benchmarks.py` với ít nhất 6 hàm: **Sphere, Rastrigin, Rosenbrock, Ackley, Griewank, Schwefel 2.22**.
- [x] Mỗi hàm: công thức, khoảng biên `(lb, ub)` chuẩn, `optimum` toạ độ + giá trị đã biết (thường là 0 tại 0; Rosenbrock = 0 tại (1,...,1)).
- [x] Viết `tests/test_benchmarks.py`: giá trị tại optimum sai khác ≤ `1e-8`; so khớp công thức cho `dim = 2`.
- [x] Viết `scripts/experiment_dbo.py`: với mỗi hàm × mỗi dim (2, 10, 30) chạy `M = 30` lần (seed khác nhau), thu thập `best_fitness`, ghi CSV cột `function, dim, run, best_fitness, iterations`.
- [x] Tính thống kê: `best / mean / std / worst` theo từng (hàm, dim); xuất bảng kết quả ra console + CSV tóm tắt.
- [ ] **Bắt buộc (Đăng):** Vẽ biểu đồ hội tụ + boxplot cho báo cáo Word — xem mục **Việc còn lại** bên dưới.

**Nghiệm thu code:** 6 hàm benchmark test xanh tại optimum đã biết; script thí nghiệm chạy trọn không lỗi, sinh CSV hợp lệ; DBO cải thiện rõ rệt so với khởi tạo ngẫu nhiên trên Sphere (sai số giảm ≥ 1e3 lần) và bám gần optimum đã biết trên các hàm còn lại ở dim thấp.

**Nghiệm thu báo cáo (chưa xong):** có CSV M=30, có PNG, có `docs/BaoCao_Tuan4.docx`.

## Đầu ra cuối tuần 4
- [x] Khung `src/algorithms/` + DBO gốc hoàn chỉnh, test xanh (`python3 -m pytest tests/`).
- [x] 6 hàm benchmark + test xanh.
- [x] Pipeline thí nghiệm `scripts/experiment_dbo.py` (M lần, dim 2/10/30, CSV `experiments/week4/`; file CSV gitignore).
- [x] `scripts/demo_week4.py`: chạy DBO 1 lần trên 1 hàm, in `best_x`, `best_fitness`, lịch sử hội tụ.
- [x] Cập nhật README: mô tả mô-đun DBO tuần 4 và tài liệu tham khảo.
- [x] Baseline DBO dùng cho tuần 5–6: test 111 passed; Sphere 10D `best_fitness = 1.47e-204`. Chi tiết tiếp theo: `docs/TASK_WEEK5_6.md`.
- [ ] **Chưa có:** số liệu thí nghiệm M=30 đầy đủ, hình PNG, báo cáo Word tuần 4. Giao **Đăng + Cương** ở mục dưới.

## Việc còn lại tuần 4 — báo cáo Word + hình (giao Cương + Đăng)

> Code DBO / 6 hàm benchmark / `experiment_dbo.py` **đã xong**. Còn thiếu đúng thứ cần để bảo vệ: **số liệu M=30**, **biểu đồ**, **file Word**. Không có hình thì không nộp báo cáo tuần 4.

Hiện trạng repo (2026-09-22):

| Hạng mục | Có chưa |
| :--- | :--- |
| `src/algorithms/benchmarks.py` + test | Có |
| `scripts/experiment_dbo.py` (pipeline CSV) | Có |
| `scripts/demo_week4.py` (1 lần Sphere 10D) | Có — chỉ 1 run, không đủ |
| CSV `experiments/week4/` (M=30, 6 hàm × 3 dim) | **Không** (gitignore, chưa nộp) |
| PNG hội tụ / boxplot | **Không** |
| `docs/BaoCao_Tuan4.docx` | **Không** |
| `matplotlib` trong `requirements.txt` | **Không** |

### Phân công còn lại

| Thành viên | Việc | Nộp gì |
| :--- | :--- | :--- |
| **Đặng Nguyễn Minh Đăng** | Chạy thí nghiệm + vẽ hình | CSV + 2 PNG + bảng 18 dòng điền số |
| **Hồ Trung Cương** | Viết báo cáo Word tuần 4 (lý thuyết DBO + dán hình/bảng của Đăng) | `docs/BaoCao_Tuan4.docx` |

Không đụng `behaviors.py` / `dbo.py` trừ khi phát hiện bug khi chạy.

---

### 1. Đăng — thí nghiệm + hình (bắt buộc)

#### 1.1 Chạy bản chính

Cấu hình **không tự đổi** (khớp tuần 5–6 để so được):

| Tham số | Giá trị |
| :--- | :--- |
| Thuật toán | `dbo` |
| Hàm | `sphere`, `schwefel_2_22`, `rosenbrock`, `rastrigin`, `ackley`, `griewank` |
| `dim` | `2`, `10`, `30` |
| `n_agents` | `30` |
| `max_iter` | `500` |
| `M` | `30` |

```bash
python scripts/experiment_dbo.py --runs 30 --dims 2 10 30 --max-iter 500 --n-agents 30
```

CSV ra `experiments/week4/` (gitignore). **Không commit CSV/PNG.** Nộp Drive / đính Word.

Nếu 6×3×30 quá nặng: tối thiểu **dim=10, M=30, đủ 6 hàm**. Summary mọi dim vẫn phải có nếu máy kịp.

#### 1.2 Code thêm (Đăng)

`experiment_dbo.py` hiện chỉ ghi `best_fitness` cuối run. Bổ sung, **không phá cột CSV cũ**:

1. Lưu lịch sử hội tụ dim=10: `experiments/week4/dbo_history_dim10.csv`  
   Cột: `function,dim,run,iteration,best_fitness` (`iteration` từ `0` đến `max_iter`).
2. Thêm `matplotlib` vào `requirements.txt`.
3. Script `scripts/plot_week4.py` — chạy **sau** khi CSV có, không gắn plot vào vòng optimize.

| Mã hình | Nội dung bắt buộc | File xuất |
| :--- | :--- | :--- |
| W4-F1 | Hội tụ trung bình dim=10, trục Y log, 6 subplot (mỗi hàm), 1 đường DBO | `experiments/week4/fig_convergence_dim10.png` |
| W4-F2 | Boxplot `best_fitness` dim=10, 6 hàm | `experiments/week4/fig_boxplot_dim10.png` |

Legend, tên hàm, `dim=10`. Trục tiếng Việt hoặc English đều được.

#### 1.3 Bảng số liệu (copy vào Word — Cương dán)

Với **mỗi** `(hàm, dim)` điền 4 số:

| Hàm | Dim | best | mean | std | worst |
| :--- | ---: | :--- | :--- | :--- | :--- |
| sphere | 2 | | | | |
| sphere | 10 | | | | |
| sphere | 30 | | | | |
| … đủ 6 hàm × 3 dim = 18 dòng | | | | | |

#### 1.4 Nghiệm thu Đăng

- [ ] CSV runs + summary (tối thiểu dim=10, M=30, 6 hàm).
- [ ] History dim=10.
- [ ] Đủ 2 PNG W4-F1, W4-F2.
- [ ] Bảng 18 dòng điền hết (hoặc 6 dòng dim=10 nếu máy không kịp 2/30).

---

### 2. Cương — báo cáo Word tuần 4

File: `docs/BaoCao_Tuan4.docx`

Bìa: tên đề tài, mã **CNTT-KLCN142**, 3 thành viên + MSSV, GVHD, mốc **Tuần 4**.

Cương **không** viết lại `behaviors.py`. Đọc `src/algorithms/dbo.py`, `behaviors.py`, bài Xue & Shen (2023) rồi viết cho người chưa đọc code.

#### Mục lục bắt buộc

| Mục | Nội dung | Ai soạn |
| :--- | :--- | :--- |
| 1. Mục tiêu tuần 4 | DBO gốc trên benchmark; chưa đụng thực đơn | Cương |
| 2. DBO gốc | 4 hành vi (tên + 1–2 câu + công thức chính), tỉ lệ quần thể, tham số bài báo | Cương |
| 3. Bộ hàm benchmark | 6 hàm: công thức ngắn, biên, optimum | Cương (lấy từ `benchmarks.py`) |
| 4. Protocol thí nghiệm | n_agents=30, max_iter=500, M=30, dim 2/10/30, seed | Cương (khớp script Đăng) |
| 5. Kết quả | Dán bảng 18 dòng + hình W4-F1, W4-F2 | Cương dán số/hình Đăng |
| 6. Nhận xét | Unimodal vs multimodal; dim 30; Sphere có hội tụ không | Cương, **phải có số** |
| 7. Kết luận + việc tuần 5–6 | Baseline DBO xong, sang IDBO | Cương |

#### Nghiệm thu Cương

- [ ] File Word đủ 7 mục, có bìa.
- [ ] Có **ít nhất 2 hình** W4-F1 và W4-F2 trong mục 5 (không nộp Word không hình).
- [ ] Bảng số liệu không ô trống ở các dòng đã chạy.
- [ ] Không viết “DBO hội tụ tốt” nếu chưa có số từ CSV của Đăng.

---

## Kết quả kiểm thử tuần 4

```text
============================= 111 passed in 0.78s ==============================
```

| File test | Số test | Nội dung chính |
| :--- | :--- | :--- |
| `tests/test_dbo.py` | 11 | DBOResult fields, optimize(), seed reproducibility, history non-increasing, bounds, behavior groups |
| `tests/test_benchmarks.py` | 27 | Registry, case-insensitive lookup, bounds, optimum values at known optimum (dim 2/10/30), vectorized batch evaluation |
| `tests/test_constraints.py` | 5 | Feasible menu, duplicates, portion range, meal_type mismatch |
| `tests/test_menu.py` | 11 | Load CSV, encode/decode round-trip, meal_counts, meal_type from CSV |
| `tests/test_model.py` | 14 | End-to-end profile → score, fitness clamped, violations |
| `tests/test_nutrition.py` | 22 | BMR/TDEE, macro/micro targets, DRI thresholds |
| `tests/test_objective.py` | 4 | Weights, fitness range, preference, diversity |

### Demo tuần 4

```bash
# Dry-run (không cần behaviors.py)
python scripts/demo_week4.py --dry-run --function sphere --dim 10

# Full run (cần behaviors.py)
python scripts/demo_week4.py --function sphere --dim 10 --max-iter 500
```

**Kết quả demo Sphere 10D:**
- Best fitness: `1.47e-204` (hội tụ gần máy tính)
- Runtime: `0.11s`
- Evaluations: `15030` (30 agents × 500 iterations)

### Lệnh chạy test tuần 4

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Quy trình làm việc (Git)
1. Mỗi thành viên tạo nhánh riêng từ `main`:
   - `git checkout -b 260907-feat-week4-dbo-core` (Duy)
   - `git checkout -b 260907-feat-week4-dbo-behaviors` (Cương)
   - `git checkout -b 260907-feat-week4-benchmark` (Đăng)
2. Commit rõ ràng, ví dụ: `feat(behaviors): implement reproduction operator`.
3. Push và tạo Merge Request (MR) về `main`.
4. Trưởng nhóm review + merge; trước khi merge chạy `python3 -m pytest tests/`.
5. Tránh commit file lớn (`experiments/week4/*.csv`, hình) — thêm vào `.gitignore`.

## Quy ước chung
- Ngôn ngữ: Python + NumPy; **không thêm thư viện mới** nếu chưa bàn trong nhóm.
- Mọi hàm ngẫu nhiên nhận `rng: np.random.Generator`; seed mặc định ghi rõ trong log.
- Số liệu fitness trong thí nghiệm dùng **cùng cấu hình DBO** (n_agents, max_iter) cho mọi hàm để so sánh công bằng.
- Hợp đồng hàm (`signature`) chốt trong file này; muốn đổi phải báo cả nhóm trước khi sửa.

## Tài liệu tham khảo
1. J. Xue and B. Shen, "Dung beetle optimizer: a new meta-heuristic algorithm for global optimization," The Journal of Supercomputing, vol. 79, pp. 7305-7336, 2023.
2. IEEE CEC benchmark functions (Sphere, Rastrigin, Rosenbrock, Ackley, Griewank, Schwefel 2.22).
