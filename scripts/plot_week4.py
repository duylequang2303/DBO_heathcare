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
    for name in ["dbo_history.csv", "dbo_history_dim10.csv", "idbo_vs_dbo_history.csv"]:
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


# ─── W4-F1: Hội tụ DBO trung bình cho từng dim ──────────────────────────────
def plot_convergence_for_dim(df: pd.DataFrame, dim: int, out_path: Path) -> None:
    sub_dim = df[df["dim"] == dim]
    if sub_dim.empty:
        return

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    axes = axes.flatten()

    for ax, func in zip(axes, FUNC_ORDER):
        sub = sub_dim[sub_dim["function"] == func]
        if sub.empty:
            ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim={dim})", fontsize=11)
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            continue
        mean_curve = sub.groupby("iteration")["best_fitness"].mean().sort_index()
        x = mean_curve.index.to_numpy()
        y = mean_curve.to_numpy().copy().astype(float)
        y[y <= 0] = np.nan
        ax.semilogy(x, y, color=DBO_COLOR, linewidth=2.0, label=f"DBO (dim={dim})")
        ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim={dim})", fontsize=11)
        ax.set_xlabel("Iteration", fontsize=9)
        ax.set_ylabel("Best fitness (log)", fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.tick_params(labelsize=8)

    fig.suptitle(f"DBO — Hội tụ trung bình, dim={dim}, M=30", fontsize=13, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Convergence dim={dim} saved: {out_path}")


# ─── Hội tụ DBO so sánh đồng thời các dimensions (10, 30, 50) ───────────────
def plot_convergence_multidim(df: pd.DataFrame, dims: list[int], out_path: Path) -> None:
    DIM_COLORS = {10: "#2b5c8f", 30: "#d95f02", 50: "#7570b3"}
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    axes = axes.flatten()

    for ax, func in zip(axes, FUNC_ORDER):
        for d in dims:
            sub = df[(df["function"] == func) & (df["dim"] == d)]
            if sub.empty:
                continue
            mean_curve = sub.groupby("iteration")["best_fitness"].mean().sort_index()
            x = mean_curve.index.to_numpy()
            y = mean_curve.to_numpy().copy().astype(float)
            y[y <= 0] = np.nan
            ax.semilogy(x, y, color=DIM_COLORS.get(d, "#333333"), linewidth=1.8, label=f"Dim {d}")

        ax.set_title(FUNC_LABEL.get(func, func), fontsize=11, fontweight="bold")
        ax.set_xlabel("Iteration", fontsize=9)
        ax.set_ylabel("Best fitness (log)", fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.tick_params(labelsize=8)

    fig.suptitle("DBO — So sánh tiến trình hội tụ qua các số chiều (Dim 10, 30, 50), M=30", fontsize=14, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Multi-dim convergence saved: {out_path}")


# ─── W4-F2: Boxplot best_fitness DBO cho từng dim ───────────────────────────
def plot_boxplot_for_dim(df: pd.DataFrame, dim: int, out_path: Path) -> None:
    sub_dim = df[df["dim"] == dim]
    if sub_dim.empty:
        return

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    axes = axes.flatten()

    for ax, func in zip(axes, FUNC_ORDER):
        data = sub_dim[sub_dim["function"] == func]["best_fitness"].to_numpy()
        if len(data) == 0:
            ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim={dim})", fontsize=11)
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            continue
        try:
            bp = ax.boxplot([data], tick_labels=[f"Dim {dim}"], patch_artist=True, widths=0.4,
                            medianprops=dict(color="black", linewidth=2))
        except TypeError:
            bp = ax.boxplot([data], labels=[f"Dim {dim}"], patch_artist=True, widths=0.4,
                            medianprops=dict(color="black", linewidth=2))
        bp["boxes"][0].set_facecolor(DBO_COLOR)
        bp["boxes"][0].set_alpha(0.75)
        ax.set_title(f"{FUNC_LABEL.get(func, func)}  (dim={dim})", fontsize=11)
        ax.set_ylabel("Best fitness", fontsize=9)
        ax.tick_params(labelsize=9)
        if np.any(data > 0):
            try:
                ax.set_yscale("log")
            except Exception:
                pass
        ax.grid(True, axis="y", linestyle=":", alpha=0.5)

    fig.suptitle(f"DBO — Phân bố best fitness, dim={dim}, M=30", fontsize=13, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Boxplot dim={dim} saved: {out_path}")


# ─── Boxplot DBO so sánh đồng thời 3 dimensions (10, 30, 50) ────────────────
def plot_boxplot_multidim(df: pd.DataFrame, dims: list[int], out_path: Path) -> None:
    colors = ["#2b5c8f", "#d95f02", "#7570b3"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    axes = axes.flatten()

    for ax, func in zip(axes, FUNC_ORDER):
        data_per_dim = []
        labels = []
        for d in dims:
            sub = df[(df["function"] == func) & (df["dim"] == d)]["best_fitness"].to_numpy()
            if len(sub) > 0:
                data_per_dim.append(sub)
                labels.append(f"D{d}")
            else:
                data_per_dim.append(np.array([0.0]))
                labels.append(f"D{d}")

        try:
            bp = ax.boxplot(data_per_dim, tick_labels=labels, patch_artist=True, widths=0.5,
                            medianprops=dict(color="black", linewidth=1.5))
        except TypeError:
            bp = ax.boxplot(data_per_dim, labels=labels, patch_artist=True, widths=0.5,
                            medianprops=dict(color="black", linewidth=1.5))

        for patch, color in zip(bp["boxes"], colors[:len(data_per_dim)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_title(FUNC_LABEL.get(func, func), fontsize=11, fontweight="bold")
        ax.set_ylabel("Best fitness", fontsize=9)
        ax.tick_params(labelsize=9)
        all_vals = np.concatenate(data_per_dim)
        if np.any(all_vals > 0):
            try:
                ax.set_yscale("log")
            except Exception:
                pass
        ax.grid(True, axis="y", linestyle=":", alpha=0.5)

    fig.suptitle("DBO — Phân bố sai số qua các số chiều (Dim 10, 30, 50), M=30", fontsize=14, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Multi-dim boxplot saved: {out_path}")


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

    dims = [10, 30, 50]

    if history_csv:
        df_hist = pd.read_csv(history_csv)
        if "algorithm" in df_hist.columns:
            df_hist = df_hist[df_hist["algorithm"] == "dbo"]
        for d in dims:
            plot_convergence_for_dim(df_hist, d, out_dir / f"fig_convergence_dim{d}.png")
        plot_convergence_multidim(df_hist, dims, out_dir / "fig_convergence_multidim.png")
    else:
        print("[SKIP W4-F1] Không có history CSV")

    if runs_csv:
        df_runs = pd.read_csv(runs_csv)
        if "algorithm" in df_runs.columns:
            df_runs = df_runs[df_runs["algorithm"] == "dbo"]
        for d in dims:
            plot_boxplot_for_dim(df_runs, d, out_dir / f"fig_boxplot_dim{d}.png")
        plot_boxplot_multidim(df_runs, dims, out_dir / "fig_boxplot_multidim.png")
        print_summary_table(runs_csv)


if __name__ == "__main__":
    main()
