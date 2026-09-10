# `scripts/experiment_dbo.py`

## Mục đích

Chạy thí nghiệm **M lần lặp độc lập** DBO trên bộ benchmark, thu thập thống kê và xuất CSV.

## Luồng chạy

1. Parse CLI args: `--functions`, `--dims`, `--runs` (M), `--max-iter`, `--n-agents`, `--out-dir`, `--dry-run`.
2. Với mỗi `(hàm, dim)`:
   - Chạy `runs` lần với seed khác nhau.
   - Seed được tính: `1000 * (f_idx + 1) + 100 * (d_idx + 1) + (r + 1)`.
3. Lưu kết quả:
   - `dbo_benchmark_runs.csv`: chi tiết từng lần chạy.
   - `dbo_benchmark_summary.csv`: thống kê best/mean/std/worst.
4. In bảng tóm tắt ra console.

## Cấu trúc CSV

### `dbo_benchmark_runs.csv`

| Cột | Mô tả |
| :--- | :--- |
| `function` | Tên hàm benchmark |
| `category` | `unimodal` / `multimodal` |
| `dim` | Số chiều |
| `run` | Thứ tự lần chạy (1-based) |
| `seed` | Seed ngẫu nhiên |
| `best_fitness` | Fitness tốt nhất tìm được |
| `runtime_s` | Thời gian chạy (giây) |
| `n_evaluations` | Tổng số lần đánh giá |

### `dbo_benchmark_summary.csv`

| Cột | Mô tả |
| :--- | :--- |
| `function` | Tên hàm |
| `dim` | Số chiều |
| `runs` | Số lần chạy |
| `best` | Fitness tốt nhất trong M lần |
| `mean` | Trung bình |
| `std` | Độ lệch chuẩn |
| `worst` | Fitness tệ nhất trong M lần |

## Chạy

```bash
# Dry-run smoke test
python scripts/experiment_dbo.py --dry-run --runs 2 --dims 2 10 --max-iter 20

# Full experiment
python scripts/experiment_dbo.py --runs 30 --dims 2 10 30 --max-iter 500
```

## Output

Mặc định: `experiments/week4/`
