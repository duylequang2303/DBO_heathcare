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
- [ ] Tạo package `src/algorithms/` với `__init__.py`.
- [ ] Định nghĩa `DBOResult` (dataclass): `best_x`, `best_fitness`, `history` (list fitness tốt nhất theo iteration), `n_evaluations`, `runtime_s`, `seed`.
- [ ] Viết lớp `DBO` với API `optimize(objective, dim, lb, ub, seed=42) -> DBOResult`.
- [ ] Khởi tạo quần thể `n_agents` ngẫu nhiên đều trong `[lb, ub]` theo seed; đánh giá fitness ban đầu.
- [ ] Vòng lặp chính `max_iter`: lần lượt gọi 4 nhóm hành vi (tỉ lệ quần thể mỗi nhóm theo bài báo), cập nhật `best` toàn cục, ghi `history`.
- [ ] Chặn biên (`clip`) nghiệm sau mỗi hành vi về `[lb, ub]`.
- [ ] Viết `tests/test_dbo.py`: (a) chạy seed cố định cho kết quả lặp lại được; (b) `best_fitness` không tăng (history không thoái lui); (c) `best_x` nằm trong biên; (d) hội tụ Sphere 10D dưới `1e-4`.

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
- [ ] Đọc kỹ bài báo Xue & Shen (2023) mục 3 (DBO): công thức 4 hành vi + ý nghĩa tham số.
- [ ] Cài **ball-rolling**: cuộn phân không vật cản (hệ số lệch α, k, b) và nhảy múa khi gặp vật cản (dùng `tan(θ)`, `θ ~ U(0, π)`).
- [ ] Cài **reproduction**: vùng đẻ trứng co dần quanh best hiện tại, sinh cá thể con.
- [ ] Cài **foraging**: vùng tìm kiếm co dần quanh best cục bộ, bọ nhỏ đi kiếm ăn.
- [ ] Cài **thieving**: bọ trộm bám quanh best toàn cục (hệ số S, phân phối Gaussian).
- [ ] Mỗi hành vi nhận `rng` (numpy `Generator`) để tái lập ngẫu nhiên.
- [ ] Ghi chú ngắn cuối file: dòng công thức gốc trong bài báo tương ứng từng hành vi.

**Nghiệm thu:** 4 hàm đủ signature đã chốt; kết quả nhất quán khi dùng cùng `rng`/`seed`; giá trị đầu ra nằm trong khoảng hợp lý khi test đơn lẻ bằng snippet trong `scripts/demo_week4.py`.

#### Hướng dẫn cho Cương
- Bám **đúng tham số gốc** của bài báo cho bản DBO chuẩn (đây là baseline để tuần 6 so sánh IDBO vs DBO). Ghi nguồn tham số vào comment.
- Tỉ lệ quần thể chia 4 nhóm hành vi là hằng số cấu hình của `DBO`, không nằm trong `behaviors.py`.
- Không dùng vòng lặp Python cho vector quần thể; vector hoá bằng NumPy.
- Tham khảo benchmark cần số chiều cố định — đọc từ `X.shape[1]`, không hardcode.

### 3. Đăng — Benchmark & thí nghiệm
- [ ] Cài `src/algorithms/benchmarks.py` với ít nhất 6 hàm: **Sphere, Rastrigin, Rosenbrock, Ackley, Griewank, Schwefel 2.22**.
- [ ] Mỗi hàm: công thức, khoảng biên `(lb, ub)` chuẩn, `optimum` toạ độ + giá trị đã biết (thường là 0 tại 0; Rosenbrock = 0 tại (1,...,1)).
- [ ] Viết `tests/test_benchmarks.py`: giá trị tại optimum sai khác ≤ `1e-8`; so khớp công thức cho `dim = 2`.
- [ ] Viết `scripts/experiment_dbo.py`: với mỗi hàm × mỗi dim (2, 10, 30) chạy `M = 30` lần (seed khác nhau), thu thập `best_fitness`, ghi CSV cột `function, dim, run, best_fitness, iterations`.
- [ ] Tính thống kê: `best / mean / std / worst` theo từng (hàm, dim); xuất bảng kết quả ra console + CSV tóm tắt.
- [ ] (Tùy chọn) Vẽ biểu đồ hội tụ trung bình (log-scale fitness) — cần thêm `matplotlib` vào `requirements.txt` sau khi nhóm đồng ý.

**Nghiệm thu:** 6 hàm benchmark test xanh tại optimum đã biết; script thí nghiệm chạy trọn không lỗi, sinh CSV hợp lệ; DBO cải thiện rõ rệt so với khởi tạo ngẫu nhiên trên Sphere (sai số giảm ≥ 1e3 lần) và bám gần optimum đã biết trên các hàm còn lại ở dim thấp.

## Đầu ra cuối tuần 4
- [ ] Khung `src/algorithms/` + DBO gốc hoàn chỉnh, test xanh (`python3 -m pytest tests/`).
- [ ] 6 hàm benchmark + test xanh.
- [ ] Thí nghiệm M=30 lần trên (hàm × dim) → CSV + bảng thống kê trong `experiments/week4/`.
- [ ] `scripts/demo_week4.py`: chạy DBO 1 lần trên 1 hàm, in `best_x`, `best_fitness`, lịch sử hội tụ.
- [ ] Cập nhật README: mô tả mô-đun DBO tuần 4 và tài liệu tham khảo.
- [ ] Báo cáo ngắn (nhóm trưởng tổng hợp): kết quả hội tụ từng hàm — phục vụ baseline cho tuần 5–6.

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
