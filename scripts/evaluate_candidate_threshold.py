"""Independent Evaluation of Candidate Diversity Threshold (th=0.28).

Evaluates IDBO with candidate diversity_threshold = 0.28 against DBO on:
- Calibration set: seeds 8001-8002
- Independent evaluation set: seeds 8003-8010 (8 hold-out seeds)

Tracks:
- best_fitness, final_fitness, runtime_s
- outer_min_diversity, outer_mean_diversity, outer_final_diversity
- outer_max_stagnation, outer_collapse_events
- outer_perturbations, outer_restarts
- inner_perturbations_total, inner_restarts_total
- calories, n_violations
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
    diversity_threshold: float = 0.28,
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
        "diversity_threshold": diversity_threshold if algo == "idbo" else 0.0,
        "seed": seed,
        "set_type": "calibration" if seed in [8001, 8002] else "independent_eval",
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
    parser = argparse.ArgumentParser(description="Evaluate candidate diversity threshold 0.28")
    parser.add_argument("--threshold", type=float, default=0.28, help="Candidate diversity threshold (default: 0.28)")
    parser.add_argument("--outer-iter", type=int, default=100, help="Outer iterations (default: 100)")
    parser.add_argument("--stagnation-window", type=int, default=10, help="Stagnation window (default: 10)")
    parser.add_argument("--workers", type=int, default=6, help="Worker processes (default: 6)")
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/ablation_dbo_idbo"), help="Output directory")
    args = parser.parse_args()

    all_seeds = list(range(8001, 8011))
    print("=" * 85)
    print(f"EVALUATING CANDIDATE THRESHOLD = {args.threshold:.2f} (10 SEEDS)")
    print(f"Calibration Set: [8001, 8002] | Independent Eval Set: {list(range(8003, 8011))}")
    print(f"Outer Iterations: {args.outer_iter} | Stagnation Window: {args.stagnation_window} | Workers: {args.workers}")
    print("=" * 85)

    tasks = []
    for seed in all_seeds:
        for algo in ["dbo", "idbo"]:
            tasks.append((algo, seed, args.threshold, args.outer_iter, args.stagnation_window))

    total = len(tasks)
    print(f"\n[INFO] Launching {total} paired runs across {args.workers} workers...\n")

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
                f"[{completed:02d}/{total:02d}] {res['algo'].upper():<4} | Seed {res['seed']} ({res['set_type'][:5]}) -> "
                f"Fit: {res['best_fitness']:>7.4f} | MinDiv: {res['outer_min_diversity']:.3f} | "
                f"MaxStag: {res['outer_max_stagnation']:>2} | Collapse: {res['outer_collapse_events']:>2} | "
                f"Pert: {res['outer_perturbations']:>2} | Rest: {res['outer_restarts']:>2} | "
                f"Time: {res['runtime_s']:>4.1f}s",
                flush=True,
            )

    elapsed = time.perf_counter() - t0
    print(f"\n[INFO] All {total} runs completed in {elapsed:.1f}s!")

    runs_df = pd.DataFrame(results)
    runs_df.sort_values(by=["seed", "algo"], inplace=True)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_csv = args.output_dir / "candidate_threshold_028_eval.csv"
    runs_df.to_csv(raw_csv, index=False, encoding="utf-8")
    print(f"[SAVED] Raw run data: {raw_csv}")

    # Compute paired differences per seed
    diff_rows = []
    for seed in all_seeds:
        dbo_r = runs_df[(runs_df["seed"] == seed) & (runs_df["algo"] == "dbo")].iloc[0]
        idbo_r = runs_df[(runs_df["seed"] == seed) & (runs_df["algo"] == "idbo")].iloc[0]

        diff_fit = round(float(idbo_r["best_fitness"] - dbo_r["best_fitness"]), 4)
        diff_rt = round(float(idbo_r["runtime_s"] - dbo_r["runtime_s"]), 2)

        if abs(diff_fit) < 1e-4:
            outcome = "TIE"
        elif diff_fit > 0:
            outcome = "IDBO_WIN"
        else:
            outcome = "DBO_WIN"

        diff_rows.append({
            "seed": seed,
            "set_type": "calibration" if seed in [8001, 8002] else "independent_eval",
            "dbo_fitness": dbo_r["best_fitness"],
            "idbo_fitness": idbo_r["best_fitness"],
            "diff_fitness": diff_fit,
            "dbo_runtime_s": dbo_r["runtime_s"],
            "idbo_runtime_s": idbo_r["runtime_s"],
            "diff_runtime_s": diff_rt,
            "idbo_min_diversity": idbo_r["outer_min_diversity"],
            "idbo_mean_diversity": idbo_r["outer_mean_diversity"],
            "idbo_max_stagnation": idbo_r["outer_max_stagnation"],
            "idbo_collapse_events": idbo_r["outer_collapse_events"],
            "idbo_outer_pert": idbo_r["outer_perturbations"],
            "idbo_outer_rest": idbo_r["outer_restarts"],
            "idbo_inner_pert_total": idbo_r["inner_perturbations_total"],
            "idbo_inner_rest_total": idbo_r["inner_restarts_total"],
            "dbo_violations": dbo_r["n_violations"],
            "idbo_violations": idbo_r["n_violations"],
            "outcome": outcome,
        })

    diff_df = pd.DataFrame(diff_rows)
    diff_csv = args.output_dir / "candidate_threshold_028_diffs.csv"
    diff_df.to_csv(diff_csv, index=False, encoding="utf-8")
    print(f"[SAVED] Paired differences: {diff_csv}")

    # Segment analyses
    cal_diff = diff_df[diff_df["set_type"] == "calibration"]
    ind_diff = diff_df[diff_df["set_type"] == "independent_eval"]

    print("\n" + "=" * 95)
    print("PAIRED RUN RESULTS TABLE (ALL 10 SEEDS)")
    print("=" * 95)
    print(diff_df[["seed", "set_type", "dbo_fitness", "idbo_fitness", "diff_fitness", "dbo_runtime_s", "idbo_runtime_s", "diff_runtime_s", "idbo_collapse_events", "idbo_outer_pert", "idbo_outer_rest", "outcome"]].to_string(index=False))
    print("=" * 95)

    print("\n" + "=" * 95)
    print("INDEPENDENT EVALUATION SET SUMMARY (SEEDS 8003 - 8010, N=8)")
    print("=" * 95)
    n_wins = int((ind_diff["outcome"] == "IDBO_WIN").sum())
    n_ties = int((ind_diff["outcome"] == "TIE").sum())
    n_losses = int((ind_diff["outcome"] == "DBO_WIN").sum())
    mean_diff = float(ind_diff["diff_fitness"].mean())
    median_diff = float(ind_diff["diff_fitness"].median())
    mean_rt_inc = float(ind_diff["diff_runtime_s"].mean())
    pct_rt_inc = float(mean_rt_inc / ind_diff["dbo_runtime_s"].mean() * 100)

    print(f"Wins / Ties / Losses       : {n_wins} Wins / {n_ties} Ties / {n_losses} Losses")
    print(f"Mean Paired Difference (Fit): {mean_diff:+.4f} points")
    print(f"Median Paired Difference   : {median_diff:+.4f} points")
    print(f"Mean Runtime Increase       : +{mean_rt_inc:.2f}s (+{pct_rt_inc:.1f}%)")
    print(f"Mean Outer Perturbations   : {ind_diff['idbo_outer_pert'].mean():.1f}")
    print(f"Mean Outer Restarts        : {ind_diff['idbo_outer_rest'].mean():.1f}")
    print(f"Mean Collapse Events       : {ind_diff['idbo_collapse_events'].mean():.1f}")
    print(f"Mean Min Diversity (IDBO)  : {ind_diff['idbo_min_diversity'].mean():.4f}")
    print(f"Mean Total Violations      : DBO={ind_diff['dbo_violations'].mean():.1f}, IDBO={ind_diff['idbo_violations'].mean():.1f}")
    print("=" * 95)

    print("\n" + "=" * 95)
    print("CALIBRATION SET SUMMARY (SEEDS 8001 - 8002, N=2)")
    print("=" * 95)
    cal_wins = int((cal_diff["outcome"] == "IDBO_WIN").sum())
    cal_ties = int((cal_diff["outcome"] == "TIE").sum())
    cal_losses = int((cal_diff["outcome"] == "DBO_WIN").sum())
    print(f"Wins / Ties / Losses       : {cal_wins} Wins / {cal_ties} Ties / {cal_losses} Losses")
    print(f"Mean Paired Difference (Fit): {cal_diff['diff_fitness'].mean():+.4f} points")
    print(f"Mean Runtime Increase       : +{cal_diff['diff_runtime_s'].mean():.2f}s")
    print("=" * 95)


if __name__ == "__main__":
    main()
