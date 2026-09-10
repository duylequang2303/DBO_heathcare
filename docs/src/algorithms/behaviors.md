# `src/algorithms/behaviors.py`

## Mục đích

Triển khai **4 hành vi DBO** theo đúng công thức bài báo Xue & Shen (2023).

Tất cả hàm nhận `rng: np.random.Generator` để tái lập ngẫu nhiên.

## Các hành vi

### `ball_rolling(X, f, best, rng, **cfg) -> np.ndarray`

**Ball rolling + dancing** (Eq. 1, 2).

**Tham số:**
- `X`: vị trí hiện tại nhóm, shape `(n_agents, dim)`
- `f`: fitness tương ứng, shape `(n_agents,)`
- `best`: vị trí tốt nhất toàn cục, shape `(dim,)`
- `rng`: random generator
- `cfg`: `k` (0.1), `b` (0.3), `X_prev`, `worst`, `obstacle_prob` (0.1), `obstacle_mask`

**Thuật toán:**
- `alpha = ±1` ngẫu nhiên
- **Rolling:** `X + alpha * k * X_prev + b * |X - worst|`
- **Dancing:** nếu gặp vật cản → `X + tan(theta) * |X - X_prev|` với `theta ~ U(0, π)`

### `reproduction(X, best, lb, ub, t, max_iter, rng, **cfg) -> np.ndarray`

**Vùng đẻ trứng co dần** (Eq. 3, 4).

- `R = 1 - t / max_iter`
- Vùng sinh: `[best * (1 - R), best * (1 + R)]` clip về `[lb, ub]`
- `offspring = best + b1 * (X - Lb*) + b2 * (X - Ub*)`

### `foraging(X, best, lb, ub, t, max_iter, rng, **cfg) -> np.ndarray`

**Tìm kiếm thức ăn** (Eq. 5, 6).

- Tương tự reproduction nhưng dùng Gaussian `C1` và uniform `C2`.
- `result = X + C1 * (X - Lbb) + C2 * (X - Ubb)`

### `thieving(X, best, rng, **cfg) -> np.ndarray`

**Bọ trộm bám best** (Eq. 7).

- `S = 0.5` (mặc định)
- `g ~ N(0, 1)`
- `result = best + S * g * (|X - local_best| + |X - best|)`

## Tham số mặc định theo bài báo

```python
k = 0.1   # ball-rolling
b = 0.3   # ball-rolling
S = 0.5   # thieving
```

## Ghi chú

- **Không** clip biên trong behaviors; `dbo.py` lo việc đó.
- **Không** dùng vòng lặp Python cho vector; toàn bộ vector hóa NumPy.
- Dim lấy từ `X.shape`, không hardcode.

## Kiểm thử (`tests/test_dbo.py`)

Các behavior được kiểm tra gián tiếp qua `tests/test_dbo.py`:
- `ball_rolling` nhận `X_prev` đúng (vị trí iteration trước)
- `reproduction` / `foraging` nhận `lb`, `ub`, `t`, `max_iter` đúng signature
- `thieving` chỉ cần `X`, `best`, `rng`
- Tất cả behavior đều nhận `rng` để tái lập
- Kết quả nằm trong biên `[lb, ub]` sau khi `dbo.py` clip
