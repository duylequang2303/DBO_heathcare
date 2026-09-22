"""Improved Dung Beetle Optimizer (IDBO) — weeks 5 and 6.

IDBO keeps the original four DBO behaviours (Xue & Shen, 2023) and adds two
randomness mechanisms aimed at population diversity and premature convergence:

1. Random perturbation — Gaussian noise on non-elite agents when diversity
   collapses, with a scale that decays over iterations.
2. Random restart — reinitialise the worst agents uniformly in ``[lb, ub]``
   after a stagnation window, while preserving elites and the global best.

The public ``optimize`` API matches ``DBO.optimize`` so week 7 can swap the
callable without touching the search loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from src.algorithms.dbo import DBO, DBOResult, Objective


def population_diversity(X: np.ndarray, lb: np.ndarray, ub: np.ndarray) -> float:
    """Mean per-dimension standard deviation, normalised by the search span.

    Returns a value in ``[0, ~0.5]``. Near-zero means the swarm has collapsed.
    """
    X = np.asarray(X, dtype=float)
    span = np.maximum(np.asarray(ub, dtype=float) - np.asarray(lb, dtype=float), 1e-12)
    return float(np.mean(np.std(X, axis=0) / span))


def elite_indices(fitness: np.ndarray, n_elite: int) -> np.ndarray:
    n = int(fitness.shape[0])
    k = int(max(1, min(n_elite, n)))
    return np.argsort(fitness)[:k]


def random_perturbation(
    X: np.ndarray,
    fitness: np.ndarray,
    rng: np.random.Generator,
    lb: np.ndarray,
    ub: np.ndarray,
    rate: float,
    scale: float,
    n_elite: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Add Gaussian noise to a fraction of non-elite agents.

    Returns ``(X_new, changed_idx)``. Elites are never moved. ``scale`` is
    relative to ``(ub - lb)``.
    """
    X = np.asarray(X, dtype=float).copy()
    fitness = np.asarray(fitness, dtype=float)
    lb = np.asarray(lb, dtype=float)
    ub = np.asarray(ub, dtype=float)
    n_agents, dim = X.shape
    protected = set(elite_indices(fitness, n_elite).tolist())
    candidates = np.array([i for i in range(n_agents) if i not in protected], dtype=int)
    if candidates.size == 0 or rate <= 0.0 or scale <= 0.0:
        return X, np.array([], dtype=int)

    n_pick = int(max(1, round(rate * n_agents)))
    n_pick = min(n_pick, int(candidates.size))
    chosen = rng.choice(candidates, size=n_pick, replace=False)
    span = np.maximum(ub - lb, 1e-12)
    noise = rng.normal(0.0, scale, size=(n_pick, dim)) * span
    X[chosen] = np.clip(X[chosen] + noise, lb, ub)
    return X, np.asarray(chosen, dtype=int)


