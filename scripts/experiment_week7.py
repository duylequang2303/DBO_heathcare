"""Week 7 Experiment: Optimization of Menu Portions using DBO and IDBO.

Compares DBO and IDBO on Profile P1 across independent runs (M seeds).
Both algorithms optimize portion sizes x in [25, 350] grams for a fixed set
of food items sampled with seed=7000.

Outputs:
  - experiments/week7/menu_runs.csv
  - experiments/week7/menu_summary.csv
  - experiments/week7/menu_history.csv
  - experiments/week7/food_ids_p1.txt
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Dict, List

import numpy as np

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.dbo import DBO
from src.algorithms.idbo import IDBO
from src.algorithms.menu_objective import make_menu_objective, decode_result
from src.models.constraints import validate_menu
from src.models.food_sampler import sample_food_ids
from src.models.menu import Menu
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets


def get_profile_p1() -> UserProfile:
    """Standard Week 7 evaluation profile P1 (Duy)."""
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


def compute_random_baseline(
    food_ids: list[str],
    food_map: dict,
    profile: UserProfile,
    targets: dict[str, float],
    n_samples: int = 10,
    seed: int = 7000,
) -> dict[str, float]:
    """Evaluate random portion assignments x ~ U(25, 350) on same food_ids."""
    rng = np.random.default_rng(seed)
    dim = len(food_ids)
    violations_list = []
    fitness_list = []
    calories_list = []

    from src.models.objective import evaluate

    for _ in range(n_samples):
        x = rng.uniform(25.0, 350.0, size=dim)
        menu = decode_result(food_ids, x, food_map, profile.meal_counts)
        viols = validate_menu(menu, profile, targets)
        fit = evaluate(menu, profile, targets)
        violations_list.append(len(viols))
        fitness_list.append(fit)
        calories_list.append(menu.total("calories"))

    return {
        "mean_violations": float(np.mean(violations_list)),
        "mean_fitness": float(np.mean(fitness_list)),
        "mean_calories": float(np.mean(calories_list)),
    }


def run_experiment(
    runs: int = 10,
    max_iter: int = 200,
    n_agents: int = 30,
    seed_sampler: int = 7000,
    output_dir: Path | None = None,
) -> None:
    if output_dir is None:
        output_dir = ROOT / "experiments" / "week7"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("================================================================")
    print("WEEK 7 MENU OPTIMIZATION EXPERIMENT (DBO vs IDBO)")
    print(f"Runs (M): {runs}, Max Iter: {max_iter}, Agents (N): {n_agents}")
    print(f"Output directory: {output_dir}")
    print("================================================================")

    # 1. Load database & setup profile
    print("[1/5] Loading food database...")
    df = load_food_db()
    food_map = build_food_map(df)
    profile = get_profile_p1()
    targets = daily_all_targets(profile)
    print(f"Profile: {profile.name}, Age: {profile.age}, Weight: {profile.weight_kg}kg, Height: {profile.height_cm}cm")
    print(f"Target Calories: {targets['calories']:.1f} kcal | Protein: {targets['protein_g']:.1f}g | Carbs: {targets['carbs_g']:.1f}g | Fat: {targets['fat_g']:.1f}g | Fiber: {targets['fiber_g']:.1f}g")

    # 2. Sample food items
    print(f"[2/5] Sampling food items with seed={seed_sampler}...")
    rng_sampler = np.random.default_rng(seed_sampler)
    food_ids = sample_food_ids(food_map, profile.meal_counts, profile, rng_sampler)
    dim = len(food_ids)
    print(f"Sampled {dim} food items:")
    food_ids_file = output_dir / "food_ids_p1.txt"
    with open(food_ids_file, "w", encoding="utf-8") as f:
        for fid in food_ids:
            row = food_map.get(fid, {})
            name = row.get("food_name", "Unknown")
            mtype = row.get("meal_type", "all")
            print(f"  - [{fid}] {name} ({mtype})")
            f.write(f"{fid}\n")
    print(f"Saved food IDs to {food_ids_file}")

    # 3. Baseline random evaluation
    print("[3/5] Evaluating random baseline (10 samples, x ~ U(25, 350))...")
    baseline = compute_random_baseline(food_ids, food_map, profile, targets, n_samples=10, seed=seed_sampler)
    print(f"  Random Menu Mean Violations: {baseline['mean_violations']:.2f}")
    print(f"  Random Menu Mean Fitness:    {baseline['mean_fitness']:.2f}")
    print(f"  Random Menu Mean Calories:   {baseline['mean_calories']:.1f} kcal")

    # 4. Run DBO and IDBO
    print(f"[4/5] Running optimization algorithms (DBO and IDBO)...")
    objective = make_menu_objective(profile, food_ids, food_map, targets)

    runs_data: List[dict] = []
    history_data: List[dict] = []

    algorithms = ["dbo", "idbo"]

    for algo_name in algorithms:
        print(f"\n--- Running {algo_name.upper()} ({runs} runs) ---")
        for r in range(1, runs + 1):
            seed = seed_sampler + r
            t0 = time.perf_counter()

            if algo_name == "dbo":
                opt = DBO(n_agents=n_agents, max_iter=max_iter)
            else:
                opt = IDBO(n_agents=n_agents, max_iter=max_iter)

            res = opt.optimize(objective, dim=dim, lb=25.0, ub=350.0, seed=seed)
            runtime_s = time.perf_counter() - t0

            # Convert minimized objective back to true fitness (higher is better)
            best_fitness = -float(res.best_fitness)

            # Record history
            for it, val in enumerate(res.history):
                history_data.append({
                    "algorithm": algo_name,
                    "profile": "P1",
                    "run": r,
                    "iteration": it,
                    "fitness": -float(val),
                })

            # Decode final menu & analyze
            menu = decode_result(food_ids, res.best_x, food_map, profile.meal_counts)
            violations = validate_menu(menu, profile, targets)
            n_violations = len(violations)

            cals = menu.total("calories")
            prot = menu.total("protein_g")
            carbs = menu.total("carbs_g")
            fat = menu.total("fat_g")
            fiber = menu.total("fiber_g")

            run_entry = {
                "algorithm": algo_name,
                "profile": "P1",
                "run": r,
                "seed": seed,
                "best_fitness": best_fitness,
                "n_evaluations": res.n_evaluations,
                "runtime_s": runtime_s,
                "n_violations": n_violations,
                "calories": cals,
                "protein_g": prot,
                "carbs_g": carbs,
                "fat_g": fat,
                "fiber_g": fiber,
            }
            runs_data.append(run_entry)
            print(f"  Run {r:2d}/{runs} (seed={seed}): fitness={best_fitness:.4f}, viols={n_violations}, cals={cals:.1f}, time={runtime_s:.2f}s")

    # 5. Export CSV files
    print("\n[5/5] Exporting CSV files...")
    
    # 5.1 menu_runs.csv
    runs_csv = output_dir / "menu_runs.csv"
    runs_fieldnames = [
        "algorithm", "profile", "run", "seed", "best_fitness",
        "n_evaluations", "runtime_s", "n_violations",
        "calories", "protein_g", "carbs_g", "fat_g", "fiber_g",
    ]
    with open(runs_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=runs_fieldnames)
        writer.writeheader()
        writer.writerows(runs_data)
    print(f"Saved runs to {runs_csv}")

    # 5.2 menu_history.csv
    hist_csv = output_dir / "menu_history.csv"
    hist_fieldnames = ["algorithm", "profile", "run", "iteration", "fitness"]
    with open(hist_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=hist_fieldnames)
        writer.writeheader()
        writer.writerows(history_data)
    print(f"Saved history to {hist_csv}")

    # 5.3 menu_summary.csv
    summary_data = []
    for algo_name in algorithms:
        algo_runs = [d for d in runs_data if d["algorithm"] == algo_name]
        fits = [d["best_fitness"] for d in algo_runs]
        evals = [d["n_evaluations"] for d in algo_runs]
        times = [d["runtime_s"] for d in algo_runs]
        viols = [d["n_violations"] for d in algo_runs]

        summary_entry = {
            "algorithm": algo_name,
            "profile": "P1",
            "runs": len(algo_runs),
            "best": float(np.max(fits)),
            "mean": float(np.mean(fits)),
            "std": float(np.std(fits)),
            "worst": float(np.min(fits)),
            "mean_n_evaluations": float(np.mean(evals)),
            "mean_runtime_s": float(np.mean(times)),
            "mean_n_violations": float(np.mean(viols)),
        }
        summary_data.append(summary_entry)

    summary_csv = output_dir / "menu_summary.csv"
    summary_fieldnames = [
        "algorithm", "profile", "runs", "best", "mean", "std", "worst",
        "mean_n_evaluations", "mean_runtime_s", "mean_n_violations",
    ]
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fieldnames)
        writer.writeheader()
        writer.writerows(summary_data)
    print(f"Saved summary to {summary_csv}")

    # Print summary table and answering questions
    print("\n======================= SUMMARY RESULTS =======================")
    dbo_sum = next(s for s in summary_data if s["algorithm"] == "dbo")
    idbo_sum = next(s for s in summary_data if s["algorithm"] == "idbo")

    diff_rel = abs(idbo_sum["mean"] - dbo_sum["mean"]) / max(abs(dbo_sum["mean"]), 1e-9)
    if diff_rel < 0.01:
        winner = "hòa"
    elif idbo_sum["mean"] > dbo_sum["mean"]:
        winner = "IDBO"
    else:
        winner = "DBO"

    print(f"DBO:  mean_fitness={dbo_sum['mean']:.4f} ± {dbo_sum['std']:.4f}, mean_viols={dbo_sum['mean_n_violations']:.2f}, mean_time={dbo_sum['mean_runtime_s']:.2f}s")
    print(f"IDBO: mean_fitness={idbo_sum['mean']:.4f} ± {idbo_sum['std']:.4f}, mean_viols={idbo_sum['mean_n_violations']:.2f}, mean_time={idbo_sum['mean_runtime_s']:.2f}s")
    print(f"Winner (mean, threshold 1%): {winner} (rel_diff = {diff_rel*100:.2f}%)")
    print("================================================================")


def main():
    parser = argparse.ArgumentParser(description="Week 7 Menu Optimization Experiment")
    parser.add_argument("--runs", type=int, default=10, help="Number of independent runs (M)")
    parser.add_argument("--max-iter", type=int, default=200, help="Max iterations per run")
    parser.add_argument("--n-agents", type=int, default=30, help="Population size")
    parser.add_argument("--seed-sampler", type=int, default=7000, help="Seed for food sampling")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")

    args = parser.parse_args()
    out_dir = Path(args.output_dir) if args.output_dir else None
    run_experiment(
        runs=args.runs,
        max_iter=args.max_iter,
        n_agents=args.n_agents,
        seed_sampler=args.seed_sampler,
        output_dir=out_dir,
    )


if __name__ == "__main__":
    main()
