"""Week 8 Experiment Script: Two-Tier Mixed-Integer Optimization (DBO vs IDBO).

Evaluates Two-Tier optimization on Profile P1 across independent runs (seeds 8001..8010):
- Outer Tier: Discrete food selection from candidate pools built from 15,929 items.
- Inner Tier: Continuous portion sizing in [25, 350] grams.
- Solvers compared: DBO (Outer DBO + Inner DBO) vs IDBO (Outer IDBO + Inner IDBO).

Outputs generated in experiments/week8/:
- two_tier_runs.csv: Per-run metrics (fitness, evaluations, runtime, violations, macros).
- two_tier_summary.csv: Aggregate statistics (best, mean, std, worst, runtime, violations).
- two_tier_history.csv: Outer iteration convergence history per run.
- selected_foods_p1.txt: Tab-separated menu items and 5g rounded portions for best overall run.

Usage:
  python scripts/experiment_week8.py --smoke
  python scripts/experiment_week8.py --runs 10 --outer-iter 25 --inner-iter 25
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

from src.algorithms.menu_objective import decode_result
from src.algorithms.two_tier_solver import TwoTierConfig, TwoTierResult, two_tier_optimize
from src.models.constraints import validate_menu
from src.models.food_selector import get_meal_order_slots
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets
from src.utils.portion_utils import round_portions


def get_profile_p1() -> UserProfile:
    """Return standard evaluation profile P1 (Duy, healthy male, maintenance).

    Returns:
        UserProfile: Standard user profile for benchmarking.
    """
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


def run_single_experiment(
    algo: str,
    run_idx: int,
    seed: int,
    profile: UserProfile,
    food_map: dict,
    targets: dict,
    outer_max_iter: int = 25,
    outer_n_agents: int = 10,
    inner_max_iter: int = 25,
    inner_n_agents: int = 10,
) -> Tuple[Dict[str, object], List[Dict[str, object]], TwoTierResult]:
    """Execute a single run of two-tier optimization for an algorithm.

    Args:
        algo: Name of algorithm ('dbo' or 'idbo').
        run_idx: 1-based index of current execution run.
        seed: Random seed for this run.
        profile: Evaluation user profile.
        food_map: Food database dictionary.
        targets: Nutrient daily targets.
        outer_max_iter: Maximum iterations for outer loop.
        outer_n_agents: Swarm size for outer loop.
        inner_max_iter: Maximum iterations for inner loop.
        inner_n_agents: Swarm size for inner loop.

    Returns:
        Tuple containing run metrics dict, list of history dicts, and raw TwoTierResult.
    """
    config = TwoTierConfig(
        outer_algo=algo,
        outer_n_agents=outer_n_agents,
        outer_max_iter=outer_max_iter,
        inner_algo=algo,
        inner_n_agents=inner_n_agents,
        inner_max_iter=inner_max_iter,
        seed=seed,
    )

    t0 = time.perf_counter()
    result = two_tier_optimize(profile, food_map, targets, config)
    runtime_s = time.perf_counter() - t0

    menu = decode_result(result.best_food_ids, result.best_portions_g, food_map, profile.meal_counts)
    violations = validate_menu(menu, profile, targets)

    cals = menu.total("calories")
    protein = menu.total("protein_g")
    carbs = menu.total("carbs_g")
    fat = menu.total("fat_g")
    fiber = menu.total("fiber_g")

    run_row = {
        "algo": algo,
        "profile": "p1",
        "run": run_idx,
        "seed": seed,
        "best_fitness": round(float(result.best_fitness), 4),
        "outer_evals": result.outer_evals,
        "inner_evals_total": result.inner_evals_total,
        "runtime_s": round(float(runtime_s), 2),
        "n_violations": len(violations),
        "calories": round(float(cals), 2),
        "protein_g": round(float(protein), 2),
        "carbs_g": round(float(carbs), 2),
        "fat_g": round(float(fat), 2),
        "fiber_g": round(float(fiber), 2),
    }

    history_rows = []
    for it_idx, fit_val in enumerate(result.history):
        history_rows.append({
            "algo": algo,
            "profile": "p1",
            "run": run_idx,
            "outer_iter": it_idx,
            "best_fitness": round(float(fit_val), 4),
        })

    return run_row, history_rows, result


def save_selected_foods_txt(
    result: TwoTierResult,
    food_map: dict,
    meal_counts: dict[str, int],
    out_path: Path,
) -> None:
    """Save selected food items with 5g rounded portions to text file.

    Args:
        result: TwoTierResult from the highest-scoring run.
        food_map: Food database dictionary.
        meal_counts: Dictionary of meal counts.
        out_path: Target path for the output txt file.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    meal_order = get_meal_order_slots(meal_counts)
    rounded_portions = round_portions(result.best_portions_g, step=5)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("food_id\tfood_name\tmeal_slot\tgram_rounded\n")
        for idx, (food_id, slot) in enumerate(zip(result.best_food_ids, meal_order)):
            item = food_map.get(food_id, {})
            name = item.get("food_name", f"Food_{food_id}") if isinstance(item, dict) else getattr(item, "food_name", f"Food_{food_id}")
            gram = int(rounded_portions[idx])
            f.write(f"{food_id}\t{name}\t{slot}\t{gram}\n")


