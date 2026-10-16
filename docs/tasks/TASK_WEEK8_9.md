# Kế Hoạch Tuần 8 & 9 — IDBO Tối Ưu Thực Đơn (Mixed-Integer + Chu Kỳ 7 Ngày)

Nhóm: Lê Quang Duy (trưởng nhóm) · Đặng Nguyễn Minh Đăng · Hồ Trung Cương

> **Gốc gác từ góp ý Tuần 7:** Thầy đề nghị (1) làm tròn gram, (2) bổ sung A/B Test DBO vs IDBO,
> (3) mở rộng từ 8 món cố định → tự chọn từ kho 15.929 món, (4) sinh thực đơn 7 ngày không trùng + đa profile bệnh lý.

---

## Tổng Quan Lộ Trình

| Tuần | Tên giai đoạn | Đầu ra chính |
| :--- | :--- | :--- |
| **7 (Xong)** | Proof of Concept — 8 món cố định | `menu_objective.py`, `food_sampler.py`, CSV/PNG, Word T7 |
| **8** | Mixed-Integer — Tự chọn món từ kho 15.929 + A/B Test | 2-tier solver, bảng đối chứng DBO vs IDBO |
| **9** | Chu kỳ 7 ngày + Đa profile bệnh lý + UX đa phương án | 7-day planner, P2/P3, Option A/B/C |

---

## Phần 0 — Fix Ngay Sau Tuần 7

Các fix nhỏ này phải **merge vào `main` trước** khi bắt đầu nhánh tuần 8.

### 0.1 Fix Gram Lẻ — Post-processing Làm Tròn 5g

**Vấn đề:** Thuật toán trả về 71.3g, 336.3g — không cân được trong bếp thực tế.

**Giải pháp ngắn hạn:** Thêm `round_portions()` trong `src/utils/portion_utils.py`.

```python
# src/utils/portion_utils.py
import numpy as np
from typing import Literal

def round_portions(
    portions_g: np.ndarray,
    step: int = 5,
    mode: Literal["nearest", "floor", "ceil"] = "nearest",
) -> np.ndarray:
    """
    Làm tròn mảng gram về bội số của step.
    Mặc định step=5: 71.3 → 70g, 336.3 → 335g.
    Sai số tối đa ±2.5g ≈ ±5~15 kcal — an toàn trong dinh dưỡng.
    """
    if mode == "nearest":
        return (np.round(portions_g / step) * step).astype(int)
    elif mode == "floor":
        return (np.floor(portions_g / step) * step).astype(int)
    else:
        return (np.ceil(portions_g / step) * step).astype(int)
```

**Quy tắc áp dụng:**
- Output-facing (demo, Word, slide): luôn gọi `round_portions(best_x, step=5)` trước khi in.
- **Không** đưa làm tròn vào bên trong `objective(x)` — optimizer cần precision liên tục.
- In 2 dòng: "Gram tối ưu (gốc): 71.3g" và "Gram thực tế (5g): 70g".

**Checklist fix 0.1:**
- [ ] Tạo `src/utils/portion_utils.py` với `round_portions()`.
- [ ] Unit test: 71.3→70, 336.3→335, 337.6→340 (step=5).
- [ ] Cập nhật `demo_week7.py` in cả 2 dòng gram.
- [ ] Không thay đổi logic tối ưu.

---

### 0.2 Fix A/B Test Còn Thiếu — Bảng Đối Chứng DBO vs IDBO Trên Cùng P1

**Vấn đề:** Slide Tuần 7 thiếu bảng so sánh trực tiếp DBO vs IDBO cùng bài toán thực đơn.

**Giải pháp:** Script `scripts/ab_test_week7_fix.py` chạy 10 seed song song.

Cột bắt buộc trong bảng kết quả:

| Algo | Best Fitness | Mean Fitness | Std | Worst | Mean n_violations | Sai lệch Calo (%) | Mean runtime (s) | Thắng |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DBO | | | | | | | | |
| IDBO | | | | | | | | |

**Tiêu chí phán thắng/thua/hòa** (giữ nguyên từ TASK_WEEK7):

| Điều kiện | Kết quả |
| :--- | :--- |
| `|mean_IDBO - mean_DBO| / max(|mean_DBO|, 1e-9) < 0.01` | **Hòa** |
| Không hòa và `mean_IDBO > mean_DBO` | **IDBO thắng** |
| Không hòa và `mean_DBO > mean_IDBO` | **DBO thắng** |

