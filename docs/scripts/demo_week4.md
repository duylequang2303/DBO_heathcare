# `scripts/demo_week4.py`

## Mục đích

Demo chạy **1 lần DBO** trên 1 hàm benchmark, in tiến trình hội tụ và kết quả tối ưu.

## Luồng chạy

1. Parse CLI args: `--function`, `--dim`, `--n-agents`, `--max-iter`, `--seed`, `--log-every`, `--dry-run`.
2. Lấy benchmark function từ registry (`get_benchmark`).
3. Load behaviors:
   - `--dry-run`: dùng mock behaviors (di chuyển 10% về gốc + nhiễu Gaussian nhỏ).
   - Normal: import `src.algorithms.behaviors`; nếu thiếu → báo lỗi + gợi ý dùng `--dry-run`.
4. Chạy `DBO.optimize()`.
5. In lịch sử hội tụ mỗi `log_every` iterations.
6. In kết quả: `best_fitness`, `sai khac toi uu`, `n_evaluations`, `runtime_s`, `best_x`.

## Ví dụ output

```text
 Iteration    0: best fitness = 1.563090e+04
 Iteration   50: best fitness = 3.740496e-15
 ...
 Iteration  500: best fitness = 1.474124e-204

 Best fitness     : 1.47412440e-204
 Sai khac toi uu  : 1.47412440e-204
 Tong so lan eval : 15030
 Thoi gian chay   : 0.1132 s
```

## Chạy

```bash
# Dry-run (không cần behaviors.py)
python scripts/demo_week4.py --dry-run --function sphere --dim 10

# Full run (cần behaviors.py)
python scripts/demo_week4.py --function sphere --dim 10 --max-iter 500
```

## Mock behavior

```python
def _step(X, *args, rng=None, **kwargs):
    return X * 0.9 + 0.01 * rng.standard_normal(X.shape)
```
