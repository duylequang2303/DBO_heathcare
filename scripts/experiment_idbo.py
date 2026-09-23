"""Compare original DBO vs IDBO on the week-4 benchmark suite.

Usage:
    python scripts/experiment_idbo.py --runs 3 --dims 2 10 --max-iter 80 --functions sphere rastrigin
    python scripts/experiment_idbo.py --runs 30 --dims 2 10 30 --max-iter 500
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.benchmarks import get_benchmark, list_benchmarks
from src.algorithms.dbo import BEHAVIOR_NAMES, DBO
from src.algorithms.idbo import IDBO


def _create_mock_behaviors() -> Dict[str, Callable]:
    def _step(X, *args, rng=None, **kwargs):
        generator = rng if rng is not None else np.random.default_rng()
        return X * 0.9 + 0.01 * generator.standard_normal(X.shape)

    return {name: _step for name in BEHAVIOR_NAMES}


def run_single(
    algorithm: str,
    benchmark_name: str,
    dim: int,
    run_idx: int,
    seed: int,
    n_agents: int,
    max_iter: int,
    behaviors: dict | None = None,
) -> dict:
    bench = get_benchmark(benchmark_name)
    if algorithm == "dbo":
        optimizer = DBO(n_agents=n_agents, max_iter=max_iter, behaviors=behaviors)
    elif algorithm == "idbo":
        optimizer = IDBO(n_agents=n_agents, max_iter=max_iter, behaviors=behaviors)
    else:
        raise ValueError(f"unknown algorithm '{algorithm}'")

    result = optimizer.optimize(
        objective=bench.func,
        dim=dim,
        lb=bench.lb,
        ub=bench.ub,
        seed=seed,
    )
    row = {
        "algorithm": algorithm,
        "function": bench.name,
        "category": bench.category,
        "dim": dim,
        "run": run_idx,
        "seed": seed,
        "best_fitness": result.best_fitness,
        "runtime_s": round(result.runtime_s, 4),
        "n_evaluations": result.n_evaluations,
        "n_perturbations": getattr(result, "n_perturbations", 0),
        "n_restarts": getattr(result, "n_restarts", 0),
        "execution_order": 0,
        "history": result.history,
        "diversity_history": getattr(result, "diversity_history", []),
    }
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare DBO vs IDBO on benchmarks.")
    parser.add_argument("--functions", nargs="+", default=list_benchmarks())
    parser.add_argument("--dims", nargs="+", type=int, default=[2, 10, 30])
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--max-iter", type=int, default=500)
    parser.add_argument("--n-agents", type=int, default=30)
    parser.add_argument("--out-dir", type=str, default="experiments/week5_6")
    parser.add_argument(
        "--algorithms",
        nargs="+",
        default=["dbo", "idbo"],
        help="Algorithms to run (default: dbo idbo)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.runs < 1:
        parser.error("--runs must be >= 1")
    if any(dim < 1 for dim in args.dims):
        parser.error("--dims values must be >= 1")
    unknown = [a for a in args.algorithms if a not in ("dbo", "idbo")]
    if unknown:
        parser.error(f"unknown algorithms: {unknown}")

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    behaviors = None
    if args.dry_run:
        print("[DRY RUN MODE] Using mock behaviors.")
        behaviors = _create_mock_behaviors()
    else:
        try:
            import src.algorithms.behaviors  # noqa: F401
        except ImportError:
            print(
                "\n[ERROR] Missing src.algorithms.behaviors. Retry with --dry-run.\n",
                file=sys.stderr,
            )
            sys.exit(1)

    print("=" * 70)
    print(" DBO vs IDBO BENCHMARK COMPARISON")
    print(f" Algorithms: {', '.join(args.algorithms)}")
    print(f" Functions : {', '.join(args.functions)}")
    print(f" Dims      : {args.dims}")
    print(f" Runs (M)  : {args.runs}")
    print(f" Pop size  : {args.n_agents} | Max iter: {args.max_iter}")
    print(f" Output dir: {out_dir}")
    print("=" * 70)

    total_runs = len(args.algorithms) * len(args.functions) * len(args.dims) * args.runs
    completed_runs = 0
    start_total_time = time.perf_counter()
    all_results: List[dict] = []

    for f_idx, func_name in enumerate(args.functions):
        canonical_name = get_benchmark(func_name).name
        for d_idx, dim in enumerate(args.dims):
            print(f"--> '{canonical_name}' dim={dim} x {args.runs} ({', '.join(args.algorithms)})")
            for r in range(args.runs):
                seed = 1000 * (f_idx + 1) + 100 * (d_idx + 1) + (r + 1)
                order_rng = np.random.default_rng(seed + 17_000)
                algo_order = list(args.algorithms)
                order_rng.shuffle(algo_order)
                for exec_idx, algo in enumerate(algo_order, start=1):
                    row = run_single(
                        algorithm=algo,
                        benchmark_name=canonical_name,
                        dim=dim,
                        run_idx=r + 1,
                        seed=seed,
                        n_agents=args.n_agents,
                        max_iter=args.max_iter,
                        behaviors=behaviors,
                    )
                    row["execution_order"] = exec_idx
                    all_results.append(row)
                    completed_runs += 1

    total_runtime = time.perf_counter() - start_total_time

    runs_csv = out_dir / "idbo_vs_dbo_runs.csv"
    fieldnames = [
        "algorithm",
        "function",
        "category",
        "dim",
        "run",
        "seed",
        "best_fitness",
        "runtime_s",
        "n_evaluations",
        "n_perturbations",
        "n_restarts",
        "execution_order",
    ]
    # Filter keys matching fieldnames so extra keys like 'history' don't crash DictWriter
    clean_runs = [{k: r[k] for k in fieldnames} for r in all_results]
    with open(runs_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_runs)
    print(f"\n[OK] Detailed runs written to: {runs_csv}")

    # History CSV (dim=10 per spec to keep file size reasonable)
    history_csv = out_dir / "idbo_vs_dbo_history.csv"
    history_fields = ["algorithm", "function", "dim", "run", "iteration", "best_fitness"]
    history_rows = []
    for r in all_results:
        if r["dim"] == 10:
            for it, fit in enumerate(r.get("history", [])):
                history_rows.append(
                    {
                        "algorithm": r["algorithm"],
                        "function": r["function"],
                        "dim": r["dim"],
                        "run": r["run"],
                        "iteration": it,
                        "best_fitness": fit,
                    }
                )
    with open(history_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=history_fields)
        writer.writeheader()
        writer.writerows(history_rows)
    print(f"[OK] Convergence history written to: {history_csv}")

    # Diversity CSV (IDBO, dim=10 per spec)
    diversity_csv = out_dir / "idbo_diversity.csv"
    diversity_fields = ["function", "dim", "run", "iteration", "diversity"]
    diversity_rows = []
    for r in all_results:
        if r["algorithm"] == "idbo" and r["dim"] == 10:
            for it, div in enumerate(r.get("diversity_history", []), start=1):
                diversity_rows.append(
                    {
                        "function": r["function"],
                        "dim": r["dim"],
                        "run": r["run"],
                        "iteration": it,
                        "diversity": div,
                    }
                )
    with open(diversity_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=diversity_fields)
        writer.writeheader()
        writer.writerows(diversity_rows)
    print(f"[OK] Diversity history written to: {diversity_csv}")

    summaries: List[dict] = []
    for algo in args.algorithms:
        for func_name in args.functions:
            canonical_name = get_benchmark(func_name).name
            for dim in args.dims:
                matching = [
                    r
                    for r in all_results
                    if r["algorithm"] == algo
                    and r["function"] == canonical_name
                    and r["dim"] == dim
                ]
                if not matching:
                    continue
                arr = np.array([r["best_fitness"] for r in matching], dtype=float)
                evals = np.array([r["n_evaluations"] for r in matching], dtype=float)
                summaries.append(
                    {
                        "algorithm": algo,
                        "function": canonical_name,
                        "dim": dim,
                        "runs": len(arr),
                        "best": float(np.min(arr)),
                        "mean": float(np.mean(arr)),
                        "std": float(np.std(arr)),
                        "worst": float(np.max(arr)),
                        "mean_n_evaluations": float(np.mean(evals)),
                    }
                )

    summary_csv = out_dir / "idbo_vs_dbo_summary.csv"
    sum_fields = [
        "algorithm",
        "function",
        "dim",
        "runs",
        "best",
        "mean",
        "std",
        "worst",
        "mean_n_evaluations",
    ]
    with open(summary_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sum_fields)
        writer.writeheader()
        writer.writerows(summaries)
    print(f"[OK] Summary statistics written to: {summary_csv}\n")

    header = (
        f"{'Algo':<6} {'Function':<16} {'Dim':<5} {'Runs':<5} "
        f"{'Best':<14} {'Mean':<14} {'Std':<14} {'Worst':<14} {'MeanEvals':<12}"
    )
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for s in summaries:
        print(
            f"{s['algorithm']:<6} {s['function']:<16} {s['dim']:<5} {s['runs']:<5} "
            f"{s['best']:<14.4e} {s['mean']:<14.4e} {s['std']:<14.4e} {s['worst']:<14.4e} "
            f"{s['mean_n_evaluations']:<12.1f}"
        )
    print("-" * len(header))
    print(
        f"Total experiment time: {total_runtime:.2f} s "
        f"({completed_runs}/{total_runs} runs completed)\n"
    )


if __name__ == "__main__":
    main()
