# `scripts/experiment_idbo.py`

So sánh DBO vs IDBO trên bộ 6 hàm tuần 4. Cùng `n_agents`, `max_iter`, bộ seed.

```bash
python scripts/experiment_idbo.py --runs 3 --dims 10 30 --max-iter 80 --functions sphere rastrigin
python scripts/experiment_idbo.py --runs 30 --dims 10 30 50 --max-iter 500
```

CSV (không commit): `experiments/week5_6/idbo_vs_dbo_runs.csv`, `idbo_vs_dbo_summary.csv`.