> **Lưu ý khoa học:** Nếu kết quả hòa, giải thích rõ trong báo cáo: địa hình liên tục mượt
> (8 món cố định, chỉ tối ưu gram) → bọ không bị kẹt → Cauchy/Restart không kích hoạt →
> IDBO bảo toàn 100% sức mạnh DBO gốc, không can thiệp thừa (overhead +0.028% evals).
> Đây là **bằng chứng thiết kế tốt**, không phải thất bại.

**Checklist fix 0.2:**
- [ ] `scripts/ab_test_week7_fix.py`: M=10, max_iter=200, n_agents=30, food_ids seed=7000.
- [ ] Xuất `experiments/week7/ab_test_summary.csv` đủ 8 cột.
- [ ] Thêm slide "A/B Test DBO vs IDBO — P1" vào deck tuần 7.
- [ ] Giải thích khoa học khi hòa.

---

## Phần 1 — Tuần 8: Mixed-Integer Optimization (Tự Chọn Món)

### 1.0 Bối Cảnh & Mục Tiêu Khoa Học

Tuần 7 cố định `food_ids` → chỉ tối ưu gram = **bài toán liên tục thuần**.

Tuần 8 nâng lên **Mixed-Integer Combinatorial**:

> Từ kho **15.929 món**, đồng thời **chọn k món** (rời rạc) **VÀ tối ưu gram** (liên tục).

Đây là địa hình có **vô số cực trị địa phương xấu** (chọn sai tổ hợp món → penalty lớn).
Đây chính là "chiến trường" nơi **IDBO vượt trội DBO** nhờ Cauchy mutation và Restart.

### 1.1 Kiến Trúc 2-Tầng (Two-Tier Solver)

```
┌─────────────────────────────────────────────────────────┐
│  TẦNG 1 (Outer): IDBO tối ưu tổ hợp món (rời rạc)     │
│    z = [z1, ..., zk],  z_i ∈ [0, 1)                   │
│    decode: z_i → food_id trong pool bữa tương ứng       │
│    Mỗi đánh giá z → gọi Tầng 2 lấy fitness             │
│    outer_max_iter = 100, outer_n_agents = 20            │
└────────────────────────┬────────────────────────────────┘
                         ▼ food_ids (rời rạc)
┌────────────────────────┴────────────────────────────────┐
│  TẦNG 2 (Inner): IDBO tối ưu gram (liên tục)           │
│    x = [p1, ..., pk],  lb=25, ub=350                   │
│    objective(x | food_ids) → fitness                    │
│    inner_max_iter = 50, inner_n_agents = 15             │
└─────────────────────────────────────────────────────────┘
```

**Lý do tách 2 tầng riêng:**
- Giữ nguyên interface `optimize(objective, dim, lb, ub)` không phá vỡ.
- Dễ debug từng tầng độc lập.
- Tuần 9 thêm tầng 3 (7 ngày) không cần refactor core.

### 1.2 File Mới Tuần 8

```
src/algorithms/
  two_tier_solver.py      # Duy — wrapper 2-tầng
src/models/
  food_selector.py        # Cương — z_i → food_id (rời rạc)
src/utils/
  portion_utils.py        # Duy — round_portions() (từ fix 0.1)
scripts/
  ab_test_week7_fix.py    # Duy — fix 0.2
  demo_week8.py           # Duy — chạy 1 lần, in thực đơn
  experiment_week8.py     # Đăng — M=10, DBO vs IDBO 2-tier
  plot_week8.py           # Đăng — 3 hình W8-F1..F3
tests/
  test_two_tier_solver.py
  test_food_selector.py
  test_portion_utils.py
experiments/week8/        # gitignore
docs/
  BaoCao_Tuan8.docx
```

### 1.3 food_selector.py — Cương làm (Kế hoạch phối hợp Phương án 2)

