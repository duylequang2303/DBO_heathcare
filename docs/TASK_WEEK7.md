# Phân Công Công Việc Tuần 7 — IDBO Tối Ưu Thực Đơn

Nhóm: Lê Quang Duy (trưởng nhóm) · Đặng Nguyễn Minh Đăng · Hồ Trung Cương

> Tuần 7 **không** chạy lại benchmark Sphere/Rastrigin. Khung DBO/IDBO đã xong. Việc tuần này: **gắn fitness thực đơn vào `optimize()`**, **chọn món hợp lệ**, **xử lý ràng buộc khi giải mã**. Chưa làm web (tuần 9). Chưa quét nhiều nhóm vận động (tuần 8).

## Mục tiêu (theo đề cương)

| Tuần | Nội dung đề cương | Việc nhóm làm |
| :--- | :--- | :--- |
| 7 | Chuyển IDBO sang tối ưu thực đơn; biểu diễn nghiệm, xử lý ràng buộc | Adapter `x` khẩu phần → Menu → fitness; sampler `food_ids`; demo + thí nghiệm nhỏ |
| 8 (chưa làm) | Hoàn thiện hàm mục tiêu; thử nghiệm theo nhóm nhu cầu / mức vận động | Đổi `WEIGHTS`, nhiều profile |

## Đã có sẵn (không làm lại)

| File | Việc gì |
| :--- | :--- |
| `src/algorithms/dbo.py`, `idbo.py` | `optimize(objective, dim, lb, ub, seed)` — **không đổi signature** |
| `src/algorithms/behaviors.py` | 4 hành vi DBO gốc — **không sửa** |
| `src/models/menu.py` | `encode()` / `decode(food_ids, portions_g, food_map, meal_counts)` |
| `src/models/objective.py` | `evaluate(menu, profile, targets)` trong `[-100, 100]`, **cao hơn tốt hơn** |
| `src/models/constraints.py` | Penalty đã nằm trong fitness; `validate_menu()` |
| `src/utils/data_loader.py` | `load_food_db()`, `build_food_map()` — 15.929 món |
| `scripts/demo_week3.py` | Profile mẫu Duy 22t, 170 cm, 65 kg, MODERATE, MAINTAIN, 2-2-2-2 |

```bash
python -m pytest tests/
python scripts/demo_week3.py
```

Còn thiếu so với đề cương: **callable fitness thực đơn cho IDBO**, **chọn `food_ids` hợp lệ**, **demo 1 lần chạy IDBO ra thực đơn**, **CSV + hình + Word**.

---

## Thiết kế chốt (không tự đổi)

### 1. Vector nghiệm

Giữ đúng format tuần 3:

```text
x        = [p_bf_1, ..., p_bf_k, p_lunch_..., p_dinner_..., p_snack_...]   # gram, liên tục
food_ids = [id_bf_1, ..., id_bf_k, ...]                                   # rời rạc, cùng thứ tự
```

- `dim = sum(meal_counts)` — profile mẫu = **8**.
- Biên: `lb = 25`, `ub = 350` (khớp `PORTION_RANGE`).
- IDBO **chỉ tối ưu `x`**. `food_ids` chọn **trước** 1 lần, giữ nguyên trong cả `optimize()`.
- Tuần 7 **không** lai ghép rời rạc trong vòng DBO. Đổi món nằm tuần 10.

### 2. Chiều tối ưu

`evaluate()` **maximize**. DBO/IDBO **minimize**. Adapter bắt buộc:

```text
objective(x) = -evaluate(Menu.decode(food_ids, x, food_map, meal_counts), profile, targets)
```

Vẽ hình: `fitness = -result.history[t]` (cao hơn tốt hơn). Không in số âm của adapter ra bảng Word mà không chú thích.

### 3. Ràng buộc — 3 lớp, không đè lên nhau

| Lớp | Ai làm | Cách |
| :--- | :--- | :--- |
| Biên khẩu phần | DBO `clip` sẵn | `lb=25`, `ub=350` |
| Penalty dinh dưỡng / số món / dị ứng | `objective.py` sẵn | Không sửa `WEIGHTS` tuần này |
| Chọn món hợp lệ | Sampler tuần 7 | Lọc `meal_type`, dị ứng, dislike, không trùng `food_id` |

