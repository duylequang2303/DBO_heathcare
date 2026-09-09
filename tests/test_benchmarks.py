import numpy as np
import pytest

from src.algorithms.benchmarks import (
    BENCHMARKS,
    BenchmarkFunction,
    ackley,
    get_benchmark,
    griewank,
    list_benchmarks,
    rastrigin,
    rosenbrock,
    schwefel_2_22,
    sphere,
)

EXPECTED_BENCHMARK_NAMES = [
    "sphere",
    "schwefel_2_22",
    "rosenbrock",
    "rastrigin",
    "ackley",
    "griewank",
]


def test_registry_contains_expected_benchmarks():
    names = list_benchmarks()
    assert sorted(names) == sorted(EXPECTED_BENCHMARK_NAMES)
    for name in EXPECTED_BENCHMARK_NAMES:
        bench = get_benchmark(name)
        assert isinstance(bench, BenchmarkFunction)
        assert bench.name == name


def test_get_benchmark_case_insensitive_and_whitespace():
    bench1 = get_benchmark("  Sphere  ")
    bench2 = get_benchmark("SPHERE")
    assert bench1.name == "sphere"
    assert bench2.name == "sphere"


def test_get_benchmark_unknown_raises_value_error():
    with pytest.raises(ValueError, match="Unknown benchmark function"):
        get_benchmark("nonexistent_func")


def test_bounds_and_metadata_validity():
    for name, bench in BENCHMARKS.items():
        assert bench.lb < bench.ub
        assert bench.category in ("unimodal", "multimodal")
        assert bench.optimum_val == 0.0
        assert len(bench.description) > 0


@pytest.mark.parametrize("name", EXPECTED_BENCHMARK_NAMES)
@pytest.mark.parametrize("dim", [2, 10, 30])
def test_optimum_value_at_known_optimum(name, dim):
    bench = get_benchmark(name)
    x_opt = bench.optimum_x(dim)
    assert x_opt.shape == (dim,)
    val = bench(x_opt)
    assert isinstance(val, float)
    assert val == pytest.approx(bench.optimum_val, abs=1e-8)


def test_manual_values_dim2_sphere():
    val = sphere(np.array([2.0, 3.0]))
    assert val == pytest.approx(13.0, abs=1e-12)


def test_manual_values_dim2_schwefel_2_22():
    # sum(|x|) = 2 + 3 = 5; prod(|x|) = 2 * 3 = 6; total = 11
    val = schwefel_2_22(np.array([2.0, -3.0]))
    assert val == pytest.approx(11.0, abs=1e-12)


def test_manual_values_dim2_rosenbrock():
    # x = [1, 2]: 100 * (2 - 1^2)^2 + (1 - 1)^2 = 100 * 1 = 100
    val1 = rosenbrock(np.array([1.0, 2.0]))
    assert val1 == pytest.approx(100.0, abs=1e-12)

    # x = [-1, 2]: 100 * (2 - 1)^2 + (-1 - 1)^2 = 100 + 4 = 104
    val2 = rosenbrock(np.array([-1.0, 2.0]))
    assert val2 == pytest.approx(104.0, abs=1e-12)


def test_manual_values_dim2_rastrigin():
    # x = [0, 1]: 10*2 + (0 - 10*cos(0)) + (1 - 10*cos(2pi))
    # = 20 + (-10) + (1 - 10) = 20 - 10 - 9 = 1.0
    val = rastrigin(np.array([0.0, 1.0]))
    assert val == pytest.approx(1.0, abs=1e-12)


def test_manual_values_dim2_ackley():
    # At origin, value is exactly 0.0
    val = ackley(np.array([0.0, 0.0]))
    assert val == pytest.approx(0.0, abs=1e-12)


def test_manual_values_dim2_griewank():
    # At origin, value is exactly 0.0
    val1 = griewank(np.array([0.0, 0.0]))
    assert val1 == pytest.approx(0.0, abs=1e-12)

    # x = [pi, pi*sqrt(2)]:
    # sum_sq / 4000 = (pi^2 + 2*pi^2)/4000 = 3*pi^2/4000
    # prod_cos = cos(pi/1) * cos(pi*sqrt(2)/sqrt(2)) = cos(pi) * cos(pi) = (-1)*(-1) = 1.0
    # val = 3*pi^2/4000 - 1.0 + 1.0 = 3*pi^2/4000
    val2 = griewank(np.array([np.pi, np.pi * np.sqrt(2.0)]))
    expected = (3.0 * (np.pi ** 2)) / 4000.0
    assert val2 == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("name", EXPECTED_BENCHMARK_NAMES)
def test_vectorized_batch_equals_scalar_evaluations(name):
    bench = get_benchmark(name)
    dim = 5
    n_samples = 8
    rng = np.random.default_rng(42)
    batch = rng.uniform(bench.lb, bench.ub, size=(n_samples, dim))

    batch_result = bench(batch)
    assert isinstance(batch_result, np.ndarray)
    assert batch_result.shape == (n_samples,)

    scalar_results = np.array([bench(batch[i]) for i in range(n_samples)], dtype=float)
    np.testing.assert_allclose(batch_result, scalar_results, rtol=1e-10, atol=1e-10)


def test_rosenbrock_rejects_dimension_less_than_2():
    with pytest.raises(ValueError, match="requires dimension >= 2"):
        rosenbrock(np.array([1.0]))

    bench = get_benchmark("rosenbrock")
    with pytest.raises(ValueError, match="requires dim >= 2"):
        bench.optimum_x(1)


def test_empty_vector_rejects():
    with pytest.raises(ValueError, match="Dimension must be at least 1"):
        sphere(np.array([]))
