import types
from dataclasses import fields

import numpy as np
import pytest

import src.algorithms.dbo as dbo_mod
from src.algorithms.dbo import DBO, DBOResult

DIM = 5
LB = -5.12
UB = 5.12


def sphere(x: np.ndarray) -> float:
    return float(np.sum(np.square(x)))


def _jitter(step: float = 0.1):
    def behavior(X, *args, rng=None, **kwargs):
        return X + step * rng.standard_normal(X.shape)

    return behavior


def _big_step():
    def behavior(X, *args, **kwargs):
        return X + np.full(X.shape, 1e6)

    return behavior


def stub_behaviors(step: float = 0.1):
    return {name: _jitter(step) for name in dbo_mod.BEHAVIOR_NAMES}


def recording_behaviors(max_iter: int):
    counts = {name: 0 for name in dbo_mod.BEHAVIOR_NAMES}

    def make(name):
        def behavior(X, *args, rng=None, **kwargs):
            counts[name] += 1
            return X + 0.05 * rng.standard_normal(X.shape)

        return behavior

    return {name: make(name) for name in dbo_mod.BEHAVIOR_NAMES}, counts


def test_dboresult_has_documented_fields():
    names = [f.name for f in fields(DBOResult)]
    assert names == ["best_x", "best_fitness", "history", "n_evaluations", "runtime_s", "seed"]


def test_optimize_returns_complete_result():
    n_agents, max_iter = 8, 10
    res = DBO(n_agents=n_agents, max_iter=max_iter, behaviors=stub_behaviors()).optimize(
        sphere, DIM, LB, UB, seed=42
    )
    assert isinstance(res, DBOResult)
    assert res.best_x.shape == (DIM,)
    assert np.all(np.isfinite(res.best_x))
    assert isinstance(res.best_fitness, float) and np.isfinite(res.best_fitness)
    assert len(res.history) == max_iter + 1
    assert res.n_evaluations == n_agents * (1 + max_iter)
    assert res.runtime_s >= 0.0
    assert res.seed == 42


def test_same_seed_is_reproducible():
    run = lambda: DBO(n_agents=8, max_iter=15, behaviors=stub_behaviors()).optimize(
        sphere, DIM, LB, UB, seed=7
    )
    res1, res2 = run(), run()
    np.testing.assert_array_equal(res1.best_x, res2.best_x)
    assert res1.best_fitness == res2.best_fitness
    assert res1.history == res2.history


def test_history_is_non_increasing_and_tracks_best():
    res = DBO(n_agents=10, max_iter=20, behaviors=stub_behaviors()).optimize(
        sphere, DIM, LB, UB, seed=3
    )
    assert len(res.history) == 21
    deltas = np.diff(res.history)
    assert np.all(deltas <= 0.0)
    assert res.history[-1] == pytest.approx(res.best_fitness, abs=0.0)
    assert sphere(res.best_x) == pytest.approx(res.best_fitness, abs=1e-9)


def test_best_x_stays_within_bounds_even_with_unbounded_proposals():
    behaviors = {name: _big_step() for name in dbo_mod.BEHAVIOR_NAMES}
    res = DBO(n_agents=10, max_iter=15, behaviors=behaviors).optimize(sphere, DIM, LB, UB, seed=11)
    assert np.all(res.best_x >= LB)
    assert np.all(res.best_x <= UB)


def test_every_behaviour_group_is_used_each_iteration():
    max_iter = 5
    behaviors, counts = recording_behaviors(max_iter)
    DBO(n_agents=8, max_iter=max_iter, behaviors=behaviors).optimize(sphere, DIM, LB, UB, seed=1)
    assert counts == {name: max_iter for name in dbo_mod.BEHAVIOR_NAMES}


def test_behaviors_dict_must_cover_all_groups():
    partial = stub_behaviors()
    del partial["thieving"]
    with pytest.raises(ValueError, match="missing behaviour callables"):
        DBO(n_agents=8, max_iter=5, behaviors=partial)


def test_invalid_configuration_is_rejected():
    with pytest.raises(ValueError, match="n_agents"):
        DBO(n_agents=2)
    with pytest.raises(ValueError, match="ratios"):
        DBO(ratios={"ball_rolling": 0.6, "reproduction": 0.6, "foraging": 0.3})
    with pytest.raises(ValueError, match="missing ratio"):
        DBO(ratios={"ball_rolling": 0.5, "reproduction": 0.3})


def test_missing_behaviors_module_raises_clear_error(monkeypatch):
    def raise_importerror(name):
        raise ImportError("no module named behaviors")

    fake_importlib = types.SimpleNamespace(import_module=raise_importerror)
    monkeypatch.setattr(dbo_mod, "importlib", fake_importlib)
    with pytest.raises(RuntimeError, match="behaviours task"):
        DBO(n_agents=8, max_iter=3).optimize(sphere, DIM, LB, UB, seed=1)


def test_sphere_10d_convergence_with_real_behaviors():
    pytest.importorskip("src.algorithms.behaviors")
    res = DBO(n_agents=30, max_iter=500).optimize(sphere, 10, LB, UB, seed=42)
    assert res.best_fitness < 1e-4
