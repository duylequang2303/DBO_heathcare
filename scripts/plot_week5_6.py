"""Generate comparison plots for DBO vs IDBO (Week 5-6).

Produces 3 required figures:
- F1: Average convergence curves (dim=10, Y-axis log scale, 6 subplots, DBO vs IDBO).
      File: experiments/week5_6/fig_convergence_dim10.png
- F2: Boxplots of best_fitness (dim=10, 6 subplots, DBO vs IDBO).
      File: experiments/week5_6/fig_boxplot_dim10.png
- F3: Average population diversity over iterations (dim=10, Sphere vs Rastrigin on single frame).
      File: experiments/week5_6/fig_diversity_dim10.png

Usage:
    python scripts/plot_week5_6.py --out-dir experiments/week5_6
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FUNCTIONS_ORDER = [
    "sphere",
    "schwefel_2_22",
    "rosenbrock",
    "rastrigin",
    "ackley",
    "griewank",
]

# Distinct, professional colors
COLOR_DBO = "#2B5C8F"   # Classic blue
COLOR_IDBO = "#D95F02"  # Vibrant orange/amber
COLOR_SPHERE = "#2CA02C"
COLOR_RASTRIGIN = "#D62728"


def plot_f1_convergence(history_csv: Path, out_path: Path, dim: int = 10) -> None:
    """F1: Convergence curve (dim=10, Y-axis log scale, 6 subplots, 2 lines DBO/IDBO)."""
    if not history_csv.is_file():
        print(f"[WARN] History file not found: {history_csv}. Skipping F1.")
        return

    df = pd.read_csv(history_csv)
    df_dim = df[df["dim"] == dim]
    if df_dim.empty:
        print(f"[WARN] No records found for dim={dim} in {history_csv}. Skipping F1.")
        return

    # Calculate mean best_fitness grouped by (algorithm, function, iteration)
    grouped = (
        df_dim.groupby(["algorithm", "function", "iteration"])["best_fitness"]
        .mean()
        .reset_index()
    )

    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    axes = axes.flatten()

    for idx, func_name in enumerate(FUNCTIONS_ORDER):
        ax = axes[idx]
        func_data = grouped[grouped["function"] == func_name]

        dbo_data = func_data[func_data["algorithm"] == "dbo"].sort_values("iteration")
        idbo_data = func_data[func_data["algorithm"] == "idbo"].sort_values("iteration")

        # Epsilon added to avoid log(0)
        eps = 1e-300
        if not dbo_data.empty:
            ax.plot(
                dbo_data["iteration"],
                np.maximum(dbo_data["best_fitness"], eps),
                label="DBO",
                color=COLOR_DBO,
                linewidth=1.8,
            )
        if not idbo_data.empty:
            ax.plot(
                idbo_data["iteration"],
                np.maximum(idbo_data["best_fitness"], eps),
                label="IDBO",
                color=COLOR_IDBO,
                linewidth=1.8,
                linestyle="--",
            )

        ax.set_yscale("log")
        ax.set_title(f"{func_name} (dim={dim})", fontsize=12, fontweight="bold")
        ax.set_xlabel("Iteration", fontsize=10)
        ax.set_ylabel("Mean Best Fitness (log scale)", fontsize=10)
        ax.grid(True, which="both", linestyle=":", alpha=0.6)
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(handles, labels, loc="upper right", framealpha=0.9)

    n_runs = int(df_dim["run"].nunique()) if "run" in df_dim.columns else 0
    run_str = f", averaged over {n_runs} runs" if n_runs > 0 else ""
    fig.suptitle(
        f"Convergence Curves: DBO vs IDBO (dim={dim}{run_str})",
        fontsize=14,
        fontweight="bold",
    )
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[OK] F1 Convergence plot saved to: {out_path}")


def plot_f2_boxplot(runs_csv: Path, out_path: Path, dim: int = 10) -> None:
    """F2: Boxplot best_fitness DBO vs IDBO, dim=10, 6 functions."""
    if not runs_csv.is_file():
        print(f"[WARN] Runs file not found: {runs_csv}. Skipping F2.")
        return

    df = pd.read_csv(runs_csv)
    df_dim = df[df["dim"] == dim]
    if df_dim.empty:
        print(f"[WARN] No records found for dim={dim} in {runs_csv}. Skipping F2.")
        return

    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    axes = axes.flatten()

    for idx, func_name in enumerate(FUNCTIONS_ORDER):
        ax = axes[idx]
        f_data = df_dim[df_dim["function"] == func_name]

        dbo_vals = f_data[f_data["algorithm"] == "dbo"]["best_fitness"].dropna().values
        idbo_vals = f_data[f_data["algorithm"] == "idbo"]["best_fitness"].dropna().values

        data_to_plot = [dbo_vals, idbo_vals]
        bp = ax.boxplot(
            data_to_plot,
            tick_labels=["DBO", "IDBO"],
            patch_artist=True,
            showmeans=True,
            meanline=True,
        )

        colors = [COLOR_DBO, COLOR_IDBO]
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.65)
        for median in bp["medians"]:
            median.set(color="black", linewidth=1.5)
        for mean in bp["means"]:
            mean.set(color="red", linewidth=1.5, linestyle="--")

        # Use log scale if dynamic range is large and min > 0
        all_vals = np.concatenate([dbo_vals, idbo_vals]) if len(dbo_vals) and len(idbo_vals) else np.array([])
        if len(all_vals) > 0 and np.all(all_vals > 0):
            ratio = np.max(all_vals) / max(np.min(all_vals), 1e-300)
            if ratio > 100:
                ax.set_yscale("log")
                ax.set_ylabel("Best Fitness (log scale)", fontsize=10)
            else:
                ax.set_ylabel("Best Fitness", fontsize=10)
        else:
            ax.set_ylabel("Best Fitness", fontsize=10)

        ax.set_title(f"{func_name} (dim={dim})", fontsize=12, fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.6)

    n_runs = int(df_dim["run"].nunique()) if "run" in df_dim.columns else 0
    run_str = f", M={n_runs} runs" if n_runs > 0 else ""
    fig.suptitle(
        f"Distribution of Best Fitness: DBO vs IDBO (dim={dim}{run_str})",
        fontsize=14,
        fontweight="bold",
    )
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[OK] F2 Boxplot saved to: {out_path}")


def plot_f3_diversity(diversity_csv: Path, out_path: Path, dim: int = 10) -> None:
    """F3: Average diversity IDBO dim=10: Sphere (unimodal) and Rastrigin (multimodal)."""
    if not diversity_csv.is_file():
        print(f"[WARN] Diversity file not found: {diversity_csv}. Skipping F3.")
        return

    df = pd.read_csv(diversity_csv)
    df_dim = df[df["dim"] == dim]
    if df_dim.empty:
        print(f"[WARN] No records found for dim={dim} in {diversity_csv}. Skipping F3.")
        return

    grouped = (
        df_dim.groupby(["function", "iteration"])["diversity"]
        .mean()
        .reset_index()
    )

    sphere_data = grouped[grouped["function"] == "sphere"].sort_values("iteration")
    rastrigin_data = grouped[grouped["function"] == "rastrigin"].sort_values("iteration")

    if sphere_data.empty or rastrigin_data.empty:
        print(f"[WARN] F3 requires both 'sphere' and 'rastrigin' data in {diversity_csv}. Skipping F3.")
        return

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)

    ax.plot(
        sphere_data["iteration"],
        sphere_data["diversity"],
        label="Sphere (Unimodal)",
        color=COLOR_SPHERE,
        linewidth=2.0,
    )
    if not rastrigin_data.empty:
        ax.plot(
            rastrigin_data["iteration"],
            rastrigin_data["diversity"],
            label="Rastrigin (Multimodal)",
            color=COLOR_RASTRIGIN,
            linewidth=2.0,
            linestyle="-.",
        )

    # Threshold indicator
    threshold = 1e-3
    ax.axhline(
        y=threshold,
        color="gray",
        linestyle="--",
        linewidth=1.2,
        label=f"Diversity Threshold ({threshold})",
    )

    ax.set_title(
        f"IDBO Population Diversity Evolution (dim={dim})",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Mean Population Diversity", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=11)

    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[OK] F3 Diversity plot saved to: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Week 5-6 benchmark results.")
    parser.add_argument(
        "--out-dir",
        type=str,
        default="experiments/week5_6",
        help="Directory containing experiment CSVs and to save plots.",
    )
    parser.add_argument("--dim", type=int, default=10, help="Dimension to plot (default: 10)")
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    history_csv = out_dir / "idbo_vs_dbo_history.csv"
    runs_csv = out_dir / "idbo_vs_dbo_runs.csv"
    diversity_csv = out_dir / "idbo_diversity.csv"

    f1_path = out_dir / f"fig_convergence_dim{args.dim}.png"
    f2_path = out_dir / f"fig_boxplot_dim{args.dim}.png"
    f3_path = out_dir / f"fig_diversity_dim{args.dim}.png"

    print("=" * 60)
    print(" PLOTTING DBO vs IDBO RESULTS")
    print(f" Input/Output Directory: {out_dir}")
    print(f" Target Dimension      : {args.dim}")
    print("=" * 60)

    for path in (f1_path, f2_path, f3_path):
        path.unlink(missing_ok=True)

    plot_f1_convergence(history_csv, f1_path, dim=args.dim)
    plot_f2_boxplot(runs_csv, f2_path, dim=args.dim)
    plot_f3_diversity(diversity_csv, f3_path, dim=args.dim)
    print("\n[DONE] All plots generated.")


if __name__ == "__main__":
    main()
