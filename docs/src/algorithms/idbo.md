# `src/algorithms/idbo.py`

## Mục đích

**Improved Dung Beetle Optimizer (IDBO)** — tuần 5–6. Giữ 4 hành vi DBO gốc, thêm nhiễu ngẫu nhiên và restart khi quần thể mất đa dạng.

## API

```python
IDBO(n_agents=30, max_iter=500, ..., diversity_threshold=1e-3,
     perturbation_rate=0.2, perturbation_scale=0.1,
     stagnation_window=25, restart_rate=0.25, n_elite=1)

optimize(objective, dim, lb, ub, seed=42) -> IDBOResult
```

`IDBO` kế thừa `DBO`. `IDBOResult` thêm `n_perturbations`, `n_restarts`, `diversity_history`.

## Cơ chế

1. `population_diversity(X, lb, ub)` — std trung bình theo chiều, chia span.
2. `random_perturbation` — Gauss trên agent không-elite khi diversity thấp; biên độ giảm theo `t`.
3. `random_restart` — khởi tạo lại agent tệ nhất khi diversity thấp và best đứng yên `stagnation_window` vòng.

Gọi sau mỗi iteration qua hook `DBO._after_iteration` (DBO gốc no-op).

## Kiểm thử

`tests/test_idbo.py`: diversity, elite, biên, seed, history không tăng, perturb/restart kích hoạt, Sphere 10D hội tụ.