def compute_summary_table(runs_data: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Compute aggregate statistical summary grouped by algorithm.

    Args:
        runs_data: List of run dictionary records.

    Returns:
        List of summary dict records matching two_tier_summary.csv schema.
    """
    df = pd.DataFrame(runs_data)
    summary_rows = []

    for algo, grp in df.groupby("algo"):
        fits = grp["best_fitness"].astype(float).values
        runtimes = grp["runtime_s"].astype(float).values
        viols = grp["n_violations"].astype(float).values
        n_runs = len(grp)

        std_val = float(np.std(fits, ddof=1)) if n_runs > 1 else 0.0

        summary_rows.append({
            "algo": algo,
            "profile": "p1",
            "runs": n_runs,
            "best": round(float(np.max(fits)), 4),
            "mean": round(float(np.mean(fits)), 4),
            "std": round(std_val, 4),
            "worst": round(float(np.min(fits)), 4),
            "mean_runtime_s": round(float(np.mean(runtimes)), 2),
            "mean_n_violations": round(float(np.mean(viols)), 2),
        })

    return summary_rows


def main() -> None:
    """Main execution function for Week 8 experiment pipeline."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Week 8 Experiment: Two-Tier DBO vs IDBO on P1")
    parser.add_argument("--runs", type=int, default=10, help="Number of independent seed runs (default: 10)")
    parser.add_argument("--outer-iter", type=int, default=25, help="Outer loop iterations (default: 25)")
    parser.add_argument("--outer-agents", type=int, default=10, help="Outer loop swarm size (default: 10)")
    parser.add_argument("--inner-iter", type=int, default=25, help="Inner loop iterations (default: 25)")
    parser.add_argument("--inner-agents", type=int, default=10, help="Inner loop swarm size (default: 10)")
    parser.add_argument("--base-seed", type=int, default=8000, help="Base seed offset (default: 8000)")
    parser.add_argument("--algos", nargs="+", default=["dbo", "idbo"], choices=["dbo", "idbo"], help="Algorithms to evaluate")
    parser.add_argument("--output-dir", type=str, default="experiments/week8", help="Output directory path")
    parser.add_argument("--smoke", action="store_true", help="Run quick smoke test with minimal iterations")

    args = parser.parse_args()

    if args.smoke:
        print("[SMOKE MODE] Running fast sanity smoke with minimal iterations...")
        runs = 2
        outer_iter = 5
        outer_agents = 5
        inner_iter = 5
        inner_agents = 5
    else:
        runs = args.runs
        outer_iter = args.outer_iter
        outer_agents = args.outer_agents
        inner_iter = args.inner_iter
        inner_agents = args.inner_agents

    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80, flush=True)
    print("EXPERIMENT WEEK 8: TWO-TIER MIXED-INTEGER OPTIMIZATION (DBO vs IDBO)", flush=True)
    print(f"Algos: {args.algos} | Runs: {runs} | Base Seed: {args.base_seed}", flush=True)
    print(f"Outer: {outer_agents} agents, {outer_iter} iters | Inner: {inner_agents} agents, {inner_iter} iters", flush=True)
    print(f"Output directory: {out_dir}", flush=True)
    print("=" * 80, flush=True)

    df_food = load_food_db()
    food_map = build_food_map(df_food)
    profile = get_profile_p1()
    targets = daily_all_targets(profile)

    all_runs: List[Dict[str, object]] = []
    all_history: List[Dict[str, object]] = []
    best_overall_result: TwoTierResult | None = None
    best_overall_fitness = -float("inf")

    t_all_start = time.perf_counter()

    for algo in args.algos:
        print(f"\n>>> Running Benchmark: {algo.upper()} 2-Tier ({runs} runs) <<<", flush=True)
        for r_idx in range(1, runs + 1):
            seed = args.base_seed + r_idx
            print(f"  [Run {r_idx:02d}/{runs:02d}] Seed {seed} ...", end=" ", flush=True)

            run_row, hist_rows, raw_res = run_single_experiment(
                algo=algo,
                run_idx=r_idx,
                seed=seed,
                profile=profile,
                food_map=food_map,
                targets=targets,
                outer_max_iter=outer_iter,
                outer_n_agents=outer_agents,
                inner_max_iter=inner_iter,
                inner_n_agents=inner_agents,
            )

            all_runs.append(run_row)
            all_history.extend(hist_rows)

            print(
                f"Done in {run_row['runtime_s']:>5.1f}s | "
                f"Fitness: {run_row['best_fitness']:>7.4f} | "
                f"Calo: {run_row['calories']:>6.1f} kcal | "
                f"Violations: {run_row['n_violations']}",
                flush=True
            )

            if raw_res.best_fitness > best_overall_fitness:
                best_overall_fitness = raw_res.best_fitness
                best_overall_result = raw_res

    total_elapsed = time.perf_counter() - t_all_start

    runs_file = out_dir / "two_tier_runs.csv"
    runs_df = pd.DataFrame(all_runs)
    runs_df.to_csv(runs_file, index=False, encoding="utf-8")
    print(f"\n[SAVED] {runs_file} ({len(runs_df)} rows)", flush=True)

    summary_file = out_dir / "two_tier_summary.csv"
    summary_data = compute_summary_table(all_runs)
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(summary_file, index=False, encoding="utf-8")
    print(f"[SAVED] {summary_file}", flush=True)
    print("\n--- SUMMARY TABLE ---", flush=True)
    print(summary_df.to_string(index=False), flush=True)

    history_file = out_dir / "two_tier_history.csv"
    hist_df = pd.DataFrame(all_history)
    hist_df.to_csv(history_file, index=False, encoding="utf-8")
    print(f"\n[SAVED] {history_file} ({len(hist_df)} rows)", flush=True)

    if best_overall_result is not None:
        txt_file = out_dir / "selected_foods_p1.txt"
        save_selected_foods_txt(best_overall_result, food_map, profile.meal_counts, txt_file)
        print(f"[SAVED] {txt_file} (Best fitness = {best_overall_fitness:.4f})", flush=True)

    print(f"\n[COMPLETE] Week 8 experiment run finished successfully in {total_elapsed:.1f}s!", flush=True)


if __name__ == "__main__":
    main()
