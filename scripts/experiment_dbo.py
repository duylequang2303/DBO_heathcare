"""Benchmark convergence experiments for Dung Beetle Optimizer (DBO).

Runs DBO over standard benchmark functions across multiple dimensions and
independent runs (seeds), computes summary statistics (best, mean, std, worst),
and exports CSV results to the output directory.

Usage:
    # Dry-run smoke test (using mock behaviors for pipeline verification):
    py scripts/experiment_dbo.py --dry-run --runs 2 --dims 2 10 --max-iter 20

    # Full benchmark experiment (once behaviors.py is available):
    py scripts/experiment_dbo.py --runs 30 --dims 2 10 30 --max-iter 500
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.benchmarks import BENCHMARKS, get_benchmark, list_benchmarks
from src.algorithms.dbo import DBO, BEHAVIOR_NAMES


def _create_mock_behaviors() -> Dict[str, Callable]:
    """Provides simple mock behaviors for dry-run verification."""
    def _step(X, *args, rng=None, **kwargs):
        generator = rng if rng is not None else np.random.default_rng()
        return X * 0.9 + 0.01 * generator.standard_normal(X.shape)

    return {name: _step for name in BEHAVIOR_NAMES}


def run_single_experiment(
    benchmark_name: str,
    dim: int,
    run_idx: int,
    seed: int,
    n_agents: int,
    max_iter: int,
    behaviors: dict | None = None,
) -> dict:
    """Executes a single optimization run of DBO on a given benchmark."""
    bench = get_benchmark(benchmark_name)
    optimizer = DBO(
        n_agents=n_agents,
        max_iter=max_iter,
        behaviors=behaviors,
    )
    result = optimizer.optimize(
        objective=bench.func,
        dim=dim,
        lb=bench.lb,
        ub=bench.ub,
        seed=seed,
    )
    return {
        "function": bench.name,
        "category": bench.category,
        "dim": dim,
        "run": run_idx,
        "seed": seed,
        "best_fitness": result.best_fitness,
        "runtime_s": round(result.runtime_s, 4),
        "n_evaluations": result.n_evaluations,
    }


def main() -> None:
    """Parse CLI arguments, run DBO benchmark experiments, and export results to CSV.

    For each combination of benchmark function and dimension, executes ``args.runs``
    independent runs of DBO with distinct seeds.  Writes per-run details and
    aggregated Best/Mean/Std/Worst statistics to CSV files in the output directory.
    Use ``--dry-run`` to verify the pipeline without needing ``behaviors.py``.
    """
    parser = argparse.ArgumentParser(description="Run DBO benchmark convergence experiments.")
    parser.add_argument(
        "--functions",
        nargs="+",
        default=list_benchmarks(),
        help="Benchmark functions to test (default: all registered benchmarks)",
    )
    parser.add_argument(
        "--dims",
        nargs="+",
        type=int,
        default=[2, 10, 30],
        help="Dimensions to evaluate (default: 2 10 30)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=30,
        help="Number of independent runs per configuration (default: 30)",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=500,
        help="Maximum iterations per run (default: 500)",
    )
    parser.add_argument(
        "--n-agents",
        type=int,
        default=30,
        help="Population size (default: 30)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="experiments/week4",
        help="Output directory for CSV files (default: experiments/week4)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run using mock behaviors to test the pipeline without behaviors.py",
    )
    args = parser.parse_args()

    if args.runs < 1:
        parser.error("--runs must be >= 1")

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    behaviors = None
    if args.dry_run:
        print("[DRY RUN MODE] Using mock behaviors for pipeline verification.")
        behaviors = _create_mock_behaviors()
    else:
        # Check if behaviors module exists
        try:
            import src.algorithms.behaviors  # noqa: F401
        except ImportError:
            print(
                "\n[ERROR] Module 'src.algorithms.behaviors' is not yet implemented (Cương's task).\n"
                "To test this experiment pipeline in dry-run mode, rerun with:\n"
                "    py scripts/experiment_dbo.py --dry-run [options]\n",
                file=sys.stderr,
            )
            sys.exit(1)

    print("=" * 70)
    print(" DBO BENCHMARK EXPERIMENT RUNNER")
    print(f" Functions : {', '.join(args.functions)}")
    print(f" Dims      : {args.dims}")
    print(f" Runs (M)  : {args.runs}")
    print(f" Pop size  : {args.n_agents} | Max iter: {args.max_iter}")
    print(f" Output dir: {out_dir}")
    print("=" * 70)

    total_runs = len(args.functions) * len(args.dims) * args.runs
    completed_runs = 0
    start_total_time = time.perf_counter()

    all_results: List[dict] = []

    for f_idx, func_name in enumerate(args.functions):
        # Resolve to canonical name once so CSV records always use the normalised key
        canonical_name = get_benchmark(func_name).name
        for d_idx, dim in enumerate(args.dims):
            print(f"--> Testing '{canonical_name}' (dim={dim}) across {args.runs} runs...")
            for r in range(args.runs):
                seed = 1000 * (f_idx + 1) + 100 * (d_idx + 1) + (r + 1)
                res = run_single_experiment(
                    benchmark_name=canonical_name,
                    dim=dim,
                    run_idx=r + 1,
                    seed=seed,
                    n_agents=args.n_agents,
                    max_iter=args.max_iter,
                    behaviors=behaviors,
                )
                all_results.append(res)
                completed_runs += 1

    total_runtime = time.perf_counter() - start_total_time

    # Save detailed runs CSV
    runs_csv = out_dir / "dbo_benchmark_runs.csv"
    fieldnames = [
        "function",
        "category",
        "dim",
        "run",
        "seed",
        "best_fitness",
        "runtime_s",
        "n_evaluations",
    ]
    with open(runs_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\n[OK] Detailed runs written to: {runs_csv}")

    # Compute summary statistics
    summaries: List[dict] = []
    for func_name in args.functions:
        canonical_name = get_benchmark(func_name).name
        for dim in args.dims:
            matching = [
                r["best_fitness"]
                for r in all_results
                if r["function"] == canonical_name and r["dim"] == dim
            ]
            if not matching:
                continue
            arr = np.array(matching, dtype=float)
            summaries.append({
                "function": canonical_name,
                "dim": dim,
                "runs": len(arr),
                "best": float(np.min(arr)),
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "worst": float(np.max(arr)),
            })

    # Save summary CSV
    summary_csv = out_dir / "dbo_benchmark_summary.csv"
    sum_fields = ["function", "dim", "runs", "best", "mean", "std", "worst"]
    with open(summary_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sum_fields)
        writer.writeheader()
        writer.writerows(summaries)
    print(f"[OK] Summary statistics written to: {summary_csv}\n")

    # Print summary table to console
    header = f"{'Function':<16} {'Dim':<5} {'Runs':<5} {'Best':<14} {'Mean':<14} {'Std':<14} {'Worst':<14}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for s in summaries:
        print(
            f"{s['function']:<16} {s['dim']:<5} {s['runs']:<5} "
            f"{s['best']:<14.4e} {s['mean']:<14.4e} {s['std']:<14.4e} {s['worst']:<14.4e}"
        )
    print("-" * len(header))
    print(f"Total experiment time: {total_runtime:.2f} s ({completed_runs}/{total_runs} runs completed)\n")


if __name__ == "__main__":
    main()