> **💡 Điều phối tiến độ nhóm (Phương án 2):**
> - Duy đã hỗ trợ dựng baseline code `food_selector.py` và 6 tests để **unblock ngay cho Đăng** chạy thực nghiệm Two-Tier Tuần 8 mà không bị trễ hạn.
> - **Cương nhận nhiệm vụ bù đắp đóng góp:**
>   1. **Git Commit cá nhân:** Cương checkout branch `261003-feat-week8-food-selector`, review hoàn thiện docstring toán học và bổ sung test cases góc (edge cases) để có commit mang tên mình trên GitHub.
>   2. **Báo cáo Word Tuần 8:** Cương phụ trách viết chính **Mục 2 & Mục 4** trong `BaoCao_Tuan8.docx` (Lý thuyết Mixed-Integer, Candidate Pools từ 15.929 món và thuật toán Linear Probing chống trùng món).
>   3. **Làm sớm Tuần 9 (Head Start):** Cương nhận làm sớm module cốt lõi Tuần 9: `src/models/diversity_penalty.py` và `tests/test_diversity_penalty.py`.

**Hợp đồng hàm chốt:**

```python
def decode_food_selection(
    z: np.ndarray,                    # shape (k,), float [0, 1)
    pools: dict[str, list[str]],      # pools[meal_slot] = [food_id, ...]
    meal_order: list[str],            # ['bf_0','bf_1','lunch_0',...]
) -> list[str]:
    """Ánh xạ z_i ∈ [0,1) → food_id. Không trùng food_id cùng bữa."""

def build_meal_pools(
    food_map: dict,
    meal_counts: dict[str, int],
    profile: UserProfile,
    min_pool_size: int = 20,
) -> dict[str, list[str]]:
    """Xây pools cho từng slot bữa, lọc meal_type + dị ứng.
    ValueError nếu pool < min_pool_size."""
```

**Cách ánh xạ rời rạc (không dùng int casting thô):**

```python
idx = int(z_i * len(pool)) % len(pool)
```

**6 tests bắt buộc (`tests/test_food_selector.py`):**
1. Cùng `z` → cùng `food_ids` (deterministic).
2. Không trùng `food_id` trong cùng bữa.
3. `z` toàn 0.0 → lấy phần tử đầu pool.
4. `z` toàn 0.999 → lấy phần tử cuối pool.
5. Pool rỗng sau lọc dị ứng → `ValueError` rõ ràng.
6. `min_pool_size=20`: pool đủ size với P1.

### 1.4 two_tier_solver.py — Duy làm

```python
from dataclasses import dataclass

@dataclass
class TwoTierConfig:
    outer_algo: str = "idbo"      # "dbo" | "idbo"
    outer_n_agents: int = 20
    outer_max_iter: int = 100
    inner_algo: str = "idbo"
    inner_n_agents: int = 15
    inner_max_iter: int = 50
    seed: int = 8000

def two_tier_optimize(
    profile: UserProfile,
    food_map: dict,
    targets: dict,
    config: TwoTierConfig,
) -> TwoTierResult:
    """
    Outer IDBO tối ưu z (chọn món rời rạc).
    Mỗi đánh giá z → inner IDBO tối ưu gram → trả fitness.
    Return: TwoTierResult(best_food_ids, best_portions_g, best_fitness, history)
    """
```

**Lưu ý thiết kế:**
- Outer fitness = best fitness của inner loop với tổ hợp `z` tương ứng.
- Không gọi `evaluate()` trực tiếp trong tầng 1 — phải qua tầng 2.
- Tổng evals tối đa ≈ `outer_iter × outer_agents × inner_iter × inner_agents` (nhỏ do inner_iter=50).

**5 tests (`tests/test_two_tier_solver.py`):**
1. Config mặc định → không exception với P1.
2. `best_portions_g` nằm trong [25, 350].
3. `best_food_ids` đủ `sum(meal_counts)` phần tử.
4. `outer_algo="dbo"` và `"idbo"` đều chạy.
5. Smoke (outer=3, inner=3) → xong trong < 30s.

### 1.5 experiment_week8.py — Đăng làm

```bash
# Smoke
python scripts/experiment_week8.py --runs 2 --outer-iter 10 --inner-iter 10

# Bản chính
python scripts/experiment_week8.py --runs 10 --outer-iter 100 --inner-iter 50
```

**CSV xuất ra `experiments/week8/`:**

| File | Cột bắt buộc |
| :--- | :--- |
| `two_tier_runs.csv` | `algo,profile,run,seed,best_fitness,outer_evals,inner_evals_total,runtime_s,n_violations,calories,protein_g,carbs_g,fat_g,fiber_g` |
| `two_tier_summary.csv` | `algo,profile,runs,best,mean,std,worst,mean_runtime_s,mean_n_violations` |
| `two_tier_history.csv` | `algo,profile,run,outer_iter,best_fitness` |
| `selected_foods_p1.txt` | `food_id TAB food_name TAB meal_slot TAB gram_rounded` (best run) |