Không viết thêm death-penalty trong `dbo.py`. Không đổi 4 hành vi.

### 4. Profile bắt buộc (P1)

Giống `scripts/demo_week3.py`:

| Trường | Giá trị |
| :--- | :--- |
| name | Duy |
| age / gender | 22 / male |
| height_cm / weight_kg | 170 / 65 |
| activity_level | MODERATE |
| goal | MAINTAIN |
| meal_counts | breakfast 2, lunch 2, dinner 2, snack 2 |
| allergies / dislikes / likes | `[]` |

Thêm P2 (nữ, LOSE_WEIGHT) **chỉ khi** P1 chạy ổn — không bắt buộc để nghiệm thu tuần 7.

### 5. Cấu hình tìm kiếm (khác benchmark tuần 4–6)

Đánh giá 1 menu chậm hơn Sphere. **Không** copy `max_iter=500`, `M=30` của tuần 4.

| Tham số | Giá trị | Lý do |
| :--- | :--- | :--- |
| Thuật toán | `dbo` và `idbo` | So sánh cùng `food_ids`, cùng seed |
| `n_agents` | `30` | Giống tuần 4 |
| `max_iter` | `200` | Đủ để thấy fitness tăng; không overnight |
| `M` | `10` | 2 algo × 1 profile × 10 seed = 20 run bản chính |
| `dim` | `8` | `sum(meal_counts)` của P1 |
| `lb`, `ub` | `25`, `350` | Gram |
| Seed run `r` | `7000 + r` (`r = 1..M`) | Không dùng công thức benchmark `1000*(f_idx+1)+...` |
| Seed chọn món | `7000` (1 lần, dùng cho mọi run) | Cùng `food_ids` thì so DBO vs IDBO được |

Tổng run: **20**. Smoke: `M=2`, `max_iter=40`.

So sánh **fixed-iteration**, không equal-evaluation-budget. Cột Thắng (mean fitness gốc, cao hơn tốt):

1. `hòa` nếu `|mean_IDBO - mean_DBO| / max(|mean_DBO|, 1e-9) < 0.01`
2. `IDBO` nếu không hòa và `mean_IDBO > mean_DBO`
3. `DBO` nếu không hòa và `mean_DBO > mean_IDBO`

---

## Kiến trúc file mới

```text
src/algorithms/
  menu_objective.py     # Duy — adapter objective(x) = -fitness
src/models/
  food_sampler.py       # Cương — chọn food_ids hợp lệ theo bữa
scripts/
  demo_week7.py         # Duy — 1 lần IDBO, in thực đơn + fitness
  experiment_week7.py   # Đăng — M run DBO vs IDBO, CSV
  plot_week7.py         # Đăng — 2 PNG
tests/
  test_menu_objective.py
  test_food_sampler.py
experiments/week7/      # gitignore CSV/PNG
docs/
  TASK_WEEK7.md         # file này
  BaoCao_Tuan7.docx     # Duy gộp cuối tuần
```

Không commit `experiments/week7/*.csv` hay `*.png`.

---

## Phân công & Quy trình Song Song (Parallel Execution Plan)

Nhóm chia làm 3 luồng công việc, trong đó **Hồ Trung Cương và Đặng Nguyễn Minh Đăng triển khai song song** ngay từ đầu dựa trên hợp đồng giao diện (interface contract) đã chốt:

