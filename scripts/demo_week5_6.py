"""Single-run demonstration of IDBO on a benchmark function.

Usage:
    python scripts/demo_week5_6.py --function rastrigin --dim 10 --max-iter 500
    python scripts/demo_week5_6.py --dry-run --function sphere --dim 10 --max-iter 80
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.benchmarks import get_benchmark, list_benchmarks
from src.algorithms.dbo import BEHAVIOR_NAMES
from src.algorithms.idbo import IDBO


def _create_mock_behaviors() -> dict:
    def _step(X, *args, rng=None, **kwargs):
        generator = rng if rng is not None else np.random.default_rng()
        return X * 0.9 + 0.01 * generator.standard_normal(X.shape)

    return {name: _step for name in BEHAVIOR_NAMES}


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo IDBO on a benchmark function.")
    parser.add_argument(
        "--function",
        type=str,
        default="rastrigin",
        help=f"Benchmark name. Available: {', '.join(list_benchmarks())} (default: rastrigin)",
    )
    parser.add_argument("--dim", type=int, default=10)
    parser.add_argument("--n-agents", type=int, default=30)
    parser.add_argument("--max-iter", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--log-every", type=int, default=50)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use mock behaviours (pipeline check without real DBO operators)",
    )
    args = parser.parse_args()

    if args.log_every < 1:
        parser.error("--log-every must be >= 1")
    if args.dim < 1:
        parser.error("--dim must be >= 1")

    bench = get_benchmark(args.function)
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

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 65)
    print(" DEMO: IMPROVED DUNG BEETLE OPTIMIZER (IDBO) - TUAN 5-6")
    print(f" Ham muc tieu     : {bench.name} ({bench.category})")
    print(f" Mo ta            : {bench.description}")
    print(f" So chieu (dim)   : {args.dim}")
    print(f" Khoang tim kiem  : [{bench.lb}, {bench.ub}]")
    print(f" Toi uu da biet   : f(x*) = {bench.optimum_val}")
    print(
        f" Cau hinh IDBO    : n_agents={args.n_agents}, max_iter={args.max_iter}, seed={args.seed}"
    )
    print("=" * 65)

    optimizer = IDBO(
        n_agents=args.n_agents,
        max_iter=args.max_iter,
        behaviors=behaviors,
    )
    result = optimizer.optimize(
        objective=bench.func,
        dim=args.dim,
        lb=bench.lb,
        ub=bench.ub,
        seed=args.seed,
    )

    print("\n--- Tien trinh hoi tu ---")
    history = result.history
    for step in range(0, len(history), args.log_every):
        print(f"  Iteration {step:>4d}: best fitness = {history[step]:.6e}")
    if (len(history) - 1) % args.log_every != 0:
        last_step = len(history) - 1
        print(f"  Iteration {last_step:>4d}: best fitness = {history[last_step]:.6e}")

    print("\n--- Diversity (cuoi moi iteration) ---")
    div = result.diversity_history
    if div:
        for step in range(0, len(div), args.log_every):
            print(f"  Iteration {step + 1:>4d}: diversity = {div[step]:.6e}")
        last_i = len(div) - 1
        if last_i % args.log_every != 0:
            print(f"  Iteration {len(div):>4d}: diversity = {div[-1]:.6e}")

    print("\n--- Ket qua toi uu ---")
    print(f" Best fitness     : {result.best_fitness:.8e}")
    print(f" Sai khac toi uu  : {abs(result.best_fitness - bench.optimum_val):.8e}")
    print(f" So perturbation  : {result.n_perturbations}")
    print(f" So restart       : {result.n_restarts}")
    print(f" Tong so lan eval : {result.n_evaluations}")
    print(f" Thoi gian chay   : {result.runtime_s:.4f} s")

    if args.dim <= 8:
        x_str = np.array2string(result.best_x, precision=4, suppress_small=True)
    else:
        prefix = np.array2string(result.best_x[:4], precision=4, suppress_small=True)[:-1]
        suffix = np.array2string(result.best_x[-2:], precision=4, suppress_small=True)[1:]
        x_str = f"{prefix} ... {suffix}"
    print(f" Best position x* : {x_str}")
    print("=" * 65)


if __name__ == "__main__":
    main()