**3 hình (`scripts/plot_week8.py`):**

| Mã | Nội dung | File |
| :--- | :--- | :--- |
| W8-F1 | Hội tụ outer loop: DBO 2-tier vs IDBO 2-tier | `fig_convergence_2tier_p1.png` |
| W8-F2 | Boxplot best fitness: DBO 2-tier vs IDBO 2-tier | `fig_boxplot_2tier_p1.png` |
| W8-F3 | Radar dinh dưỡng: mean IDBO vs target P1 | `fig_radar_nutrition_p1.png` |

### 1.6 Bảng Đối Chứng Tuần 8

**Bảng W8-1: DBO 2-tier vs IDBO 2-tier trên P1**

| Algo | Best | Mean | Std | Worst | Mean Violations | Sai lệch Calo (%) | Mean Runtime (s) | Thắng |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DBO 2-tier | | | | | | | | |
| IDBO 2-tier | | | | | | | | |

**Bảng W8-2: T7 (8 món cố định) vs T8 (k món từ kho)**

| Phương pháp | Mean Fitness | Mean Violations | Sai lệch Calo (%) | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| T7-IDBO (cố định) | | | | Số từ T7 CSV |
| T8-IDBO 2-tier | | | | |

> **Kỳ vọng:** IDBO 2-tier thắng DBO 2-tier vì địa hình tổ hợp món có nhiều cực trị xấu.
> Nếu hòa: giải thích outer_max_iter=100 chưa đủ, đề xuất tăng lên 200+.

### 1.7 Phân Công Tuần 8

| Thành viên | Việc chính Tuần 8 | Việc chính Tuần 9 | Nhánh |
| :--- | :--- | :--- | :--- |
| **Hồ Trung Cương** | - Review & test biên `food_selector.py`<br/>- Viết Mục 2 & 4 Word T8<br/>- *(Làm sớm T9)* `diversity_penalty.py` | - Hoàn thiện 7-Day diversity analysis<br/>- Báo cáo chu kỳ thực đơn tuần | `261003-feat-week8-food-selector` |
| **Đặng Nguyễn Minh Đăng** | - `experiment_week8.py` + `plot_week8.py`<br/>- CSV/PNG + Bảng W8-1/W8-2 | - Thực nghiệm so sánh 7-Day Planner<br/>- Biểu đồ radar & phân phối 7 ngày | `261003-feat-week8-experiment` |
| **Lê Quang Duy** | - Fix 0.1+0.2 (đã merge `main`)<br/>- `two_tier_solver.py` + `demo_week8.py`<br/>- Viết Mục 1, 3, 5 Word T8 | - Mở rộng profile P2 (Tiểu đường), P3 (Huyết áp)<br/>- Triển khai 7-Day Weekly Solver | `261003-feat-week8-solver` |

**Thứ tự triển khai (Phương án 2):**
1. ✅ **Fix 0.1 + 0.2 (Duy):** Đã hoàn tất và merge vào `main`.
2. ✅ **Baseline `two_tier_solver.py` + `food_selector.py` (Duy):** Đã hoàn tất, unblock Đăng chạy thực nghiệm ngay.
3. ⏳ **Thực nghiệm & Vẽ hình (Đăng):** Chạy `experiment_week8.py` trên nhánh `261003-feat-week8-solver`.
4. ⏳ **Review & Báo cáo & Head Start T9 (Cương):** Review commit `food_selector.py`, viết Mục 2 & 4 Word T8, làm sớm `diversity_penalty.py`.
5. ⏳ **Tổng hợp Word T8 & PR merge vào `main`**.

### 1.8 Checklist Nghiệm Thu Tuần 8

- [x] `portion_utils.py`: `round_portions()` hoạt động đúng (Fix 0.1 - Duy).
- [x] `ab_test_week7_fix.py`: bảng A/B có số, giải thích khoa học khi hòa (Fix 0.2 - Duy).
- [x] `food_selector.py`: 6 tests xanh, pool ≥ 20 món P1 (Baseline Duy dựng; Cương review & hoàn thiện).
- [x] `two_tier_solver.py`: 5 tests xanh, smoke 0.65s (Duy).
- [x] `demo_week8.py`: in thực đơn đa dạng mỗi lần chạy từ kho 15.929 món (Duy).
- [ ] `experiment_week8.py`: 4 CSV + 3 PNG, bảng W8-1/W8-2 đủ số (Đăng).
- [ ] `BaoCao_Tuan8.docx`: đủ 6 mục + phụ lục (Cả nhóm: Duy 1,3,5; Cương 2,4; Đăng số liệu).
- [x] `python -m pytest tests/` xanh toàn bộ (159/159 passed).
- [ ] Không commit CSV/PNG experiments.

