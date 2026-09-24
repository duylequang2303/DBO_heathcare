"""Vẽ 3 hình so sánh DBO vs IDBO — Tuần 5–6.

Yêu cầu: đã chạy experiment_idbo.py để có CSV trong experiments/week5_6/.

Hình xuất ra:
  F1 — fig_convergence_dim10.png   : Hội tụ trung bình, 6 subplot, log-Y
  F2 — fig_boxplot_dim10.png       : Boxplot best_fitness, 6 hàm
  F3 — fig_diversity_dim10.png     : Diversity IDBO trên sphere và rastrigin

Usage:
    python scripts/plot_week5_6.py
    python scripts/plot_week5_6.py --out-dir experiments/week5_6
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
    matplotlib.use("Agg")          # non-interactive backend (server-safe)
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
except ImportError:
    print("[ERROR] matplotlib not installed. Run: pip install matplotlib", file=sys.stderr)
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("[ERROR] pandas not installed. Run: pip install pandas", file=sys.stderr)
    sys.exit(1)

# ─── màu / style ────────────────────────────────────────────────────────────
COLOR = {"dbo": "#4C72B0", "idbo": "#DD8452"}
STYLE = {"dbo": "--", "idbo": "-"}
FUNC_ORDER = ["sphere", "schwefel_2_22", "rosenbrock", "rastrigin", "ackley", "griewank"]
FUNC_LABEL = {
    "sphere": "Sphere",
    "schwefel_2_22": "Schwefel 2.22",
    "rosenbrock": "Rosenbrock",
    "rastrigin": "Rastrigin",
    "ackley": "Ackley",
    "griewank": "Griewank",
}


def _safe_log(arr: np.ndarray) -> np.ndarray:
    """Thay giá trị 0 bằng NaN để tránh log(0) trên trục Y."""
    out = arr.copy().astype(float)
    out[out <= 0] = np.nan
    return out


# ─── F1: Hội tụ trung bình DBO vs IDBO theo dim ─────────────────────────────
def plot_convergence_for_dim(df: pd.DataFrame, dim: int, out_path: Path) -> None:
    sub_dim = df[df["dim"] == dim]
    if sub_dim.empty:
        return

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    axes = axes.flatten()

    for ax, func in zip(axes, FUNC_ORDER):
        for algo in ["dbo", "idbo"]:
            sub = sub_dim[(sub_dim["function"] == func) & (sub_dim["algorithm"] == algo)]
            if sub.empty:
                continue
            mean_curve = (
                sub.groupby("iteration")["best_fitness"]
                .mean()
                .sort_index()
            )
            x = mean_curve.index.to_numpy()
            y = _safe_log(mean_curve.to_numpy())
            ax.semilogy(
                x, y,
                linestyle=STYLE[algo],
                color=COLOR[algo],
                linewidth=1.8,
                label=algo.upper(),
            )
        ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim={dim})", fontsize=11)
        ax.set_xlabel("Iteration", fontsize=9)
        ax.set_ylabel("Best fitness (log)", fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.tick_params(labelsize=8)

    fig.suptitle(f"Hội tụ trung bình DBO vs IDBO — dim={dim}, M=30", fontsize=13, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] F1 Convergence dim={dim} saved: {out_path}")


# ─── F2: Boxplot best_fitness DBO vs IDBO theo dim ──────────────────────────
def plot_boxplot_for_dim(df: pd.DataFrame, dim: int, out_path: Path) -> None:
    sub_dim = df[df["dim"] == dim]
    if sub_dim.empty:
        return

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    axes = axes.flatten()

    for ax, func in zip(axes, FUNC_ORDER):
        data_dbo  = sub_dim[(sub_dim["function"] == func) & (sub_dim["algorithm"] == "dbo")]["best_fitness"].to_numpy()
        data_idbo = sub_dim[(sub_dim["function"] == func) & (sub_dim["algorithm"] == "idbo")]["best_fitness"].to_numpy()

        try:
            bp = ax.boxplot(
                [data_dbo, data_idbo],
                tick_labels=["DBO", "IDBO"],
                patch_artist=True,
                medianprops=dict(color="black", linewidth=2),
                widths=0.5,
            )
        except TypeError:
            bp = ax.boxplot(
                [data_dbo, data_idbo],
                labels=["DBO", "IDBO"],
                patch_artist=True,
                medianprops=dict(color="black", linewidth=2),
                widths=0.5,
            )
        for patch, color in zip(bp["boxes"], [COLOR["dbo"], COLOR["idbo"]]):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)

        ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim={dim})", fontsize=11)
        ax.set_ylabel("Best fitness", fontsize=9)
        ax.tick_params(labelsize=9)

        all_vals = np.concatenate([data_dbo, data_idbo])
        if np.any(all_vals > 0):
            try:
                ax.set_yscale("log")
            except Exception:
                pass
        ax.grid(True, axis="y", linestyle=":", alpha=0.5)

    fig.suptitle(f"Phân bố best fitness DBO vs IDBO — dim={dim}, M=30", fontsize=13, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] F2 Boxplot dim={dim} saved: {out_path}")


# ─── F3: Diversity IDBO theo dim (sphere + rastrigin) ───────────────────────
def plot_diversity_for_dim(df: pd.DataFrame, dim: int, out_path: Path) -> None:
    sub_dim = df[df["dim"] == dim]
    if sub_dim.empty:
        return

    target_funcs = ["sphere", "rastrigin"]
    func_colors  = {"sphere": "#2ca02c", "rastrigin": "#d62728"}

    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)

    for func in target_funcs:
        sub = sub_dim[sub_dim["function"] == func]
        if sub.empty:
            continue
        mean_div = sub.groupby("iteration")["diversity"].mean().sort_index()
        x = mean_div.index.to_numpy()
        y = mean_div.to_numpy()
        ax.plot(
            x, y,
            color=func_colors[func],
            linewidth=2.0,
            label=FUNC_LABEL.get(func, func),
        )

    ax.axhline(1e-3, color="grey", linestyle=":", linewidth=1.2, label="Ngưỡng kích hoạt (1e-3)")

    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Diversity trung bình", fontsize=11)
    ax.set_title(f"Diversity IDBO — dim={dim}, M=30  (Sphere vs Rastrigin)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.tick_params(labelsize=9)

    if sub_dim["diversity"].min() > 0:
        ax.set_yscale("log")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] F3 Diversity dim={dim} saved: {out_path}")


# ─── main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Vẽ hình so sánh DBO vs IDBO tuần 5–6 cho mọi dim.")
    parser.add_argument(
        "--out-dir",
        type=str,
        default="experiments/week5_6",
        help="Thư mục chứa CSV đầu vào và xuất PNG (default: experiments/week5_6)",
    )
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    if not out_dir.exists():
        print(f"[ERROR] Thư mục '{out_dir}' không tồn tại. Hãy chạy experiment_idbo.py trước.")
        sys.exit(1)

    print(f"Input/output dir: {out_dir}\n")

    dims = [10, 30, 50]

    # F1 Convergence
    history_csv = out_dir / "idbo_vs_dbo_history.csv"
    if history_csv.exists():
        df_hist = pd.read_csv(history_csv)
        for d in dims:
            plot_convergence_for_dim(df_hist, d, out_path=out_dir / f"fig_convergence_dim{d}.png")
    else:
        print(f"[SKIP F1] Không tìm thấy {history_csv}")

    # F2 Boxplot
    runs_csv = out_dir / "idbo_vs_dbo_runs.csv"
    if runs_csv.exists():
        df_runs = pd.read_csv(runs_csv)
        for d in dims:
            plot_boxplot_for_dim(df_runs, d, out_path=out_dir / f"fig_boxplot_dim{d}.png")
    else:
        print(f"[SKIP F2] Không tìm thấy {runs_csv}")

    # F3 Diversity
    diversity_csv = out_dir / "idbo_diversity.csv"
    if diversity_csv.exists():
        df_div = pd.read_csv(diversity_csv)
        for d in dims:
            plot_diversity_for_dim(df_div, d, out_path=out_dir / f"fig_diversity_dim{d}.png")
    else:
        print(f"[SKIP F3] Không tìm thấy {diversity_csv}")

    print("\nHoàn tất sinh toàn bộ hình ảnh cho các dims (10, 30, 50).")


if __name__ == "__main__":
    main()
