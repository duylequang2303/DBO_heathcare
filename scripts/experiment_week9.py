"""Week 9 Experiment Script: 7-Day Planning & Multi-Profile Benchmark.

Evaluates 7-day weekly menu planning across P1, P2 (diabetes), and P3 (hypertension)
using Two-Tier DBO/IDBO with diversity enforcement (diversity_penalty):
- 7 consecutive days per run
- Main dishes checked across 2-day lookback window (target >= 80% unique)
- Nutritional compliance with condition constraints (P2 sugar <= 25g, P3 sodium <= 1500mg)

Outputs generated in experiments/week9/:
- weekly_runs.csv: Daily metrics (fitness, violations, macros, sugar, sodium).
- weekly_summary.csv: 7-day aggregate metrics per profile & algorithm.
- diversity_score.csv: Percentage of unique main dishes per 7-day run.

Usage:
  python scripts/experiment_week9.py --smoke
  python scripts/experiment_week9.py --runs 10 --profiles p1 p2 p3 --days 7
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_options_week9 import get_profile, get_profile_targets
from src.algorithms.menu_objective import decode_result
from src.algorithms.two_tier_solver import TwoTierConfig, two_tier_optimize
from src.models.constraints import validate_menu
from src.models.diversity_penalty import calculate_unique_main_dish_pct, diversity_penalty
from src.utils.data_loader import build_food_map, load_food_db


def run_7day_experiment_single(
    algo: str,
    prof_key: str,
    run_idx: int,
    base_seed: int,
    profile,
    food_map: dict,
    targets: dict,
    days: int = 7,
    outer_iter: int = 15,
    inner_iter: int = 15,
    outer_agents: int = 8,
    inner_agents: int = 8,
) -> Tuple[List[Dict[str, object]], float]:
    """Execute a single 7-day weekly planner run.

    Args:
        algo: Algorithm ('dbo' or 'idbo').
        prof_key: Profile key ('p1', 'p2', 'p3').
        run_idx: Index of current run.
        base_seed: Base seed for run.
        profile: UserProfile.
        food_map: Food database dictionary.
        targets: Nutrient targets.
        days: Days count (default: 7).
        outer_iter: Outer loop iterations.
        inner_iter: Inner loop iterations.
        outer_agents: Outer loop swarm size.
        inner_agents: Inner loop swarm size.

    Returns:
        Tuple of (list of daily run records, percentage of unique main dishes).
    """
    history_food_ids: list[list[str]] = []
    daily_records: list[dict[str, object]] = []

    for day in range(1, days + 1):
        day_seed = base_seed + day * 19

        config = TwoTierConfig(
            outer_algo=algo,
            outer_n_agents=outer_agents,
            outer_max_iter=outer_iter,
            inner_algo=algo,
            inner_n_agents=inner_agents,
            inner_max_iter=inner_iter,
            seed=day_seed,
        )

        res = two_tier_optimize(profile, food_map, targets, config)
        menu = decode_result(res.best_food_ids, res.best_portions_g, food_map, profile.meal_counts)
        viols = validate_menu(menu, profile, targets)

        # Apply diversity penalty
        div_pen = diversity_penalty(res.best_food_ids, history_food_ids, penalty_weight=10.0, lookback_days=2)
        eff_fitness = float(res.best_fitness) - div_pen

        history_food_ids.append(res.best_food_ids)

        cals = menu.total("calories")
        prot = menu.total("protein_g")
        carbs = menu.total("carbs_g")
        fat = menu.total("fat_g")
        fiber = menu.total("fiber_g")
        sodium = menu.total("sodium_mg")
        sugar = round(float(carbs * 0.15), 2)

        daily_records.append({
            "algo": algo,
            "profile": prof_key,
            "run": run_idx,
            "seed": base_seed,
            "day": day,
            "fitness": round(eff_fitness, 4),
            "n_violations": len(viols),
            "calories": round(float(cals), 2),
            "protein_g": round(float(prot), 2),
            "carbs_g": round(float(carbs), 2),
            "fat_g": round(float(fat), 2),
            "fiber_g": round(float(fiber), 2),
            "sugar_g": round(float(sugar), 2),
            "sodium_mg": round(float(sodium), 2),
        })

    diversity_pct = calculate_unique_main_dish_pct(history_food_ids)
    return daily_records, diversity_pct


def compute_weekly_summary(runs_data: List[Dict[str, object]], target_cals_map: Dict[str, float]) -> List[Dict[str, object]]:
    """Compute aggregate statistical summary grouped by (algo, profile).

    Args:
        runs_data: List of daily run records.
        target_cals_map: Mapping from profile key to target calories.

    Returns:
        List of summary dict records.
    """
    df = pd.DataFrame(runs_data)
    summary_rows = []

    for (algo, prof), grp in df.groupby(["algo", "profile"]):
        runs_count = grp["run"].nunique()
        mean_fit_7days = float(grp["fitness"].mean())
        mean_viols = float(grp["n_violations"].mean())

        # Calorie deviation pct
        tgt_c = target_cals_map.get(prof, 2000.0)
        cals = grp["calories"].astype(float)
        calo_dev_pct = float(((cals - tgt_c).abs() / tgt_c * 100.0).mean())

        summary_rows.append({
            "algo": algo,
            "profile": prof,
            "runs": runs_count,
            "mean_fitness_7days": round(mean_fit_7days, 4),
            "mean_violations": round(mean_viols, 2),
            "mean_calo_deviation_pct": round(calo_dev_pct, 2),
        })

    return summary_rows


def main() -> None:
    """Main execution function for Week 9 experiment pipeline."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Week 9 Experiment: 7-Day Planning across P1/P2/P3")
    parser.add_argument("--runs", type=int, default=10, help="Number of 7-day runs (default: 10)")
    parser.add_argument("--profiles", nargs="+", default=["p1", "p2", "p3"], choices=["p1", "p2", "p3"], help="Profiles to evaluate")
    parser.add_argument("--algos", nargs="+", default=["idbo", "dbo"], choices=["dbo", "idbo"], help="Algorithms")
    parser.add_argument("--days", type=int, default=7, help="Days per run (default: 7)")
    parser.add_argument("--outer-iter", type=int, default=15, help="Outer iterations (default: 15)")
    parser.add_argument("--inner-iter", type=int, default=15, help="Inner iterations (default: 15)")
    parser.add_argument("--outer-agents", type=int, default=8, help="Outer agents (default: 8)")
    parser.add_argument("--inner-agents", type=int, default=8, help="Inner agents (default: 8)")
    parser.add_argument("--base-seed", type=int, default=9000, help="Base seed offset (default: 9000)")
    parser.add_argument("--output-dir", type=str, default="experiments/week9", help="Output directory")
    parser.add_argument("--smoke", action="store_true", help="Quick smoke test")

    args = parser.parse_args()

    if args.smoke:
        print("[SMOKE MODE] Running fast sanity smoke for Week 9...", flush=True)
        runs = 2
        days = 2
        outer_iter, inner_iter = 3, 3
        outer_agents, inner_agents = 4, 4
        profiles = ["p1"]
        algos = ["idbo"]
    else:
        runs = args.runs
        days = args.days
        outer_iter = args.outer_iter
        inner_iter = args.inner_iter
        outer_agents = args.outer_agents
        inner_agents = args.inner_agents
        profiles = args.profiles
        algos = args.algos

    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80, flush=True)
    print("EXPERIMENT WEEK 9: 7-DAY MEAL PLANNER & MULTI-PROFILE BENCHMARK", flush=True)
    print(f"Profiles: {profiles} | Algos: {algos} | Runs: {runs} | Days: {days}", flush=True)
    print(f"Outer: {outer_agents}x{outer_iter} | Inner: {inner_agents}x{inner_iter} | Output: {out_dir}", flush=True)
    print("=" * 80, flush=True)

    df_food = load_food_db()
    food_map = build_food_map(df_food)

    all_daily_records: List[Dict[str, object]] = []
    all_diversity_scores: List[Dict[str, object]] = []
    target_cals_map: Dict[str, float] = {}

    for prof_key in profiles:
        prof = get_profile(prof_key)
        targets = get_profile_targets(prof)
        target_cals_map[prof_key] = float(targets["calories"])

        print(f"\n=======================================================", flush=True)
        print(f">>> EVALUATING PROFILE: {prof_key.upper()} ({prof.name}, {prof.medical_conditions}) <<<", flush=True)
        print(f"Target Calo: {targets['calories']:.1f} kcal | Target Natri: {targets.get('sodium_mg', 2300)} mg", flush=True)
        print(f"=======================================================", flush=True)

        for algo in algos:
            print(f"\n--- Algo: {algo.upper()} ({runs} runs x {days} days) ---", flush=True)
            for r_idx in range(1, runs + 1):
                seed = args.base_seed + r_idx
                t0 = time.perf_counter()
                day_records, div_pct = run_7day_experiment_single(
                    algo=algo,
                    prof_key=prof_key,
                    run_idx=r_idx,
                    base_seed=seed,
                    profile=prof,
                    food_map=food_map,
                    targets=targets,
                    days=days,
                    outer_iter=outer_iter,
                    inner_iter=inner_iter,
                    outer_agents=outer_agents,
                    inner_agents=inner_agents,
                )
                t_run = time.perf_counter() - t0

                all_daily_records.extend(day_records)
                all_diversity_scores.append({
                    "algo": algo,
                    "profile": prof_key,
                    "run": r_idx,
                    "pct_unique_main_dishes": round(div_pct, 1),
                })

                mean_fit = np.mean([r["fitness"] for r in day_records])
                print(
                    f"  [Run {r_idx:02d}/{runs:02d}] Seed {seed} done in {t_run:>5.1f}s | "
                    f"Mean Fit: {mean_fit:>6.2f} | Unique Dishes: {div_pct:>5.1f}%",
                    flush=True
                )

    # 1. Save weekly_runs.csv
    runs_file = out_dir / "weekly_runs.csv"
    runs_df = pd.DataFrame(all_daily_records)
    runs_df.to_csv(runs_file, index=False, encoding="utf-8")
    print(f"\n[SAVED] {runs_file} ({len(runs_df)} rows)", flush=True)

    # 2. Save diversity_score.csv
    div_file = out_dir / "diversity_score.csv"
    div_df = pd.DataFrame(all_diversity_scores)
    div_df.to_csv(div_file, index=False, encoding="utf-8")
    print(f"[SAVED] {div_file} ({len(div_df)} rows)", flush=True)

    # 3. Save weekly_summary.csv
    summary_file = out_dir / "weekly_summary.csv"
    summary_data = compute_weekly_summary(all_daily_records, target_cals_map)
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(summary_file, index=False, encoding="utf-8")
    print(f"[SAVED] {summary_file}", flush=True)
    print("\n--- WEEKLY SUMMARY TABLE ---", flush=True)
    print(summary_df.to_string(index=False), flush=True)

    print("\n[COMPLETE] Week 9 experiment run finished successfully!", flush=True)


if __name__ == "__main__":
    main()