def random_restart(
    X: np.ndarray,
    fitness: np.ndarray,
    rng: np.random.Generator,
    lb: np.ndarray,
    ub: np.ndarray,
    rate: float,
    n_elite: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Reinitialise the worst non-elite agents uniformly in ``[lb, ub]``.

    Returns ``(X_new, changed_idx)``.
    """
    X = np.asarray(X, dtype=float).copy()
    fitness = np.asarray(fitness, dtype=float)
    lb = np.asarray(lb, dtype=float)
    ub = np.asarray(ub, dtype=float)
    n_agents, dim = X.shape
    protected = set(elite_indices(fitness, n_elite).tolist())
    worst_first = [i for i in np.argsort(fitness)[::-1] if i not in protected]
    if not worst_first or rate <= 0.0:
        return X, np.array([], dtype=int)

    n_pick = int(max(1, round(rate * n_agents)))
    n_pick = min(n_pick, len(worst_first))
    chosen = np.asarray(worst_first[:n_pick], dtype=int)
    X[chosen] = rng.uniform(lb, ub, size=(n_pick, dim))
    return X, chosen


@dataclass
class IDBOResult(DBOResult):
    n_perturbations: int = 0
    n_restarts: int = 0
    diversity_history: list[float] = field(default_factory=list)


class IDBO(DBO):
    def __init__(
        self,
        n_agents: int = 30,
        max_iter: int = 500,
        ratios: Optional[dict[str, float]] = None,
        cfg: Optional[dict[str, float]] = None,
        behaviors: Optional[dict[str, Callable]] = None,
        diversity_threshold: float = 1e-3,
        perturbation_rate: float = 0.2,
        perturbation_scale: float = 0.1,
        stagnation_window: int = 25,
        restart_rate: float = 0.25,
        n_elite: int = 1,
    ) -> None:
        super().__init__(
            n_agents=n_agents,
            max_iter=max_iter,
            ratios=ratios,
            cfg=cfg,
            behaviors=behaviors,
        )
        if not 0.0 < diversity_threshold < 1.0:
            raise ValueError("diversity_threshold must be in (0, 1)")
        if not 0.0 <= perturbation_rate <= 1.0:
            raise ValueError("perturbation_rate must be in [0, 1]")
        if perturbation_scale < 0.0:
            raise ValueError("perturbation_scale must be >= 0")
        if stagnation_window < 1:
            raise ValueError("stagnation_window must be >= 1")
        if not 0.0 <= restart_rate <= 1.0:
            raise ValueError("restart_rate must be in [0, 1]")
        if n_elite < 1:
            raise ValueError("n_elite must be >= 1")
        self.diversity_threshold = float(diversity_threshold)
        self.perturbation_rate = float(perturbation_rate)
        self.perturbation_scale = float(perturbation_scale)
        self.stagnation_window = int(stagnation_window)
        self.restart_rate = float(restart_rate)
        self.n_elite = int(n_elite)
        self._stagnation = 0
        self._n_perturbations = 0
        self._n_restarts = 0
        self._diversity_history: list[float] = []
        self._prev_best: Optional[float] = None

    def optimize(
        self, objective: Objective, dim: int, lb: float, ub: float, seed: int = 42
    ) -> IDBOResult:
        self._stagnation = 0
        self._n_perturbations = 0
        self._n_restarts = 0
        self._diversity_history = []
        self._prev_best = None
        base = super().optimize(objective, dim, lb, ub, seed)
        return IDBOResult(
            best_x=base.best_x,
            best_fitness=base.best_fitness,
            history=base.history,
            n_evaluations=base.n_evaluations,
            runtime_s=base.runtime_s,
            seed=base.seed,
            n_perturbations=self._n_perturbations,
            n_restarts=self._n_restarts,
            diversity_history=list(self._diversity_history),
        )

    def _after_iteration(
        self,
        t: int,
        positions: np.ndarray,
        fitness: np.ndarray,
        best_x: np.ndarray,
        best_fitness: float,
        rng: np.random.Generator,
        lbv: np.ndarray,
        ubv: np.ndarray,
        objective: Objective,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, int]:
        extra_evals = 0
        diversity = population_diversity(positions, lbv, ubv)
        self._diversity_history.append(diversity)

        if self._prev_best is None or best_fitness < self._prev_best - 1e-15:
            self._stagnation = 0
        else:
            self._stagnation += 1
        self._prev_best = best_fitness

        collapsed = diversity < self.diversity_threshold
        do_restart = (
            collapsed
            and self.restart_rate > 0.0
            and self._stagnation >= self.stagnation_window
        )
        if do_restart:
            positions, idx = random_restart(
                positions,
                fitness,
                rng,
                lbv,
                ubv,
                rate=self.restart_rate,
                n_elite=self.n_elite,
            )
            if idx.size:
                new_f = self._evaluate(objective, positions[idx])
                extra_evals += int(idx.size)
                fitness[idx] = new_f
                self._n_restarts += 1
                self._stagnation = 0
                k = int(np.argmin(fitness))
                if fitness[k] < best_fitness:
                    best_fitness = float(fitness[k])
                    best_x = positions[k].copy()
            return positions, fitness, best_x, best_fitness, extra_evals

        if collapsed:
            scale_t = self.perturbation_scale * (1.0 - (t - 1) / max(self.max_iter, 1))
            positions, idx = random_perturbation(
                positions,
                fitness,
                rng,
                lbv,
                ubv,
                rate=self.perturbation_rate,
                scale=max(scale_t, 0.0),
                n_elite=self.n_elite,
            )
            if idx.size:
                new_f = self._evaluate(objective, positions[idx])
                extra_evals += int(idx.size)
                fitness[idx] = new_f
                self._n_perturbations += 1
                k = int(np.argmin(fitness))
                if fitness[k] < best_fitness:
                    best_fitness = float(fitness[k])
                    best_x = positions[k].copy()

        return positions, fitness, best_x, best_fitness, extra_evals