---

## Phần 2 — Tuần 9: Chu Kỳ 7 Ngày + Đa Profile Bệnh Lý + UX Đa Phương Án

### 2.0 Mục Tiêu Khoa Học

Bài toán tuần 9 nâng lên 3 chiều phức tạp:
1. **Thời gian:** Thực đơn 7 ngày liên tiếp, không trùng món chính.
2. **Cá nhân hóa bệnh lý:** P2 (Tiểu đường — kiêng đường/Carb), P3 (Huyết áp — kiêng muối/Natri).
3. **UX:** Sinh 3 phương án A/B/C để người dùng lựa chọn theo sở thích.

### 2.1 Kiến Trúc 3-Tầng (Weekly Planner)

```
┌──────────────────────────────────────────────────────────┐
│  TẦNG 3: 7-Day Planner                                   │
│  Cho ngày d = 1..7:                                      │
│    - Penalty nếu món chính trùng ngày d-1 hoặc d-2      │
│    - Gọi Tầng 2 (Two-Tier) cho ngày d                   │
│    - Cập nhật used_main_dishes set                       │
└──────────────────────────┬───────────────────────────────┘
                           ▼ (lặp 7 lần tuần tự)
              [Tầng 2 Two-Tier — tuần 8]
```

Tầng 3 **không thêm vòng lặp tối ưu mới** — gọi Tầng 2 tuần tự 7 lần, mỗi ngày truyền penalty đa dạng.

### 2.2 diversity_penalty.py — Cương làm

```python
def diversity_penalty(
    day_food_ids: list[str],
    history_food_ids: list[list[str]],
    penalty_weight: float = 10.0,
    lookback_days: int = 2,
) -> float:
    """
    Trả penalty (dương) = penalty_weight × số lần trùng món chính.
    Chỉ nhìn lại lookback_days ngày gần nhất (tránh quá ngặt).
    Món chính = slot lunch_0 và dinner_0 (index cố định trong meal_order).
    """
```

**Tích hợp vào objective:**

```python
def make_menu_objective_with_diversity(
    profile, food_ids, food_map, targets,
    history_food_ids: list[list[str]] = None,
    diversity_weight: float = 10.0,
) -> Callable:
    def objective(x):
        score = -evaluate(decode(...), profile, targets)
        if history_food_ids:
            score += diversity_penalty(food_ids, history_food_ids, diversity_weight)
        return score
    return objective
```

### 2.3 Profile Bệnh Lý Mới — Duy mở rộng

**Mở rộng `src/models/user_profile.py`:**

```python
@dataclass
class UserProfile:
    # ... trường cũ giữ nguyên ...
    condition: str = "healthy"          # "healthy"|"diabetes"|"hypertension"
    max_sugar_g: float | None = None    # P2: giới hạn đường (WHO: 25g/ngày)
    max_sodium_mg: float | None = None  # P3: giới hạn natri (WHO: 1500mg/ngày)

P2_PROFILE = UserProfile(
    name="Lan", age=45, gender="female",
    height_cm=158, weight_kg=62,
    activity_level="LIGHT", goal="LOSE_WEIGHT",
    meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
    condition="diabetes", max_sugar_g=25.0,
)

P3_PROFILE = UserProfile(
    name="Minh", age=55, gender="male",
    height_cm=168, weight_kg=75,
    activity_level="SEDENTARY", goal="MAINTAIN",
    meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
    condition="hypertension", max_sodium_mg=1500.0,
)
```

**Mở rộng `objective.py` — thêm WEIGHTS bệnh lý:**

```python
WEIGHTS_DIABETES     = {**WEIGHTS_BASE, "sugar":  -30.0}  # phạt nặng đường
WEIGHTS_HYPERTENSION = {**WEIGHTS_BASE, "sodium": -25.0}  # phạt nặng natri
```

### 2.4 UX Đa Phương Án (Option A/B/C)

