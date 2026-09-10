# `src/algorithms/dbo.py`

## Mục đích

Khung thuật toán **Dung Beetle Optimizer (DBO) gốc** theo Xue & Shen (2023).

Thuật toán **tách rời** khỏi bài toán cụ thể: chỉ nhận `objective(x) -> float`, không biết về thực đơn hay benchmark.

## Cấu trúc chính

### `DBOResult` (dataclass)

| Trường | Kiểu | Mô tả |
| :--- | :--- | :--- |
| `best_x` | `np.ndarray` | Vị trí tốt nhất tìm được |
| `best_fitness` | `float` | Giá trị fitness tốt nhất |
| `history` | `list[float]` | Lịch sử best fitness qua các iteration |
| `n_evaluations` | `int` | Tổng số lần đánh giá objective |
| `runtime_s` | `float` | Thời gian chạy (giây) |
| `seed` | `int` | Seed ngẫu nhiên đã dùng |

### `DBO` (class)

#### Constructor

```python
DBO(n_agents=30, max_iter=500, ratios=None, cfg=None, behaviors=None)
```

- `n_agents`: số bọ trong quần thể (≥4, mỗi nhóm hành vi cần ≥1)
- `max_iter`: số vòng lặp
- `ratios`: tỷ lệ quần thể mỗi nhóm hành vi
- `cfg`: tham số chung cho behaviors
- `behaviors`: dict `{name: callable}` để inject behaviors (dùng cho test)

#### `optimize(objective, dim, lb, ub, seed=42) -> DBOResult`

1. Khởi tạo quần thể ngẫu nhiên đều trong `[lb, ub]`
2. Vòng lặp `max_iter`:
   - Chia quần thể thành 4 nhóm hành vi
   - Mỗi nhóm gọi behavior tương ứng
   - Greedy acceptance: chỉ thay thế nếu fitness tốt hơn
   - Cập nhật `best` toàn cục, ghi `history`
3. Trả về `DBOResult`

### Tỷ lệ nhóm hành vi (mặc định)

```python
DEFAULT_RATIOS = {
    "ball_rolling": 0.2,
    "reproduction": 0.2,
    "foraging": 7.0 / 30.0,  # ~0.233
    # thieving: phần còn lại (~0.367)
}
```

### Hợp đồng behaviors

4 hàm trong `behaviors.py`:
- `ball_rolling(X, f, best, rng, **cfg)`
- `reproduction(X, best, lb, ub, t, max_iter, rng, **cfg)`
- `foraging(X, best, lb, ub, t, max_iter, rng, **cfg)`
- `thieving(X, best, rng, **cfg)`

### Đánh giá vector hóa

`_evaluate()` thử gọi `objective(X)` với batch 2D; nếu trả về vector dài `n_agents` thì dùng trực tiếp, ngược lại fallback về vòng lặp từng dòng.

## Kiểm thử (`tests/test_dbo.py`)

11 bài test:
- `DBOResult` có đủ các trường đã định nghĩa (`best_x`, `best_fitness`, `history`, `n_evaluations`, `runtime_s`, `seed`)
- `optimize()` trả `DBOResult` hoàn chỉnh, `history` dài `max_iter + 1`
- Cùng `seed` → kết quả lặp lại được (reproducibility)
- `history` không tăng (non-increasing), theo dõi best fitness
- `best_x` nằm trong `[lb, ub]` ngay cả khi behavior đề xuất giá trị ngoài biên
- Mỗi iteration dùng đủ 4 nhóm hành vi (không nhóm nào bị bỏ sót)
- `behaviors` dict phải cover đủ 4 nhóm, thiếu → `ValueError`
- Cấu hình không hợp lệ (`n_agents < 4`, `max_iter < 1`, ratios tổng ≥ 1) → `ValueError`
- Thiếu module `behaviors` → `RuntimeError` rõ ràng
- Hỗ trợ cả objective vectorized (batch) và scalar (từng dòng)
- `ball_rolling` nhận `X_prev` đúng (vị trí iteration trước)
