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


# ─── F1: Hội tụ trung bình dim=10 ────────────────────────────────────────────
def plot_convergence(history_csv: Path, out_path: Path) -> None:
    if not history_csv.exists():
        print(f"[SKIP F1] Không tìm thấy {history_csv}")
        return

    df = pd.read_csv(history_csv)
    df = df[df["dim"] == 10]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    axes = axes.flatten()

    for ax, func in zip(axes, FUNC_ORDER):
        for algo in ["dbo", "idbo"]:
            sub = df[(df["function"] == func) & (df["algorithm"] == algo)]
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
        ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim=10)", fontsize=11)
        ax.set_xlabel("Iteration", fontsize=9)
        ax.set_ylabel("Best fitness (log)", fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.tick_params(labelsize=8)

    fig.suptitle("Hội tụ trung bình DBO vs IDBO — dim=10, M=30", fontsize=13, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] F1 saved: {out_path}")


# ─── F2: Boxplot best_fitness dim=10 ─────────────────────────────────────────
def plot_boxplot(runs_csv: Path, out_path: Path) -> None:
    if not runs_csv.exists():
        print(f"[SKIP F2] Không tìm thấy {runs_csv}")
        return

    df = pd.read_csv(runs_csv)
    df = df[df["dim"] == 10]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    axes = axes.flatten()

    for ax, func in zip(axes, FUNC_ORDER):
        data_dbo  = df[(df["function"] == func) & (df["algorithm"] == "dbo")]["best_fitness"].to_numpy()
        data_idbo = df[(df["function"] == func) & (df["algorithm"] == "idbo")]["best_fitness"].to_numpy()

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

        ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim=10)", fontsize=11)
        ax.set_ylabel("Best fitness", fontsize=9)
        ax.tick_params(labelsize=9)

        # Log-scale nếu giá trị không bằng 0 hoàn toàn
        all_vals = np.concatenate([data_dbo, data_idbo])
        if np.any(all_vals > 0):
            try:
                ax.set_yscale("log")
            except Exception:
                pass
        ax.grid(True, axis="y", linestyle=":", alpha=0.5)

    fig.suptitle("Phân bố best fitness DBO vs IDBO — dim=10, M=30", fontsize=13, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] F2 saved: {out_path}")


# ─── F3: Diversity IDBO dim=10 (sphere + rastrigin) ──────────────────────────
def plot_diversity(diversity_csv: Path, out_path: Path) -> None:
    if not diversity_csv.exists():
        print(f"[SKIP F3] Không tìm thấy {diversity_csv}")
        return

    df = pd.read_csv(diversity_csv)
    df = df[df["dim"] == 10]

    target_funcs = ["sphere", "rastrigin"]
    func_colors  = {"sphere": "#2ca02c", "rastrigin": "#d62728"}

    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)

    for func in target_funcs:
        sub = df[df["function"] == func]
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

    # Vẽ đường ngưỡng diversity_threshold = 1e-3
    ax.axhline(1e-3, color="grey", linestyle=":", linewidth=1.2, label="Ngưỡng (1e-3)")

    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Diversity trung bình", fontsize=11)
    ax.set_title("Diversity IDBO — dim=10, M=30  (Sphere vs Rastrigin)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.tick_params(labelsize=9)

    # Y-log nếu diversity về gần 0
    if df["diversity"].min() > 0:
        ax.set_yscale("log")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] F3 saved: {out_path}")


# ─── main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Vẽ 3 hình so sánh DBO vs IDBO tuần 5–6.")
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

    plot_convergence(
        history_csv=out_dir / "idbo_vs_dbo_history.csv",
        out_path=out_dir / "fig_convergence_dim10.png",
    )
    plot_boxplot(
        runs_csv=out_dir / "idbo_vs_dbo_runs.csv",
        out_path=out_dir / "fig_boxplot_dim10.png",
    )
    plot_diversity(
        diversity_csv=out_dir / "idbo_diversity.csv",
        out_path=out_dir / "fig_diversity_dim10.png",
    )

    print("\nXong. Kiểm tra kết quả trong:", out_dir)


if __name__ == "__main__":
    main()
