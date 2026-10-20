"""Threshold Calibration: Testing diversity_threshold = 0.25, 0.28, 0.32 on seeds 8001, 8002.

Calibrates the sensitivity of IDBO perturbation and restart mechanisms under
realistic diversity ranges before locking configuration for full benchmark.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import sys
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.menu_objective import decode_result
from src.algorithms.two_tier_solver import TwoTierConfig, two_tier_optimize
from src.models.constraints import validate_menu
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets


def get_profile_p1() -> UserProfile:
    return UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        weight_kg=65.0,
        height_cm=170.0,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        diet_type=DietType.STANDARD,
        meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 2},
        allergies=[],
        dislikes=[],
        likes=[],
    )


def run_single(
    algo: str,
    seed: int,
    diversity_threshold: float,
    outer_max_iter: int = 100,
    stagnation_window: int = 10,
    perturbation_rate: float = 0.2,
    restart_rate: float = 0.25,
    outer_n_agents: int = 10,
    inner_max_iter: int = 25,
    inner_n_agents: int = 10,
) -> Dict[str, Any]:
    df_food = load_food_db()
    food_map = build_food_map(df_food)
    profile = get_profile_p1()
    targets = daily_all_targets(profile)

    cfg = TwoTierConfig(
        outer_algo=algo,
        outer_n_agents=outer_n_agents,
        outer_max_iter=outer_max_iter,
        inner_algo=algo,
        inner_n_agents=inner_n_agents,
        inner_max_iter=inner_max_iter,
        seed=seed,
        stagnation_window=stagnation_window,
        diversity_threshold=diversity_threshold,
        perturbation_rate=perturbation_rate,
        restart_rate=restart_rate,
    )

    t0 = time.perf_counter()
    result = two_tier_optimize(profile, food_map, targets, cfg)
    runtime_s = time.perf_counter() - t0

    menu = decode_result(result.best_food_ids, result.best_portions_g, food_map, profile.meal_counts)
    violations = validate_menu(menu, profile, targets)
    cals = menu.total("calories")

    final_fitness = result.history[-1] if result.history else result.best_fitness

    return {
        "algo": algo,
        "diversity_threshold": diversity_threshold,
        "seed": seed,
        "outer_max_iter": outer_max_iter,
        "stagnation_window": stagnation_window,
        "best_fitness": round(float(result.best_fitness), 4),
        "final_fitness": round(float(final_fitness), 4),
        "runtime_s": round(float(runtime_s), 2),
        "n_evaluations": result.outer_evals + result.inner_evals_total,
        "outer_min_diversity": round(float(result.outer_min_diversity), 4),
        "outer_mean_diversity": round(float(result.outer_mean_diversity), 4),
        "outer_final_diversity": round(float(result.outer_final_diversity), 4),
        "outer_max_stagnation": int(result.outer_max_stagnation),
        "outer_collapse_events": int(result.outer_collapse_events),
        "outer_perturbations": int(result.outer_perturbations),
        "outer_restarts": int(result.outer_restarts),
        "final_inner_perturbations": int(result.final_inner_perturbations),
        "final_inner_restarts": int(result.final_inner_restarts),
        "inner_perturbations_total": int(result.inner_perturbations_total),
        "inner_restarts_total": int(result.inner_restarts_total),
        "calories": round(float(cals), 2),
        "n_violations": len(violations),
    }


def _worker_wrapper(args: tuple) -> Dict[str, Any]:
    return run_single(*args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate diversity threshold on seeds 8001, 8002")
    parser.add_argument("--thresholds", nargs="+", type=float, default=[0.25, 0.28, 0.32], help="List of diversity thresholds to test")
    parser.add_argument("--seeds", nargs="+", type=int, default=[8001, 8002], help="Seeds to test")
    parser.add_argument("--outer-iter", type=int, default=100, help="Outer iterations (default: 100)")
    parser.add_argument("--stagnation-window", type=int, default=10, help="Stagnation window (default: 10)")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker processes")
    parser.add_argument("--output", type=Path, default=Path("experiments/ablation_dbo_idbo/threshold_calibration_2seeds.csv"), help="Output CSV path")
    args = parser.parse_args()

    print("=" * 80)
    print("DIVERSITY THRESHOLD CALIBRATION ON SEEDS 8001 & 8002")
    print(f"Thresholds: {args.thresholds} | Seeds: {args.seeds}")
    print(f"Outer Iter: {args.outer_iter} | Stagnation Window: {args.stagnation_window} | Workers: {args.workers}")
    print("=" * 80)

    tasks = []
    # 1. Add DBO baseline for each seed
    for seed in args.seeds:
        tasks.append(("dbo", seed, 0.001, args.outer_iter, args.stagnation_window))

    # 2. Add IDBO for each threshold and seed
    for th in args.thresholds:
        for seed in args.seeds:
            tasks.append(("idbo", seed, th, args.outer_iter, args.stagnation_window))

    total = len(tasks)
    print(f"\n[INFO] Launching {total} calibration tasks across {args.workers} workers...\n")

    t0 = time.perf_counter()
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(_worker_wrapper, t): t for t in tasks}
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            print(
                f"[{completed:02d}/{total:02d}] {res['algo'].upper():<4} (th={res['diversity_threshold']:.3f}) | "
                f"Seed {res['seed']} -> Fit: {res['best_fitness']:>7.4f} | "
                f"MinDiv: {res['outer_min_diversity']:.3f} | MeanDiv: {res['outer_mean_diversity']:.3f} | "
                f"MaxStag: {res['outer_max_stagnation']:>2} | CollapseEv: {res['outer_collapse_events']:>2} | "
                f"Pert: {res['outer_perturbations']:>2} | Rest: {res['outer_restarts']:>2} | "
                f"Time: {res['runtime_s']:>4.1f}s",
                flush=True,
            )

    elapsed = time.perf_counter() - t0
    print(f"\n[INFO] All {total} calibration runs completed in {elapsed:.1f}s!")

    df = pd.DataFrame(results)
    df.sort_values(by=["seed", "algo", "diversity_threshold"], ascending=[True, True, True], inplace=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False, encoding="utf-8")
    print(f"[SAVED] Results saved to {args.output}")

    # Build comparison display against DBO baseline
    print("\n" + "=" * 90)
    print("CALIBRATION SUMMARY TABLE (PAIRED BY SEED)")
    print("=" * 90)
    dbo_map = {}
    for r in results:
        if r["algo"] == "dbo":
            dbo_map[r["seed"]] = r["best_fitness"]

    rows = []
    for r in results:
        seed = r["seed"]
        dbo_fit = dbo_map.get(seed, None)
        diff = round(r["best_fitness"] - dbo_fit, 4) if dbo_fit is not None else 0.0
        rows.append({
            "algo": r["algo"].upper(),
            "threshold": r["diversity_threshold"],
            "seed": seed,
            "best_fitness": r["best_fitness"],
            "diff_vs_dbo": diff,
            "runtime_s": r["runtime_s"],
            "min_diversity": r["outer_min_diversity"],
            "mean_diversity": r["outer_mean_diversity"],
            "max_stagnation": r["outer_max_stagnation"],
            "collapse_events": r["outer_collapse_events"],
            "outer_pert": r["outer_perturbations"],
            "outer_rest": r["outer_restarts"],
            "inner_pert_total": r["inner_perturbations_total"],
            "inner_rest_total": r["inner_restarts_total"],
            "violations": r["n_violations"],
        })

    summary_df = pd.DataFrame(rows)
    summary_df.sort_values(by=["seed", "threshold"], inplace=True)
    print(summary_df.to_string(index=False))
    print("=" * 90)


if __name__ == "__main__":
    main()