| Thành viên | Pha 1: Triển khai độc lập & Song song | Pha 2: Khớp nối & Chạy thực nghiệm | Pha 3: Nghiệm thu & Báo cáo | Nộp gì |
| :--- | :--- | :--- | :--- | :--- |
| **Hồ Trung Cương** (Song song) | • Code `src/models/food_sampler.py`<br>• Viết 6 tests trong `tests/test_food_sampler.py`<br>• Soạn nháp Mục 2 & 3 Word (Biểu diễn & Ràng buộc) | Cung cấp sampler `food_ids` (seed 7000) cho Duy & Đăng | Rà soát Mục 2–3 trong bản gộp cuối | `food_sampler.py`, `tests/test_food_sampler.py`, mục 2–3 Word |
| **Đặng Nguyễn Minh Đăng** (Song song) | • Dựng khung `scripts/experiment_week7.py`<br>• Dựng script vẽ `scripts/plot_week7.py`<br>• Chuẩn bị schema 3 file CSV & 2 hình<br>• Soạn nháp Mục 4 & khung Mục 5 Word | Nhận sampler & adapter $\rightarrow$ Bấm chạy M=10 runs thực nghiệm DBO vs IDBO, xuất CSV + PNG | Trả lời 5 câu hỏi mục 5; điền số Bảng 1 & 2 Word | CSV (`runs`, `summary`, `history`), 2 PNG (W7-F1, W7-F2), mục 4–5 Word |
| **Lê Quang Duy** (Trưởng nhóm) | • Code `src/algorithms/menu_objective.py`<br>• Viết tests `tests/test_menu_objective.py`<br>• Code script `scripts/demo_week7.py`<br>• Soạn Mục 1 Word | Khớp nối pipeline, kiểm tra tương thích giữa các module | Tổng hợp toàn bộ Word `docs/BaoCao_Tuan7.docx` (Mục 1, 6, 7, Phụ lục), test toàn hệ thống, quản lý Git | `menu_objective.py`, `demo_week7.py`, `tests/test_menu_objective.py`, `docs/BaoCao_Tuan7.docx` |

### Quy trình phối hợp song song 4 bước:

1. **Bước 1 (Song song độc lập):**
   - **Cương**: Code `food_sampler.py` và hoàn thành 6 unit tests cho sampler. Đồng thời soạn nháp Mục 2 & 3 của báo cáo Word.
   - **Đăng**: Viết sẵn khung script thí nghiệm `experiment_week7.py` và script vẽ đồ thị `plot_week7.py` dựa trên hợp đồng hàm đã chốt ở mục 1.1 và 2.1. Đồng thời soạn nháp Mục 4 của báo cáo Word.
   - **Duy**: Code adapter `menu_objective.py` và unit tests. Soạn nháp Mục 1 của báo cáo Word.
2. **Bước 2 (Khớp nối module):**
   - Duy kiểm thử `demo_week7.py` với `food_sampler.py` và `menu_objective.py`. Chạy `pytest tests/` bảo đảm 100% test xanh.
3. **Bước 3 (Đăng chạy thực nghiệm & phân tích):**
   - Đăng chạy pipeline thực nghiệm chính thức ($M=10$, $max\_iter=200$, $N=30$) trên Profile P1.
   - Xuất 3 file CSV, vẽ 2 hình W7-F1 và W7-F2, trả lời 5 câu hỏi phân tích định lượng (Mục 5).
4. **Bước 4 (Duy nghiệm thu & tổng hợp báo cáo):**
   - Duy gộp các phần văn bản từ Cương (Mục 2-3) và Đăng (Mục 4-5) vào báo cáo chuẩn `docs/BaoCao_Tuan7.docx`.
   - Viết Mục 1 (Mở đầu), Mục 6 (Thảo luận khoa học), Mục 7 (Kết luận & Định hướng Tuần 8), Phụ lục.
   - Chạy toàn bộ test suite, cập nhật README và commit/push lên GitHub.

---

## 1. Cương — chọn món hợp lệ

> **Phương thức làm việc song song (Pha 1):** Cương triển khai độc lập module `src/models/food_sampler.py`, viết đủ 6 unit tests cho sampler, đồng thời soạn thảo nháp nội dung Mục 2 (Biểu diễn nghiệm) và Mục 3 (Xử lý ràng buộc) cho báo cáo Word mà không phải chờ đợi các thành viên khác.

Cương **không** sửa `behaviors.py` / `idbo.py`. File được phép: `src/models/food_sampler.py`, `tests/test_food_sampler.py`. Được đọc `menu.py`, `constraints.py`, `data_loader.py`; không đổi API `encode`/`decode`.

### 1.1 Hợp đồng hàm (chốt)

```python
def sample_food_ids(
    food_map: dict,
    meal_counts: dict[str, int],
    profile: UserProfile,
    rng: np.random.Generator,
) -> list[str]:
    """Trả về list food_id, độ dài = sum(meal_counts), thứ tự breakfast→lunch→dinner→snack."""
```

Bắt buộc:

