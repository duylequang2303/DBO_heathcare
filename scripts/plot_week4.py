"""Vẽ hình W4-F1 và W4-F2 cho báo cáo DBO tuần 4.

Yêu cầu: đã chạy experiment_dbo.py để có CSV trong experiments/week4/.

Usage:
    python scripts/plot_week4.py
    python scripts/plot_week4.py --out-dir experiments/week4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("[ERROR] pip install matplotlib", file=sys.stderr)
    sys.exit(1)

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("[ERROR] pip install pandas numpy", file=sys.stderr)
    sys.exit(1)

FUNC_ORDER = ["sphere", "schwefel_2_22", "rosenbrock", "rastrigin", "ackley", "griewank"]
FUNC_LABEL = {
    "sphere": "Sphere",
    "schwefel_2_22": "Schwefel 2.22",
    "rosenbrock": "Rosenbrock",
    "rastrigin": "Rastrigin",
    "ackley": "Ackley",
    "griewank": "Griewank",
}
DBO_COLOR = "#4C72B0"


def _find_history_csv(out_dir: Path) -> Path | None:
    for name in ["dbo_history_dim10.csv", "idbo_vs_dbo_history.csv"]:
        p = out_dir / name
        if p.exists():
            return p
    return None


def _find_runs_csv(out_dir: Path) -> Path | None:
    for name in ["dbo_benchmark_runs.csv", "idbo_vs_dbo_runs.csv"]:
        p = out_dir / name
        if p.exists():
            return p
    return None


# ─── W4-F1: Hội tụ DBO trung bình dim=10 ─────────────────────────────────────
def plot_convergence_week4(history_csv: Path, out_path: Path) -> None:
    if not history_csv.exists():
        print(f"[SKIP W4-F1] Không tìm thấy {history_csv}")
        return

    df = pd.read_csv(history_csv)
    df = df[df["dim"] == 10]
    if "algorithm" in df.columns:
        df = df[df["algorithm"] == "dbo"]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    axes = axes.flatten()

    for ax, func in zip(axes, FUNC_ORDER):
        sub = df[df["function"] == func]
        if sub.empty:
            ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim=10)", fontsize=11)
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            continue
        mean_curve = sub.groupby("iteration")["best_fitness"].mean().sort_index()
        x = mean_curve.index.to_numpy()
        y = mean_curve.to_numpy().copy().astype(float)
        y[y <= 0] = np.nan
        ax.semilogy(x, y, color=DBO_COLOR, linewidth=2.0, label="DBO")
        ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim=10)", fontsize=11)
        ax.set_xlabel("Iteration", fontsize=9)
        ax.set_ylabel("Best fitness (log)", fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.tick_params(labelsize=8)

    fig.suptitle("DBO — Hội tụ trung bình, dim=10, M=30", fontsize=13, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] W4-F1 saved: {out_path}")


# ─── W4-F2: Boxplot best_fitness DBO dim=10 ──────────────────────────────────
def plot_boxplot_week4(runs_csv: Path, out_path: Path) -> None:
    if not runs_csv.exists():
        print(f"[SKIP W4-F2] Không tìm thấy {runs_csv}")
        return

    df = pd.read_csv(runs_csv)
    df = df[df["dim"] == 10]
    if "algorithm" in df.columns:
        df = df[df["algorithm"] == "dbo"]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    axes = axes.flatten()

    for ax, func in zip(axes, FUNC_ORDER):
        data = df[df["function"] == func]["best_fitness"].to_numpy()
        if len(data) == 0:
            ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim=10)", fontsize=11)
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            continue
        try:
            bp = ax.boxplot([data], tick_labels=["DBO"], patch_artist=True, widths=0.4,
                            medianprops=dict(color="black", linewidth=2))
        except TypeError:
            bp = ax.boxplot([data], labels=["DBO"], patch_artist=True, widths=0.4,
                            medianprops=dict(color="black", linewidth=2))
        bp["boxes"][0].set_facecolor(DBO_COLOR)
        bp["boxes"][0].set_alpha(0.75)
        ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim=10)", fontsize=11)
        ax.set_ylabel("Best fitness", fontsize=9)
        ax.tick_params(labelsize=9)
        if np.any(data > 0):
            try:
                ax.set_yscale("log")
            except Exception:
                pass
        ax.grid(True, axis="y", linestyle=":", alpha=0.5)

    fig.suptitle("DBO — Phân bố best fitness, dim=10, M=30", fontsize=13, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] W4-F2 saved: {out_path}")


# ─── Bảng kết quả tổng hợp ra console ────────────────────────────────────────
def print_summary_table(runs_csv: Path) -> None:
    if not runs_csv.exists():
        return
    df = pd.read_csv(runs_csv)
    if "algorithm" in df.columns:
        df = df[df["algorithm"] == "dbo"]

    print("\n" + "="*80)
    print("KẾT QUẢ DBO — M=30 lần chạy độc lập")
    print("="*80)
    header = f"{'Hàm':<16} {'Dim':>4}  {'Best':>14} {'Mean':>14} {'Std':>14} {'Worst':>14}"
    print(header)
    print("-"*80)
    for func in FUNC_ORDER:
        for dim in sorted(df["dim"].unique()):
            sub = df[(df["function"] == func) & (df["dim"] == dim)]["best_fitness"].to_numpy()
            if len(sub) == 0:
                continue
            print(f"{FUNC_LABEL.get(func, func):<16} {dim:>4}  "
                  f"{np.min(sub):>14.4e} {np.mean(sub):>14.4e} "
                  f"{np.std(sub):>14.4e} {np.max(sub):>14.4e}")
    print("="*80 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Vẽ hình tuần 4: W4-F1 và W4-F2.")
    parser.add_argument("--out-dir", type=str, default="experiments/week4")
    args = parser.parse_args()
    out_dir = ROOT / args.out_dir

    if not out_dir.exists():
        print(f"[ERROR] '{out_dir}' không tồn tại. Chạy experiment_dbo.py trước.")
        sys.exit(1)

    history_csv = _find_history_csv(out_dir)
    runs_csv = _find_runs_csv(out_dir)

    print(f"Input dir : {out_dir}")
    print(f"History   : {history_csv}")
    print(f"Runs      : {runs_csv}\n")

    if history_csv:
        plot_convergence_week4(history_csv, out_dir / "fig_convergence_dim10.png")
    else:
        print("[SKIP W4-F1] Không có history CSV — chạy experiment_dbo.py với --save-history")

    if runs_csv:
        plot_boxplot_week4(runs_csv, out_dir / "fig_boxplot_dim10.png")
        print_summary_table(runs_csv)


if __name__ == "__main__":
    main()
