# `src/algorithms/benchmarks.py`

## Mục đích

Bộ **6 hàm benchmark chuẩn** dùng để kiểm tra và đánh giá thuật toán tối ưu (DBO/IDBO).

## Các hàm benchmark

| Hàm | Công thức | Biên | Optimum | Loại |
| :--- | :--- | :--- | :--- | :--- |
| `sphere` | `sum(x_i^2)` | `[-100, 100]` | `0` tại `(0,...,0)` | Unimodal |
| `schwefel_2_22` | `sum(|x_i|) + prod(|x_i|)` | `[-10, 10]` | `0` tại `(0,...,0)` | Unimodal |
| `rosenbrock` | `sum(100*(x_{i+1}-x_i^2)^2 + (x_i-1)^2)` | `[-30, 30]` | `0` tại `(1,...,1)` | Unimodal |
| `rastrigin` | `10D + sum(x_i^2 - 10*cos(2πx_i))` | `[-5.12, 5.12]` | `0` tại `(0,...,0)` | Multimodal |
| `ackley` | `-20*exp(-0.2*sqrt(sum(x^2)/D)) - exp(sum(cos(2πx))/D) + 20 + e` | `[-32, 32]` | `0` tại `(0,...,0)` | Multimodal |
| `griewank` | `sum(x_i^2)/4000 - prod(cos(x_i/sqrt(i))) + 1` | `[-600, 600]` | `0` tại `(0,...,0)` | Multimodal |

## Cấu trúc dữ liệu

### `BenchmarkFunction` (dataclass)

```python
@dataclass(frozen=True)
class BenchmarkFunction:
    name: str
    func: Callable
    lb: float
    ub: float
    optimum_val: float
    category: str  # "unimodal" | "multimodal"
    description: str
```

### Registry

```python
BENCHMARKS: Dict[str, BenchmarkFunction]
```

### Hàm tiện ích

| Hàm | Mô tả |
| :--- | :--- |
| `get_benchmark(name) -> BenchmarkFunction` | Lấy benchmark theo tên (case-insensitive) |
| `list_benchmarks() -> List[str]` | Liệt kê tên tất cả benchmark |

## Đánh giá

Mỗi hàm hỗ trợ:
- **Scalar**: `x` shape `(dim,)` → `float`
- **Batch**: `X` shape `(N, dim)` → `np.ndarray` shape `(N,)`

## Ghi chú

- Rosenbrock yêu cầu `dim >= 2`.
- Các hàm khác yêu cầu `dim >= 1`.

## Kiểm thử (`tests/test_benchmarks.py`)

27 bài test:
- Registry chứa đúng 6 hàm: `sphere`, `schwefel_2_22`, `rosenbrock`, `rastrigin`, `ackley`, `griewank`
- `get_benchmark()` hỗ trợ case-insensitive và loại bỏ whitespace
- `get_benchmark()` ném `ValueError` với tên không hợp lệ
- Bounds và metadata hợp lệ (`lb < ub`, `optimum_val` đúng, `category` đúng)
- Giá trị tại **known optimum** đúng với sai khác ≤ `1e-8` cho `dim = 2, 10, 30`
- Giá trị thủ công (hand-crafted) khớp công thức cho `dim = 2`
- Batch evaluation `(N, dim)` trả kết quả trùng với vòng lặp scalar
- `rosenbrock` từ chối `dim < 2`
- Empty vector từ chối
- `optimum_x()` từ chối `dim < 1`
