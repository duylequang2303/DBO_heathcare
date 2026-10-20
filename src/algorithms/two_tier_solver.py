"""Two-Tier Mixed-Integer Optimizer for Healthcare Menu Generation.

Architecture:
- Outer Tier: DBO / IDBO optimizes discrete food selection vector z in [0, 1)^k.
  z is decoded to valid food_ids across meal slots using candidate food pools.
- Inner Tier: DBO / IDBO optimizes continuous portion sizes x in [25, 350]^k (grams)
  for the food_ids proposed by the Outer Tier.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from src.algorithms.dbo import DBO
from src.algorithms.idbo import IDBO
from src.algorithms.menu_objective import make_menu_objective
from src.models.food_selector import (
    build_meal_pools,
    decode_food_selection,
    get_meal_order_slots,
)
from src.models.user_profile import UserProfile
from src.models.dish_category import classify_dish_role, get_role_portion_bounds


@dataclass
class TwoTierConfig:
    """Configuration parameters for Two-Tier Optimization."""

    outer_algo: str = "idbo"  # "dbo" | "idbo"
    outer_n_agents: int = 20
    outer_max_iter: int = 100
    inner_algo: str = "idbo"  # "dbo" | "idbo"
    inner_n_agents: int = 15
    inner_max_iter: int = 50
    seed: int = 8000
    min_pool_size: int = 20
    # IDBO specific parameters
    diversity_threshold: float = 1e-3
    stagnation_window: int = 25
    perturbation_rate: float = 0.2
    perturbation_scale: float = 0.1
    restart_rate: float = 0.25
    n_elite: int = 1


@dataclass
class TwoTierResult:
    """Output result from Two-Tier Optimization."""

    best_food_ids: list[str]
    best_portions_g: np.ndarray
    best_fitness: float  # True fitness in range [-100, 100] (higher is better)
    history: list[float]  # Outer convergence history in true fitness
    outer_evals: int
    inner_evals_total: int
    runtime_s: float
    outer_perturbations: int = 0
    outer_restarts: int = 0
    final_inner_perturbations: int = 0
    final_inner_restarts: int = 0
    inner_perturbations_total: int = 0
    inner_restarts_total: int = 0
    outer_min_diversity: float = 0.0
    outer_mean_diversity: float = 0.0
    outer_final_diversity: float = 0.0
    outer_max_stagnation: int = 0
    outer_collapse_events: int = 0
    final_inner_min_diversity: float = 0.0
    final_inner_max_stagnation: int = 0


def two_tier_optimize(
    profile: UserProfile,
    food_map: dict,
    targets: dict,
    config: Optional[TwoTierConfig] = None,
) -> TwoTierResult:
    """Run two-tier mixed-integer optimization.

    Args:
        profile: Target user profile with nutritional and meal requirements.
        food_map: Full dictionary of food items keyed by food_id.
        targets: Nutrient target dictionary (calories, macros, fiber, micros).
        config: TwoTierConfig configuration instance.

    Returns:
        TwoTierResult containing best foods, portions, fitness, and metrics.
    """
    if config is None:
        config = TwoTierConfig()

    outer_algo = config.outer_algo.strip().lower()
    if outer_algo not in ("dbo", "idbo"):
        raise ValueError(f"Unsupported outer_algo: '{config.outer_algo}'. Must be 'dbo' or 'idbo'.")
    inner_algo = config.inner_algo.strip().lower()
    if inner_algo not in ("dbo", "idbo"):
        raise ValueError(f"Unsupported inner_algo: '{config.inner_algo}'. Must be 'dbo' or 'idbo'.")

    t_start = time.perf_counter()

    # 1. Build candidate food pools and slot ordering
    pools = build_meal_pools(
        food_map=food_map,
        meal_counts=profile.meal_counts,
        profile=profile,
        min_pool_size=config.min_pool_size,
    )
    meal_order = get_meal_order_slots(profile.meal_counts)
    dim_k = len(meal_order)

    inner_evals_counter = [0]
    inner_perturbations_counter = [0]
    inner_restarts_counter = [0]
    eval_call_idx = [0]

    def portion_bounds(food_ids: list[str]) -> tuple[np.ndarray, np.ndarray]:
        bounds = []
        for food_id in food_ids:
            food = food_map[food_id]
            role = classify_dish_role(
                str(food.get("food_name", "")), str(food.get("category", "")), str(food.get("source", ""))
            )
            bounds.append(get_role_portion_bounds(role))
        return (
            np.asarray([low for low, _ in bounds], dtype=float),
            np.asarray([high for _, high in bounds], dtype=float),
        )

    # 2. Define outer objective function (minimized by outer optimizer)
    def outer_objective(z: np.ndarray) -> float:
        # Decode continuous vector z into valid food_ids
        food_ids = decode_food_selection(z, pools, meal_order)

        # Build inner continuous objective
        inner_obj = make_menu_objective(profile, food_ids, food_map, targets)

        # Configure inner optimizer
        inner_seed = (config.seed + eval_call_idx[0] * 101 + 7) % 2147483647
        eval_call_idx[0] += 1

        if inner_algo == "dbo":
            inner_solver = DBO(
                n_agents=config.inner_n_agents,
                max_iter=config.inner_max_iter,
            )
        else:
            inner_solver = IDBO(
                n_agents=config.inner_n_agents,
                max_iter=config.inner_max_iter,
                diversity_threshold=config.diversity_threshold,
                stagnation_window=config.stagnation_window,
                perturbation_rate=config.perturbation_rate,
                perturbation_scale=config.perturbation_scale,
                restart_rate=config.restart_rate,
                n_elite=config.n_elite,
            )

        inner_lb, inner_ub = portion_bounds(food_ids)
        inner_res = inner_solver.optimize(
            inner_obj,
            dim=dim_k,
            lb=inner_lb,
            ub=inner_ub,
            seed=inner_seed,
        )
        inner_evals_counter[0] += inner_res.n_evaluations
        inner_perturbations_counter[0] += int(getattr(inner_res, "n_perturbations", 0))
        inner_restarts_counter[0] += int(getattr(inner_res, "n_restarts", 0))

        # Return inner best fitness (already negated by make_menu_objective)
        return float(inner_res.best_fitness)

    # 3. Configure and execute outer optimizer
    if outer_algo == "dbo":
        outer_solver = DBO(
            n_agents=config.outer_n_agents,
            max_iter=config.outer_max_iter,
        )
    else:
        outer_solver = IDBO(
            n_agents=config.outer_n_agents,
            max_iter=config.outer_max_iter,
            diversity_threshold=config.diversity_threshold,
            stagnation_window=config.stagnation_window,
            perturbation_rate=config.perturbation_rate,
            perturbation_scale=config.perturbation_scale,
            restart_rate=config.restart_rate,
            n_elite=config.n_elite,
        )

    outer_res = outer_solver.optimize(
        outer_objective,
        dim=dim_k,
        lb=0.0,
        ub=1.0 - 1e-9,
        seed=config.seed,
    )

    # 4. Final decoding and portion refinement
    best_food_ids = decode_food_selection(outer_res.best_x, pools, meal_order)
    final_inner_obj = make_menu_objective(profile, best_food_ids, food_map, targets)

    if inner_algo == "dbo":
        final_inner_solver = DBO(
            n_agents=config.inner_n_agents,
            max_iter=config.inner_max_iter,
        )
    else:
        final_inner_solver = IDBO(
            n_agents=config.inner_n_agents,
            max_iter=config.inner_max_iter,
            diversity_threshold=config.diversity_threshold,
            stagnation_window=config.stagnation_window,
            perturbation_rate=config.perturbation_rate,
            perturbation_scale=config.perturbation_scale,
            restart_rate=config.restart_rate,
            n_elite=config.n_elite,
        )

    final_lb, final_ub = portion_bounds(best_food_ids)
    final_res = final_inner_solver.optimize(
        final_inner_obj,
        dim=dim_k,
        lb=final_lb,
        ub=final_ub,
        seed=config.seed,
    )
    inner_evals_counter[0] += final_res.n_evaluations

    runtime_s = time.perf_counter() - t_start

    # History in true fitness scale (higher is better)
    true_history = [-float(val) for val in outer_res.history]
    true_best_fitness = -float(final_res.best_fitness)

    return TwoTierResult(
        best_food_ids=best_food_ids,
        best_portions_g=final_res.best_x,
        best_fitness=true_best_fitness,
        history=true_history,
        outer_evals=outer_res.n_evaluations,
        inner_evals_total=inner_evals_counter[0],
        runtime_s=runtime_s,
        outer_perturbations=int(getattr(outer_res, "n_perturbations", 0)),
        outer_restarts=int(getattr(outer_res, "n_restarts", 0)),
        final_inner_perturbations=int(getattr(final_res, "n_perturbations", 0)),
        final_inner_restarts=int(getattr(final_res, "n_restarts", 0)),
        inner_perturbations_total=inner_perturbations_counter[0],
        inner_restarts_total=inner_restarts_counter[0],
        outer_min_diversity=float(getattr(outer_res, "min_diversity", 0.0)),
        outer_mean_diversity=float(getattr(outer_res, "mean_diversity", 0.0)),
        outer_final_diversity=float(getattr(outer_res, "final_diversity", 0.0)),
        outer_max_stagnation=int(getattr(outer_res, "max_stagnation", 0)),
        outer_collapse_events=int(getattr(outer_res, "n_collapse_events", 0)),
        final_inner_min_diversity=float(getattr(final_res, "min_diversity", 0.0)),
        final_inner_max_stagnation=int(getattr(final_res, "max_stagnation", 0)),
    )