1. Breakfast chỉ lấy `meal_type == "breakfast"` (hoặc rỗng/`all` nếu pool breakfast < số món — ghi rõ trong docstring nếu phải fallback, ưu tiên đúng nhãn CSV).
2. Snack chỉ lấy `meal_type == "snack"`.
3. Lunch/dinner lấy `meal_type == "all"`.
4. Loại món tên chứa token `profile.allergies` hoặc `profile.dislikes`.
5. Không trùng `food_id` trong ngày.
6. Thiếu pool → `ValueError` rõ ràng (tên bữa + số candidate), không im lặng trả list ngắn.
7. Mọi ngẫu nhiên qua `rng`, không `np.random.seed` toàn cục.

Gợi ý API phụ (nếu cần):

```python
def candidates_for_meal(food_map, meal_name: str, profile) -> list[str]: ...
```

### 1.2 Test bắt buộc (`tests/test_food_sampler.py`)

1. Độ dài list = `sum(meal_counts)` với P1 (8).
2. Cùng `rng` seed → cùng `food_ids`.
3. Không trùng `food_id`.
4. Không món tên chứa allergy (thêm 1 profile test `allergies=["peanut"]`).
5. Breakfast id có `meal_type` thuộc tập cho phép; snack tương tự.
6. `meal_counts` lẻ (ví dụ snack=0) vẫn round-trip được với `Menu.decode`.

### 1.3 Mục 2–3 Word (Cương soạn)

**Mục 2 — Biểu diễn nghiệm thực đơn (~1 trang)**

- `x` vs `food_ids`; vì sao IDBO chỉ sửa gram.
- `dim=8`, biên 25–350 g.
- 1 hình: vector 8 ô → 4 bữa.

**Mục 3 — Xử lý ràng buộc (~1.5 trang)**

- 3 lớp (biên / penalty / sampler) đúng mục **Thiết kế chốt**.
- Ví dụ 1 món bị loại vì dị ứng.
- Không chép nguyên `constraints.py`.

### 1.4 Nghiệm thu Cương

- [ ] `sample_food_ids` đúng hợp đồng, 6 test xanh.
- [ ] Mục 2–3 Word có sơ đồ, không bịa thêm hành vi DBO.
- [ ] Không đổi signature `Menu.decode`.

Nhánh gợi ý: `260926-feat-week7-food-sampler`.

---

## 2. Duy — adapter + demo + Git + Word

File được phép: `src/algorithms/menu_objective.py`, `scripts/demo_week7.py`, `tests/test_menu_objective.py`, `README.md`, `docs/BaoCao_Tuan7.docx`. Không sửa `optimize()` signature. Không sửa `WEIGHTS`.

### 2.1 Hợp đồng adapter

```python
def make_menu_objective(
    profile: UserProfile,
    food_ids: list[str],
    food_map: dict,
    targets: dict[str, float],
) -> Callable[[np.ndarray], float]:
    """objective(x) = -evaluate(decode(...)). x.shape == (dim,)."""
```

Bắt buộc:

1. `len(x) == len(food_ids) == sum(profile.meal_counts)`; sai → `ValueError`.
2. Decode bằng `Menu.decode(..., meal_counts=profile.meal_counts)`.
3. Trả về `-float(evaluate(...))` (minimize).
4. Không gọi IDBO bên trong adapter (thuần callable).
5. Được cache `targets` ở closure; không đọc CSV mỗi lần gọi.

Gợi ý thêm (không bắt buộc nhưng tốt cho demo):

```python
def decode_result(food_ids, x, food_map, meal_counts) -> Menu: ...
```

### 2.2 Test (`tests/test_menu_objective.py`)

1. Menu tốt hơn (gần calo mục tiêu) → `objective` **nhỏ hơn** (vì đã đổi dấu).
2. `x` đúng `dim` của P1; `x` sai dim → `ValueError`.
3. Giá trị nằm trong `[-100, 100]` sau khi đổi dấu ngược (`-objective` trong [−100, 100]).
4. Cùng `x` → cùng số (deterministic).
5. Tích hợp: `IDBO(n_agents=8, max_iter=5).optimize(obj, dim=8, lb=25, ub=350, seed=42)` chạy xong, `best_x` nằm trong [25, 350].

### 2.3 Demo `scripts/demo_week7.py`

```bash
python scripts/demo_week7.py
python scripts/demo_week7.py --algo idbo --max-iter 50 --seed 42
```

In ra (tiếng Việt, không screenshot IDE):

