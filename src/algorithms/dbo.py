"""Original Dung Beetle Optimizer (DBO) framework, Xue & Shen (2023).

The optimizer is decoupled from any objective function: ``optimize`` only
receives a callable ``objective(x: np.ndarray) -> float`` together with the
search space (``dim``, ``lb``, ``ub``).  The four behaviour groups
(ball-rolling, reproduction, foraging, thieving) live in ``behaviors.py``
and are loaded lazily at run time so this framework can be developed,
tested and merged independently of the behaviour implementations.

Function signatures of the behaviour group follow the frozen contract in
docs/TASK_WEEK4.md (do not change them without team agreement).
"""

from __future__ import annotations

import importlib
import time
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

Objective = Callable[[np.ndarray], float]

BEHAVIOR_NAMES = ("ball_rolling", "reproduction", "foraging", "thieving")

# Population proportion of each behaviour group. The remaining share is
# assigned to the thieving group. Ratios reproduce the reference DBO demo
# (Xue & Shen, 2022) at pop = 30: 6 ball-rolling / 6 reproduction /
# 7 foraging / 11 thieving beetles.
DEFAULT_RATIOS = {
    "ball_rolling": 0.2,
    "reproduction": 0.2,
    "foraging": 7.0 / 30.0,
}

BEHAVIORS_MODULE = "src.algorithms.behaviors"


@dataclass
class DBOResult:
    best_x: np.ndarray
    best_fitness: float
    history: list[float]
    n_evaluations: int
    runtime_s: float
    seed: int


class DBO:
    def __init__(
        self,
        n_agents: int = 30,
        max_iter: int = 500,
        ratios: Optional[dict[str, float]] = None,
        cfg: Optional[dict] = None,
        behaviors: Optional[dict[str, Callable]] = None,
    ) -> None:
        if n_agents < 4:
            raise ValueError("n_agents must be at least 4 (one per behaviour group)")
        if max_iter < 1:
            raise ValueError("max_iter must be >= 1")
        self.n_agents = n_agents
        self.max_iter = max_iter
        self.ratios = dict(DEFAULT_RATIOS if ratios is None else ratios)
        self.cfg = dict(cfg or {})
        self._validate_ratios(self.ratios)
        if behaviors is not None:
            missing = [n for n in BEHAVIOR_NAMES if n not in behaviors]
            if missing:
                raise ValueError(f"missing behaviour callables: {missing}")
        self._behaviors = behaviors
        self._behaviors_module = None

    def optimize(
        self, objective: Objective, dim: int, lb: float, ub: float, seed: int = 42
    ) -> DBOResult:
        start = time.perf_counter()
        rng = np.random.default_rng(seed)
        lbv = np.broadcast_to(np.asarray(lb, dtype=float), (dim,)).astype(float)
        ubv = np.broadcast_to(np.asarray(ub, dtype=float), (dim,)).astype(float)
        if np.any(lbv >= ubv):
            raise ValueError("lb must be strictly smaller than ub for every dimension")

        positions = rng.uniform(lbv, ubv, size=(self.n_agents, dim))
        fitness = self._evaluate(objective, positions)
        n_evaluations = self.n_agents
        best_i = int(np.argmin(fitness))
        best_x = positions[best_i].copy()
        best_fitness = float(fitness[best_i])
        history = [best_fitness]

        behaviors = self._resolve_behaviors()
        groups = self._partition(self.n_agents)
        for t in range(1, self.max_iter + 1):
            worst_x = positions[int(np.argmax(fitness))].copy()
            for name, idx in zip(BEHAVIOR_NAMES, groups):
                if len(idx) == 0:
                    continue
                fn = behaviors[name]
                group_x = positions[idx]
                group_f = fitness[idx]
                if name == "ball_rolling":
                    new_x = fn(group_x, group_f, best_x, rng=rng, worst=worst_x, **self.cfg)
                elif name in ("reproduction", "foraging"):
                    new_x = fn(group_x, best_x, lbv, ubv, t, self.max_iter, rng=rng, **self.cfg)
                else:
                    new_x = fn(group_x, best_x, rng=rng, **self.cfg)
                new_x = np.clip(new_x, lbv, ubv)
                new_f = self._evaluate(objective, new_x)
                n_evaluations += len(idx)
                improved = new_f < group_f
                if np.any(improved):
                    positions[idx[improved]] = new_x[improved]
                    fitness[idx[improved]] = new_f[improved]
                    k = int(np.argmin(new_f))
                    if new_f[k] < best_fitness:
                        best_fitness = float(new_f[k])
                        best_x = new_x[k].copy()
            history.append(best_fitness)

        runtime_s = time.perf_counter() - start
        return DBOResult(
            best_x=best_x,
            best_fitness=best_fitness,
            history=history,
            n_evaluations=n_evaluations,
            runtime_s=runtime_s,
            seed=seed,
        )

    def _resolve_behaviors(self) -> dict[str, Callable]:
        if self._behaviors is not None:
            return self._behaviors
        if self._behaviors_module is None:
            try:
                module = importlib.import_module(BEHAVIORS_MODULE)
            except ImportError as exc:
                raise RuntimeError(
                    f"cannot find behaviour module '{BEHAVIORS_MODULE}'; "
                    "it is provided by the behaviours task (see TASK_WEEK4.md)"
                ) from exc
            missing = [n for n in BEHAVIOR_NAMES if not hasattr(module, n)]
            if missing:
                raise RuntimeError(f"behaviour module is missing functions: {missing}")
            self._behaviors_module = module
        return {n: getattr(self._behaviors_module, n) for n in BEHAVIOR_NAMES}

    def _partition(self, n: int) -> list[np.ndarray]:
        counts = [
            int(round(n * self.ratios["ball_rolling"])),
            int(round(n * self.ratios["reproduction"])),
            int(round(n * self.ratios["foraging"])),
        ]
        counts.append(n - sum(counts))
        if any(c < 1 for c in counts):
            raise ValueError(
                "population size too small for the configured behaviour ratios "
                "(every group needs at least one agent)"
            )
        boundaries = np.cumsum([0] + counts)
        return [np.arange(boundaries[i], boundaries[i + 1]) for i in range(len(counts))]

    @staticmethod
    def _validate_ratios(ratios: dict[str, float]) -> None:
        for name in ("ball_rolling", "reproduction", "foraging"):
            if name not in ratios:
                raise ValueError(f"missing ratio for behaviour group '{name}'")
            if not 0.0 < ratios[name] < 1.0:
                raise ValueError(f"ratio '{name}' must be in (0, 1)")
        if sum(ratios[name] for name in ("ball_rolling", "reproduction", "foraging")) >= 1.0:
            raise ValueError("ball_rolling + reproduction + foraging ratios must be < 1")

    @staticmethod
    def _evaluate(objective: Objective, X: np.ndarray) -> np.ndarray:
        values = np.empty(X.shape[0], dtype=float)
        for i in range(X.shape[0]):
            values[i] = objective(X[i])
        return values