**File:** `scripts/generate_options_week9.py` — Đăng làm

```bash
python scripts/generate_options_week9.py --profile p1 --options 3 --days 7
```

Sinh 3 thực đơn 7 ngày với seed A=9001, B=9002, C=9003. Output dạng bảng so sánh:

```
PHƯƠNG ÁN A (seed 9001)     | PHƯƠNG ÁN B (9002) | PHƯƠNG ÁN C (9003)
Ngày 1: Bún bò Huế, Cơm... | Phở gà, Rau...     | ...
Fitness: 72.3               | 68.1               | 75.2
Sai lệch Calo: +45 kcal    | -12 kcal           | +8 kcal
```

### 2.5 experiment_week9.py — Đăng làm

```bash
python scripts/experiment_week9.py --runs 10 --profiles p1 p2 p3 --days 7
```

**CSV xuất ra `experiments/week9/`:**

| File | Cột |
| :--- | :--- |
| `weekly_runs.csv` | `algo,profile,run,seed,day,fitness,n_violations,calories,protein_g,carbs_g,fat_g,fiber_g,sugar_g,sodium_mg` |
| `weekly_summary.csv` | `algo,profile,runs,mean_fitness_7days,mean_violations,mean_calo_deviation_pct` |
| `diversity_score.csv` | `algo,profile,run,pct_unique_main_dishes` (kỳ vọng ≥ 80%) |

**3 hình (`scripts/plot_week9.py`):**

| Mã | Nội dung |
| :--- | :--- |
| W9-F1 | Heatmap 7 ngày × dinh dưỡng — thực đơn tốt nhất P1 |
| W9-F2 | Bar chart P1/P2/P3: mean fitness và sai lệch target |
| W9-F3 | Radar 3 phương án A/B/C (fitness, đa dạng, sai lệch calo, vi phạm) |

### 2.6 Bảng Đối Chứng Tuần 9

**Bảng W9-1: 3 Profile trên thực đơn 7 ngày**