1. Hồ sơ P1 + BMR/TDEE/calo mục tiêu.
2. `food_ids` + tên món (1 dòng / món, kèm bữa và gram).
3. `best_fitness` **gốc** (`-result.best_fitness`), `n_evaluations`, `runtime_s`.
4. Tổng calo / protein / carb / fat / fiber vs target.
5. `validate_menu` — số vi phạm (được phép > 0; ghi rõ).
6. 5 mốc `history` (đổi dấu) chia đều theo `max_iter`, mốc cuối in đúng 1 lần (ví dụ `max_iter=50` → iter 0, 12, 25, 37, 50).

Mặc định: `--algo idbo`, `--max-iter 50`, `--n-agents 30`, seed chọn món `7000`.

### 2.4 Word `docs/BaoCao_Tuan7.docx`

Bìa: đề tài, mã **CNTT-KLCN142**, GVHD ThS. Đinh Nguyễn Trọng Nghĩa, 3 SV + MSSV, mốc **Tuần 7**.

| Mục | Người soạn nháp | Duy làm gì |
| :--- | :--- | :--- |
| 1. Mục tiêu tuần 7 (rời benchmark, vào thực đơn) | Duy | Viết |
| 2. Biểu diễn nghiệm | Cương | Biên tập |
| 3. Xử lý ràng buộc | Cương | Biên tập, đối chiếu code |
| 4. Thiết kế thí nghiệm (protocol mục 5) | Đăng | Kiểm tra tham số |
| 5. Kết quả: bảng + hình W7-F1 W7-F2 | Đăng | Spot-check CSV |
| 6. Thảo luận: IDBO có tốt hơn DBO trên P1 không; vi phạm còn lại | Duy | Viết, bám số |
| 7. Kết luận và việc tuần 8 (nhiều profile / WEIGHTS) | Duy | Viết |
| Phụ lục: lệnh chạy, pytest | Duy | Viết |

Độ dài gợi ý: **6–10 trang**. Font Times New Roman. Không dim=2, không bảng benchmark tuần 4–6.

### 2.5 Git / README

```text
git checkout -b 260926-feat-week7-menu-adapter
```

README: thêm 1 đoạn **Tiến độ tuần 7**, lệnh `demo_week7.py` / `experiment_week7.py`, sửa bảng vai trò.

Trước merge: `python -m pytest tests/`. Thêm `experiments/week7/*.csv|png|json` vào `.gitignore` nếu chưa có.

### 2.6 Nghiệm thu Duy

- [ ] Adapter đổi dấu đúng, 5 test xanh.
- [ ] Demo in đủ 6 khối mục 2.3.
- [ ] Word đủ 7 mục + phụ lục; 3 ô số khớp CSV.
- [ ] Không commit CSV/PNG.
- [ ] Toàn bộ `tests/` vẫn xanh.

---

## 3. Đăng — thí nghiệm P1

> **Phương thức làm việc song song (Pha 1):** Đăng không cần đợi Cương hay Duy hoàn thành mới bắt đầu. Dựa vào hợp đồng hàm đã chốt (Mục 1.1 và 2.1), Đăng viết sẵn cấu trúc script `scripts/experiment_week7.py` (khung vòng lặp, tính vi phạm, dinh dưỡng, xuất CSV) và `scripts/plot_week7.py` (đồ thị W7-F1 và W7-F2), đồng thời soạn nháp trước Mục 4 và dàn ý Mục 5 trong báo cáo Word.

File được phép: `scripts/experiment_week7.py`, `scripts/plot_week7.py`, `requirements.txt` (matplotlib đã có thì không thêm). Không sửa `idbo.py`.

### 3.1 Pipeline

```bash
# Smoke (không nộp)
python scripts/experiment_week7.py --runs 2 --max-iter 40

# Bản chính
python scripts/experiment_week7.py --runs 10 --max-iter 200 --n-agents 30
```

Ghi `experiments/week7/` (gitignore):

| File | Cột bắt buộc |
| :--- | :--- |
| `menu_runs.csv` | `algorithm,profile,run,seed,best_fitness,n_evaluations,runtime_s,n_violations,calories,protein_g,carbs_g,fat_g,fiber_g` |
| `menu_summary.csv` | `algorithm,profile,runs,best,mean,std,worst,mean_n_evaluations,mean_runtime_s,mean_n_violations` |
| `menu_history.csv` | `algorithm,profile,run,iteration,fitness` — **fitness gốc** (đã đổi dấu), iter `0..max_iter` |

