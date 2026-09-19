import numpy as np
import pytest

from src.algorithms.dbo import DBO, DBOResult, BEHAVIOR_NAMES
from src.algorithms.idbo import (
    IDBO,
    IDBOResult,
    elite_indices,
    population_diversity,
    random_perturbation,
    random_restart,
)


DIM = 5
LB = -5.12
UB = 5.12


def sphere(x: np.ndarray) -> float:
    return float(np.sum(np.square(x)))


def rastrigin(x: np.ndarray) -> float:
    arr = np.asarray(x, dtype=float)
    dim = arr.shape[-1]
    return float(10.0 * dim + np.sum(np.square(arr) - 10.0 * np.cos(2.0 * np.pi * arr)))


def _jitter(step: float = 0.1):
    def behavior(X, *args, rng=None, **kwargs):
        return X + step * rng.standard_normal(X.shape)

    return behavior


def stub_behaviors(step: float = 0.1):
    return {name: _jitter(step) for name in BEHAVIOR_NAMES}


def test_idbo_is_dbo_subclass():
    assert issubclass(IDBO, DBO)
    assert issubclass(IDBOResult, DBOResult)


def test_population_diversity_is_zero_when_collapsed():
    X = np.ones((8, 4))
    lb = np.full(4, -10.0)
    ub = np.full(4, 10.0)
    assert population_diversity(X, lb, ub) == pytest.approx(0.0, abs=1e-15)


def test_population_diversity_is_positive_for_spread_swarm():
    rng = np.random.default_rng(0)
    lb = np.full(3, -5.0)
    ub = np.full(3, 5.0)
    X = rng.uniform(lb, ub, size=(20, 3))
    assert population_diversity(X, lb, ub) > 0.05


def test_elite_indices_protects_best_agents():
    fitness = np.array([4.0, 0.1, 3.0, 0.2, 9.0])
    idx = elite_indices(fitness, 2)
    assert set(idx.tolist()) == {1, 3}


def test_random_perturbation_never_moves_elites():
    rng = np.random.default_rng(1)
    X = np.arange(24, dtype=float).reshape(6, 4)
    fitness = np.array([5.0, 0.1, 4.0, 3.0, 2.0, 1.0])
    lb = np.full(4, -100.0)
    ub = np.full(4, 100.0)
    elite = elite_indices(fitness, 1)
    X_new, changed = random_perturbation(X, fitness, rng, lb, ub, rate=1.0, scale=0.5, n_elite=1)
    assert elite[0] not in set(changed.tolist())
    np.testing.assert_array_equal(X_new[elite[0]], X[elite[0]])
    assert changed.size == 5


def test_random_perturbation_stays_inside_bounds():
    rng = np.random.default_rng(2)
    X = np.zeros((10, 3))
    fitness = np.linspace(0.0, 1.0, 10)
    lb = np.full(3, -1.0)
    ub = np.full(3, 1.0)
    X_new, _ = random_perturbation(X, fitness, rng, lb, ub, rate=1.0, scale=5.0, n_elite=1)
    assert np.all(X_new >= lb)
    assert np.all(X_new <= ub)


def test_random_restart_replaces_worst_not_elites():
    rng = np.random.default_rng(3)
    X = np.zeros((8, 2))
    fitness = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    lb = np.array([-10.0, -10.0])
    ub = np.array([10.0, 10.0])
    X_new, changed = random_restart(X, fitness, rng, lb, ub, rate=0.25, n_elite=1)
    assert 0 not in set(changed.tolist())
    assert changed.size == 2
    assert set(changed.tolist()) == {7, 6}
    assert not np.allclose(X_new[changed], 0.0)
    np.testing.assert_array_equal(X_new[0], X[0])
    assert np.all(X_new >= lb) and np.all(X_new <= ub)


def test_idbo_invalid_config_is_rejected():
    with pytest.raises(ValueError, match="diversity_threshold"):
        IDBO(diversity_threshold=0.0)
    with pytest.raises(ValueError, match="perturbation_rate"):
        IDBO(perturbation_rate=1.5)
    with pytest.raises(ValueError, match="stagnation_window"):
        IDBO(stagnation_window=0)
    with pytest.raises(ValueError, match="n_elite"):
        IDBO(n_elite=0)


