"""Week 7 Plotting Script: Visualization of Menu Optimization (DBO vs IDBO).

Generates:
  - W7-F1: experiments/week7/fig_convergence_p1.png (Mean convergence curve)
  - W7-F2: experiments/week7/fig_boxplot_p1.png     (Boxplot of best fitness)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("[ERROR] matplotlib not installed. Run: pip install matplotlib", file=sys.stderr)
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("[ERROR] pandas not installed. Run: pip install pandas", file=sys.stderr)
    sys.exit(1)


COLOR = {"dbo": "#2B5C8F", "idbo": "#D95F02"}
LABEL = {"dbo": "DBO (Gốc)", "idbo": "IDBO (Cải tiến)"}
STYLE = {"dbo": "--", "idbo": "-"}


def plot_convergence(hist_df: pd.DataFrame, out_path: Path, max_iter: int = 200, m_runs: int = 10) -> None:
    """Plot W7-F1: Mean convergence curves of DBO vs IDBO on Profile P1."""
    plt.figure(figsize=(9, 5.5), dpi=300)

    for algo in ["dbo", "idbo"]:
        sub = hist_df[hist_df["algorithm"] == algo]
        if sub.empty:
            continue

        # Group by iteration across runs
        grouped = sub.groupby("iteration")["fitness"]
        mean_curve = grouped.mean()
        std_curve = grouped.std().fillna(0)
        iters = mean_curve.index.values

        plt.plot(
            iters,
            mean_curve.values,
            label=f"{LABEL.get(algo, algo.upper())} (Mean)",
            color=COLOR[algo],
            linestyle=STYLE[algo],
            linewidth=2.2,
        )
        plt.fill_between(
            iters,
            mean_curve.values - std_curve.values,
            mean_curve.values + std_curve.values,
            color=COLOR[algo],
            alpha=0.18,
            label=f"±1 SD {LABEL.get(algo, algo.upper())}",
        )

    plt.title(
        f"W7-F1: Đường cong hội tụ tối ưu thực đơn Profile P1\n(max_iter={max_iter}, M={m_runs} runs)",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    plt.xlabel("Số vòng lặp (Iteration)", fontsize=11, labelpad=8)
    plt.ylabel("Hàm mục tiêu Fitness gốc (Càng cao càng tốt)", fontsize=11, labelpad=8)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(frameon=True, facecolor="white", edgecolor="#D3D3D3", fontsize=10, loc="lower right")
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved convergence plot to {out_path}")


def plot_boxplot(runs_df: pd.DataFrame, out_path: Path, max_iter: int = 200, m_runs: int = 10) -> None:
    """Plot W7-F2: Boxplot comparing final best fitness distributions."""
    plt.figure(figsize=(7, 5.5), dpi=300)

    algos = ["dbo", "idbo"]
    data = []
    labels = []
    colors = []

    for algo in algos:
        sub = runs_df[runs_df["algorithm"] == algo]
        if not sub.empty:
            data.append(sub["best_fitness"].values)
            labels.append(LABEL.get(algo, algo.upper()))
            colors.append(COLOR[algo])

    bp = plt.boxplot(
        data,
        tick_labels=labels,
        patch_artist=True,
        widths=0.45,
        medianprops=dict(color="black", linewidth=2.0),
        whiskerprops=dict(color="#555555", linewidth=1.5),
        capprops=dict(color="#555555", linewidth=1.5),
        flierprops=dict(marker="o", markerfacecolor="red", markersize=6, alpha=0.7),
    )

    for patch, col in zip(bp["boxes"], colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.65)
        patch.set_edgecolor("#333333")
        patch.set_linewidth(1.5)

    # Overlay jittered data points
    for idx, d in enumerate(data, start=1):
        rng = np.random.default_rng(42 + idx)
        jitter = rng.uniform(-0.08, 0.08, size=len(d))
        plt.scatter(
            np.full_like(d, idx) + jitter,
            d,
            color=colors[idx - 1],
            edgecolor="black",
            s=45,
            alpha=0.85,
            zorder=3,
        )

    plt.title(
        f"W7-F2: Phân bố Best Fitness thực đơn Profile P1\n(max_iter={max_iter}, M={m_runs} runs)",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    plt.ylabel("Best Fitness gốc ([-100, 100], Càng cao càng tốt)", fontsize=11, labelpad=8)
    plt.grid(True, linestyle=":", alpha=0.6, axis="y")
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved boxplot to {out_path}")


def main():
    """Load Week 7 experiment CSVs and generate convergence and boxplot figures."""
    parser = argparse.ArgumentParser(description="Generate Week 7 Plots")
    parser.add_argument("--exp-dir", type=str, default=None, help="Directory containing experiment CSVs")
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir) if args.exp_dir else ROOT / "experiments" / "week7"
    runs_csv = exp_dir / "menu_runs.csv"
    hist_csv = exp_dir / "menu_history.csv"

    if not runs_csv.exists() or not hist_csv.exists():
        print(f"[ERROR] Required CSV files not found in {exp_dir}", file=sys.stderr)
        print("Please run `python scripts/experiment_week7.py` first.", file=sys.stderr)
        sys.exit(1)

    runs_df = pd.read_csv(runs_csv)
    hist_df = pd.read_csv(hist_csv)

    m_runs = int(runs_df["run"].max()) if not runs_df.empty else 10
    max_iter = int(hist_df["iteration"].max()) if not hist_df.empty else 200

    plot_convergence(hist_df, exp_dir / "fig_convergence_p1.png", max_iter=max_iter, m_runs=m_runs)
    plot_boxplot(runs_df, exp_dir / "fig_boxplot_p1.png", max_iter=max_iter, m_runs=m_runs)
    print("All Week 7 plots generated successfully!")


if __name__ == "__main__":
    main()