| Profile | Điều kiện | Mean Fitness | Mean Violations | Sai lệch Calo (%) | % Unique món | Mean Runtime (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| P1 (Healthy-Maintain) | Không | | | | | |
| P2 (Diabetes-Lose) | max_sugar 25g | | | | | |
| P3 (Hypertension) | max_sodium 1500mg | | | | | |

**Bảng W9-2: DBO vs IDBO trên 7-day planner, P1**

| Algo | Mean 7-day Fitness | Mean Violations | % Unique Main Dishes | Runtime (s) | Thắng |
| :--- | :--- | :--- | :--- | :--- | :--- |
| DBO 2-tier | | | | | |
| IDBO 2-tier | | | | | |

### 2.7 File Mới Tuần 9

```
src/models/
  diversity_penalty.py      # Cương
scripts/
  experiment_week9.py       # Đăng
  plot_week9.py             # Đăng
  generate_options_week9.py # Đăng
  demo_week9.py             # Duy
tests/
  test_diversity_penalty.py
  test_weekly_planner.py
experiments/week9/
docs/
  BaoCao_Tuan9.docx
```

### 2.8 Phân Công Tuần 9

| Thành viên | Việc chính | Nhánh |
| :--- | :--- | :--- |
| **Hồ Trung Cương** | `diversity_penalty.py` + tests + Mục 2 Word T9 | `261010-feat-week9-diversity` |
| **Đặng Nguyễn Minh Đăng** | `experiment_week9.py` + `plot_week9.py` + `generate_options_week9.py` + CSV/PNG + Bảng | `261010-feat-week9-experiment` |
| **Lê Quang Duy** | P2/P3 profiles + WEIGHTS + `demo_week9.py` + Word T9 | `261010-feat-week9-profiles` |

### 2.9 Checklist Nghiệm Thu Tuần 9

- [ ] `diversity_penalty.py`: trùng món → penalty > 0, không trùng → 0.
- [ ] P2: max_sugar_g=25 → penalty hoạt động, món đường bị phạt nặng.
- [ ] P3: max_sodium_mg=1500 → penalty hoạt động.
- [ ] 7-day planner: chạy 7 ngày, ≥ 80% ngày không trùng món chính.
- [ ] `generate_options_week9.py`: 3 phương án A/B/C có fitness khác nhau.
- [ ] Bảng W9-1/W9-2 đủ số.
- [ ] `python -m pytest tests/` xanh toàn bộ.
- [ ] Không commit CSV/PNG experiments.

---

## Phần 3 — Quy Ước Chung Tuần 8 & 9

### 3.1 Không Bao Giờ Sửa

- `src/algorithms/dbo.py` — signature `optimize()`.
- `src/algorithms/behaviors.py` — 4 hành vi gốc.
- `src/algorithms/idbo.py` — chỉ Duy được sửa khi có bug thực sự.
- `src/models/menu.py` — `encode()`/`decode()` API.

### 3.2 Số Trong Word

Mọi con số trong Word **phải lấy từ CSV** — không bịa, không estimate.
Duy spot-check ít nhất 3 ô số ngẫu nhiên trước khi merge Word.

### 3.3 Gram Hiển Thị

- Output-facing: luôn `round_portions(x, step=5)`.
- Optimizer input: luôn `x` liên tục gốc.
- **Không bao giờ** in số gram lẻ trong bảng Word.

### 3.4 Seed Convention

| Mục | Seed |
| :--- | :--- |
| Tuần 7 — sampler | 7000 |
| Tuần 7 — runs | 7001..7010 |
| Tuần 8 — runs | 8001..8010 |
| Tuần 9 — runs | 9001..9010 |
| Tuần 9 — Option A/B/C | 9001 / 9002 / 9003 |

### 3.5 Nhánh Git

```
YYMMDD-(feat|fix|docs)-week(8|9)-<tên-ngắn>
```

Ví dụ: `261003-feat-week8-food-selector`, `261010-fix-week9-diversity`.

### 3.6 Khi Kết Quả Hòa

1. **Không** xóa kết quả hoặc bịa số.
2. Viết giải thích khoa học trong Thảo luận.
3. Đề xuất cải tiến cụ thể (tăng outer_max_iter, giảm pool size, thêm Tabu Search).

---

## Phần 4 — Kỳ Vọng Kết Quả Khoa Học

| Giai đoạn | Kỳ vọng IDBO vs DBO | Lý do |
| :--- | :--- | :--- |
| T7 (8 món cố định, gram) | **Hòa** | Địa hình liên tục mượt → Cauchy/Restart không kích hoạt |
| T8 (Mixed-Integer 2-tier) | **IDBO ≥ DBO** | Tổ hợp món tạo cực trị xấu → Cauchy cần thiết |
| T9 (7-day + bệnh lý) | **IDBO > DBO rõ** | Không gian tìm kiếm phức tạp nhất, nhiều ràng buộc nhất |

> Kỳ vọng ≠ kết thúc. Nếu trái kỳ vọng → **phát hiện khoa học có giá trị**.

---

## Phần 5 — Timeline Thực Hiện

### Tuần 8

| Ngày | Duy | Cương | Đăng |
| :--- | :--- | :--- | :--- |
| 1–2 | Fix 0.1 + 0.2, merge `main` | Bắt đầu `food_selector.py` | Khung `experiment_week8.py` |
| 3–4 | `two_tier_solver.py` + tests | Hoàn thành selector + 6 tests | Smoke --runs 2 |
| 5–7 | `demo_week8.py` + Word T8 | Review + merge | Bản chính --runs 10, CSV+PNG |

### Tuần 9

| Ngày | Duy | Cương | Đăng |
| :--- | :--- | :--- | :--- |
| 1–2 | P2/P3 profiles + WEIGHTS | `diversity_penalty.py` | Khung `experiment_week9.py` |
| 3–4 | Tích hợp penalty + 7-day planner | Tests diversity | Smoke P1/P2/P3 |
| 5–7 | `demo_week9.py` + Word T9 | Review + merge | Bản chính 3 profile × 10 seeds, `generate_options_week9.py` |

---

## Tài Liệu Tham Khảo

1. J. Xue and B. Shen, "Dung beetle optimizer," *The Journal of Supercomputing*, vol. 79, 2023.
2. M. Amiri et al., "Personalized Flexible Meal Planning," *JMIR Formative Research*, vol. 7, e46434, 2023.
3. `docs/TASK_WEEK7.md` — thiết kế chốt tuần 7.
4. `docs/TASK_WEEK5_6.md` — IDBO; Cauchy mutation; Restart.
5. WHO Dietary Guidelines — Sugar ≤ 25g/ngày, Sodium ≤ 1500mg/ngày.