def test_idbo_optimize_returns_extended_result():
    n_agents, max_iter = 8, 12
    res = IDBO(n_agents=n_agents, max_iter=max_iter, behaviors=stub_behaviors()).optimize(
        sphere, DIM, LB, UB, seed=42
    )
    assert isinstance(res, IDBOResult)
    assert res.best_x.shape == (DIM,)
    assert len(res.history) == max_iter + 1
    assert len(res.diversity_history) == max_iter
    assert res.n_perturbations >= 0
    assert res.n_restarts >= 0
    assert res.n_evaluations >= n_agents * (1 + max_iter)
    assert np.all(res.best_x >= LB) and np.all(res.best_x <= UB)


def test_idbo_same_seed_is_reproducible():
    def run():
        return IDBO(n_agents=8, max_iter=15, behaviors=stub_behaviors()).optimize(
            sphere, DIM, LB, UB, seed=7
        )

    res1, res2 = run(), run()
    np.testing.assert_array_equal(res1.best_x, res2.best_x)
    assert res1.best_fitness == res2.best_fitness
    assert res1.history == res2.history
    assert res1.n_perturbations == res2.n_perturbations
    assert res1.n_restarts == res2.n_restarts
    assert res1.diversity_history == res2.diversity_history


def test_idbo_history_is_non_increasing():
    res = IDBO(n_agents=10, max_iter=20, behaviors=stub_behaviors()).optimize(
        sphere, DIM, LB, UB, seed=3
    )
    assert np.all(np.diff(res.history) <= 0.0)
    assert res.history[-1] == pytest.approx(res.best_fitness, abs=0.0)


def test_idbo_perturbation_fires_when_diversity_collapses():
    collapsed = np.full((8, DIM), 0.01)

    def freeze(X, *args, rng=None, **kwargs):
        return np.broadcast_to(collapsed[0], X.shape).copy()

    behaviors = {name: freeze for name in BEHAVIOR_NAMES}
    opt = IDBO(
        n_agents=8,
        max_iter=6,
        behaviors=behaviors,
        diversity_threshold=0.2,
        perturbation_rate=0.5,
        perturbation_scale=0.3,
        stagnation_window=100,
        restart_rate=0.0,
        n_elite=1,
    )
    res = opt.optimize(sphere, DIM, LB, UB, seed=11)
    assert res.n_perturbations >= 1
    assert res.n_restarts == 0


def test_idbo_restart_fires_after_stagnation_window():
    collapsed = np.full((8, DIM), 0.01)

    def freeze(X, *args, rng=None, **kwargs):
        return np.broadcast_to(collapsed[0], X.shape).copy()

    behaviors = {name: freeze for name in BEHAVIOR_NAMES}
    opt = IDBO(
        n_agents=8,
        max_iter=8,
        behaviors=behaviors,
        diversity_threshold=0.2,
        perturbation_rate=0.0,
        perturbation_scale=0.0,
        stagnation_window=2,
        restart_rate=0.5,
        n_elite=1,
    )
    res = opt.optimize(sphere, DIM, LB, UB, seed=13)
    assert res.n_restarts >= 1


def test_idbo_disabled_mechanisms_match_dbo_when_not_triggered():
    behaviors = stub_behaviors(0.05)
    dbo = DBO(n_agents=8, max_iter=10, behaviors=behaviors).optimize(sphere, DIM, LB, UB, seed=21)
    idbo = IDBO(
        n_agents=8,
        max_iter=10,
        behaviors=behaviors,
        diversity_threshold=1e-12,
        perturbation_rate=0.0,
        restart_rate=0.0,
        stagnation_window=10_000,
    ).optimize(sphere, DIM, LB, UB, seed=21)
    np.testing.assert_allclose(dbo.best_x, idbo.best_x)
    assert dbo.best_fitness == idbo.best_fitness
    assert dbo.history == idbo.history
    assert idbo.n_perturbations == 0
    assert idbo.n_restarts == 0


def test_idbo_sphere_10d_still_converges():
    pytest.importorskip("src.algorithms.behaviors")
    res = IDBO(n_agents=30, max_iter=400).optimize(sphere, 10, LB, UB, seed=42)
    assert res.best_fitness < 1e-4


def test_idbo_rastrigin_does_not_lose_best():
    pytest.importorskip("src.algorithms.behaviors")
    res = IDBO(
        n_agents=20,
        max_iter=80,
        diversity_threshold=1e-3,
        perturbation_rate=0.2,
        restart_rate=0.2,
        stagnation_window=15,
    ).optimize(rastrigin, 5, -5.12, 5.12, seed=5)
    assert np.all(np.diff(res.history) <= 1e-12)
    assert res.best_fitness == pytest.approx(res.history[-1], abs=0.0)
