# `src/models/objective.py`

## Mục đích

Tính fitness (điểm đánh giá) cho một thực đơn, cân bằng giữa:
- Đáp ứng dinh dưỡng (energy, macros)
- Sở thích người dùng (preference)
- Đa dạng món ăn (diversity)
- Phạt vi phạm ràng buộc

## Công thức fitness

```text
fitness = 0.35*energy + 0.30*macros + 0.20*preference + 0.15*diversity
          - min(90, 12 * so_vi_pham)
```

- Mỗi thành phần con nằm trong `[0, 100]`.
- Fitness được clamp về `[-100, 100]`.

## Trọng số

```python
WEIGHTS = {
    "energy": 0.35,
    "macros": 0.30,
    "preference": 0.20,
    "diversity": 0.15,
}
PENALTY_PER_VIOLATION = 12.0   # mỗi lỗi vi phạm trừ 12 điểm
MAX_PENALTY = 90.0             # tối đa trừ 90 điểm
FITNESS_MIN = -100.0
FITNESS_MAX = 100.0
```

## Các hàm thành phần

### `_energy_score(menu, calorie_target) -> float`

```python
100.0 * max(0.0, 1.0 - abs(total - target) / target)
```

### `_macro_score(menu, targets) -> float`

Trung bình harmonic của 4 macro (protein, carbs, fat, fiber), mỗi cái tính tương tự energy.

### `_preference_score(menu, profile) -> float`

- `dislike_score = 100 * (1 - disliked / total_items)`
- `like_score = 100 * liked / total_items`
- Kết hợp: `0.6 * dislike_score + 0.4 * like_score`

### `_diversity_score(menu) -> float`

```python
100.0 * len(unique_names) / len(items)
```

## API

| Hàm | Mô tả |
| :--- | :--- |
| `evaluate(menu, profile, targets) -> float` | Trả fitness đơn thuần |
| `evaluate_breakdown(menu, profile, targets) -> dict` | Trả dict chi tiết: `energy`, `macros`, `preference`, `diversity`, `weighted`, `penalty`, `n_violations`, `fitness` |

## Kiểm thử (`tests/test_objective.py`)

4 bài test:
- Trọng số (`energy 0.35 + macros 0.30 + preference 0.20 + diversity 0.15`) cộng lại đúng `1.0`
- Fitness nằm trong `[-100, 100]` đối với menu hợp lệ và menu ngẫu nhiên
- `preference` giảm khi có món trong `dislikes`
- `diversity = 100` khi tất cả món khác nhau