`best_fitness` trong CSV là **fitness gốc** (cao hơn tốt), không phải giá trị minimize của optimizer.

Cùng `food_ids` (seed sampler = 7000) cho mọi run. In `food_ids` ra `experiments/week7/food_ids_p1.txt` (1 id / dòng) để Word trích.

### 3.2 Hình

| Mã | Nội dung | File |
| :--- | :--- | :--- |
| W7-F1 | Hội tụ trung bình P1, 2 đường DBO / IDBO, trục Y = fitness gốc | `experiments/week7/fig_convergence_p1.png` |
| W7-F2 | Boxplot best fitness DBO vs IDBO, P1 | `experiments/week7/fig_boxplot_p1.png` |

Legend `DBO` / `IDBO`, chú thích P1, `max_iter=200`, `M=10`.

### 3.3 Bảng copy vào Word

**Bảng 1 — P1 (2 dòng)**

| Algo | best | mean | std | worst | mean n_evals | mean runtime_s | mean n_violations | Thắng (mean) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DBO | | | | | | | | |
| IDBO | | | | | | | | |

**Bảng 2 — dinh dưỡng mean vs target P1** (1 dòng DBO, 1 dòng IDBO): calories, protein_g, carbs_g, fat_g, fiber_g.

Không viết "IDBO tốt hơn" nếu Bảng 1 chưa có số. Hòa nếu chênh mean < 1%.

### 3.4 Năm câu Đăng trả lời trong Word (mục 5)

Trả lời từng câu, có số:

1. Fitness mean IDBO vs DBO: hòa / IDBO / DBO theo ngưỡng 1%?
2. Số vi phạm trung bình giảm được bao nhiêu so với menu ngẫu nhiên (lấy 10 decode ngẫu nhiên cùng `food_ids`, `x ~ U(25,350)` — tính trong script, in ra console)?
3. Calo mean lệch bao nhiêu % so với target?
4. IDBO chậm hơn DBO bao nhiêu % (`mean_runtime_s`)?
5. Hình W7-F1: fitness còn tăng ở iter 200 hay đã bằng? Nếu bằng, khoảng iter nào?

### 3.5 Nghiệm thu Đăng

- [ ] Bản chính M=10, max_iter=200, đủ DBO và IDBO (hoặc giải thích nếu máy không kịp: tối thiểu M=5).
- [ ] 3 CSV + `food_ids_p1.txt` + 2 PNG.
- [ ] Bảng 1–2 điền hết, không ô trống.
- [ ] 5 câu mục 3.4 có số.

Nhánh gợi ý: `260926-feat-week7-menu-experiment`.

---

## Đầu ra cuối tuần 7 (checklist nhóm)

- [ ] `food_sampler.py` + test xanh (Cương).
- [ ] `menu_objective.py` + `demo_week7.py` + test xanh (Duy).
- [ ] CSV + W7-F1 W7-F2 (Đăng).
- [ ] `docs/BaoCao_Tuan7.docx` đủ 7 mục (Duy gộp).
- [ ] README có lệnh tuần 7.
- [ ] `python -m pytest tests/` xanh.

Tuần 8: thêm profile theo mức vận động / goal, cân `WEIGHTS` nếu cần, **chưa** so với GA/PSO (tuần 9), **chưa** web.

## Quy ước

- Không đổi signature `optimize` và 4 hành vi tuần 4.
- Mọi ngẫu nhiên qua `np.random.Generator`.
- CSV/PNG thí nghiệm không commit.
- Số trong Word lấy từ CSV, không bịa.
- Nhánh: `YYMMDD-(feat|docs|fix)-week7-...` ; MR vào `main`; Duy review.

## Tài liệu tham khảo

1. J. Xue and B. Shen, "Dung beetle optimizer: a new meta-heuristic algorithm for global optimization," The Journal of Supercomputing, vol. 79, pp. 7305-7336, 2023.
2. M. Amiri, J. Li, and W. Hasan, "Personalized Flexible Meal Planning...," JMIR Formative Research, vol. 7, e46434, 2023.
3. `docs/TASK_WEEK3.md` — format `x` / `food_ids`.
4. `docs/TASK_WEEK5_6.md` — IDBO; tuần 7 không lặp lại bảng benchmark.
