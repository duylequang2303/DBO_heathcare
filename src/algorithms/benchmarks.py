"""Standard mathematical benchmark functions for metaheuristic optimization.

Implements classic benchmark functions used in Xue & Shen (2023) (Dung Beetle Optimizer)
and IEEE CEC benchmarks:
- Sphere (F1, Unimodal)
- Schwefel 2.22 (F2, Unimodal)
- Rosenbrock (F5, Valley / Unimodal)
- Rastrigin (F9, Multimodal)
- Ackley (F10, Multimodal)
- Griewank (F11, Multimodal)

Each function supports both 1D array evaluation `(dim,) -> float` and
vectorized 2D batch evaluation `(N, dim) -> (N,)`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Union

import numpy as np


# ---------------------------------------------------------------------------
# Individual mathematical functions
# ---------------------------------------------------------------------------

def sphere(x: np.ndarray) -> Union[float, np.ndarray]:
    r"""Sphere function (F1): f(x) = \sum_{i=1}^D x_i^2.

    Search bounds: [-100, 100].
    Global minimum: f(0, ..., 0) = 0.
    """
    arr = np.asarray(x, dtype=float)
    if arr.shape[-1] < 1:
        raise ValueError("Dimension must be at least 1")
    val = np.sum(np.square(arr), axis=-1)
    return float(val) if arr.ndim == 1 else val


def schwefel_2_22(x: np.ndarray) -> Union[float, np.ndarray]:
    r"""Schwefel 2.22 function (F2): f(x) = \sum_{i=1}^D |x_i| + \prod_{i=1}^D |x_i|.

    Search bounds: [-10, 10].
    Global minimum: f(0, ..., 0) = 0.
    """
    arr = np.asarray(x, dtype=float)
    if arr.shape[-1] < 1:
        raise ValueError("Dimension must be at least 1")
    abs_arr = np.abs(arr)
    sum_abs = np.sum(abs_arr, axis=-1)
    prod_abs = np.prod(abs_arr, axis=-1)
    val = sum_abs + prod_abs
    return float(val) if arr.ndim == 1 else val


def rosenbrock(x: np.ndarray) -> Union[float, np.ndarray]:
    r"""Rosenbrock function (F5): f(x) = \sum_{i=1}^{D-1} [100(x_{i+1} - x_i^2)^2 + (x_i - 1)^2].

    Search bounds: [-30, 30].
    Global minimum: f(1, ..., 1) = 0.
    Requires dimension >= 2.
    """
    arr = np.asarray(x, dtype=float)
    if arr.shape[-1] < 2:
        raise ValueError("Rosenbrock function requires dimension >= 2")
    x_i = arr[..., :-1]
    x_next = arr[..., 1:]
    term1 = 100.0 * np.square(x_next - np.square(x_i))
    term2 = np.square(x_i - 1.0)
    val = np.sum(term1 + term2, axis=-1)
    return float(val) if arr.ndim == 1 else val


def rastrigin(x: np.ndarray) -> Union[float, np.ndarray]:
    r"""Rastrigin function (F9): f(x) = 10D + \sum_{i=1}^D [x_i^2 - 10 \cos(2\pi x_i)].

    Search bounds: [-5.12, 5.12].
    Global minimum: f(0, ..., 0) = 0.
    """
    arr = np.asarray(x, dtype=float)
    dim = arr.shape[-1]
    if dim < 1:
        raise ValueError("Dimension must be at least 1")
    val = 10.0 * dim + np.sum(np.square(arr) - 10.0 * np.cos(2.0 * np.pi * arr), axis=-1)
    return float(val) if arr.ndim == 1 else val


def ackley(x: np.ndarray) -> Union[float, np.ndarray]:
    r"""Ackley function (F10):
    f(x) = -20 \exp(-0.2 \sqrt{\frac{1}{D} \sum x_i^2}) - \exp(\frac{1}{D} \sum \cos(2\pi x_i)) + 20 + e.

    Search bounds: [-32, 32].
    Global minimum: f(0, ..., 0) = 0.
    """
    arr = np.asarray(x, dtype=float)
    dim = arr.shape[-1]
    if dim < 1:
        raise ValueError("Dimension must be at least 1")
    sum_sq = np.sum(np.square(arr), axis=-1)
    sum_cos = np.sum(np.cos(2.0 * np.pi * arr), axis=-1)
    term1 = -20.0 * np.exp(-0.2 * np.sqrt(sum_sq / dim))
    term2 = -np.exp(sum_cos / dim)
    val = term1 + term2 + 20.0 + np.e
    return float(val) if arr.ndim == 1 else val


def griewank(x: np.ndarray) -> Union[float, np.ndarray]:
    r"""Griewank function (F11): f(x) = \frac{1}{4000} \sum x_i^2 - \prod \cos(\frac{x_i}{\sqrt{i}}) + 1.

    Search bounds: [-600, 600].
    Global minimum: f(0, ..., 0) = 0.
    """
    arr = np.asarray(x, dtype=float)
    dim = arr.shape[-1]
    if dim < 1:
        raise ValueError("Dimension must be at least 1")
    indices = np.sqrt(np.arange(1, dim + 1, dtype=float))
    sum_sq = np.sum(np.square(arr), axis=-1) / 4000.0
    prod_cos = np.prod(np.cos(arr / indices), axis=-1)
    val = sum_sq - prod_cos + 1.0
    return float(val) if arr.ndim == 1 else val


# ---------------------------------------------------------------------------
# BenchmarkFunction Metadata and Registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BenchmarkFunction:
    """Represents an optimization benchmark function with metadata."""

    name: str
    func: Callable[[np.ndarray], Union[float, np.ndarray]]
    lb: float
    ub: float
    optimum_val: float
    category: str  # "unimodal" | "multimodal"
    description: str = ""

    def __call__(self, x: np.ndarray) -> Union[float, np.ndarray]:
        return self.func(x)

    def optimum_x(self, dim: int) -> np.ndarray:
        """Returns the known global optimum coordinates for dimension `dim`."""
        if self.name == "rosenbrock":
            if dim < 2:
                raise ValueError("Rosenbrock optimum requires dim >= 2")
            return np.ones(dim, dtype=float)
        return np.zeros(dim, dtype=float)


BENCHMARKS: Dict[str, BenchmarkFunction] = {
    "sphere": BenchmarkFunction(
        name="sphere",
        func=sphere,
        lb=-100.0,
        ub=100.0,
        optimum_val=0.0,
        category="unimodal",
        description="Sphere function: f(x) = sum(x_i^2)",
    ),
    "schwefel_2_22": BenchmarkFunction(
        name="schwefel_2_22",
        func=schwefel_2_22,
        lb=-10.0,
        ub=10.0,
        optimum_val=0.0,
        category="unimodal",
        description="Schwefel 2.22: f(x) = sum(|x_i|) + prod(|x_i|)",
    ),
    "rosenbrock": BenchmarkFunction(
        name="rosenbrock",
        func=rosenbrock,
        lb=-30.0,
        ub=30.0,
        optimum_val=0.0,
        category="unimodal",
        description="Rosenbrock: f(x) = sum(100*(x_{i+1}-x_i^2)^2 + (x_i-1)^2)",
    ),
    "rastrigin": BenchmarkFunction(
        name="rastrigin",
        func=rastrigin,
        lb=-5.12,
        ub=5.12,
        optimum_val=0.0,
        category="multimodal",
        description="Rastrigin: f(x) = 10*D + sum(x_i^2 - 10*cos(2*pi*x_i))",
    ),
    "ackley": BenchmarkFunction(
        name="ackley",
        func=ackley,
        lb=-32.0,
        ub=32.0,
        optimum_val=0.0,
        category="multimodal",
        description="Ackley: f(x) = -20*exp(-0.2*sqrt(sum(x^2)/D)) - exp(sum(cos(2pi*x))/D) + 20 + e",
    ),
    "griewank": BenchmarkFunction(
        name="griewank",
        func=griewank,
        lb=-600.0,
        ub=600.0,
        optimum_val=0.0,
        category="multimodal",
        description="Griewank: f(x) = sum(x_i^2)/4000 - prod(cos(x_i/sqrt(i))) + 1",
    ),
}


def get_benchmark(name: str) -> BenchmarkFunction:
    """Retrieve benchmark function by name (case-insensitive)."""
    key = name.strip().lower()
    if key not in BENCHMARKS:
        available = ", ".join(sorted(BENCHMARKS.keys()))
        raise ValueError(f"Unknown benchmark function '{name}'. Available: {available}")
    return BENCHMARKS[key]


def list_benchmarks() -> List[str]:
    """Return list of all registered benchmark function names."""
    return list(BENCHMARKS.keys())
