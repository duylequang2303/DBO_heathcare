"""Week 8 Plotting Script: Visualization of Two-Tier Optimization (DBO vs IDBO).

Generates 3 scientific figures in experiments/week8/:
- W8-F1: experiments/week8/fig_convergence_2tier_p1.png (Outer loop mean convergence)
- W8-F2: experiments/week8/fig_boxplot_2tier_p1.png     (Boxplot comparing best fitness distributions)
- W8-F3: experiments/week8/fig_radar_nutrition_p1.png   (Nutritional radar chart vs target P1)

Usage:
  python scripts/plot_week8.py
  python scripts/plot_week8.py --output-dir experiments/week8
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

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

from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.nutrition import daily_all_targets

COLOR: Dict[str, str] = {"dbo": "#2B5C8F", "idbo": "#D95F02"}
LABEL: Dict[str, str] = {"dbo": "DBO 2-Tier (Gốc)", "idbo": "IDBO 2-Tier (Cải tiến)"}
STYLE: Dict[str, str] = {"dbo": "--", "idbo": "-"}


def get_profile_p1() -> UserProfile:
    """Return standard evaluation profile P1 (Duy).

    Returns:
        UserProfile: Standard user profile.
    """
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


def plot_convergence(hist_df: pd.DataFrame, out_path: Path) -> None:
    """Plot W8-F1: Outer loop mean convergence curves of DBO vs IDBO.

    Args:
        hist_df: DataFrame containing columns ['algo', 'outer_iter', 'best_fitness'].
        out_path: File path to save output figure.
    """
    plt.figure(figsize=(9, 5.5), dpi=300)

    for algo in ["dbo", "idbo"]:
        sub = hist_df[hist_df["algo"] == algo]
        if sub.empty:
            continue

        grouped = sub.groupby("outer_iter")["best_fitness"]
        mean_curve = grouped.mean()
        std_curve = grouped.std().fillna(0.0)
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
        "W8-F1: Đường cong hội tụ tầng ngoài (Outer Loop) Tối ưu 2 tầng Profile P1\n(Không gian tìm kiếm tổ hợp từ 15.929 món ăn)",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    plt.xlabel("Số vòng lặp tầng ngoài (Outer Iteration)", fontsize=11, labelpad=8)
    plt.ylabel("Hàm mục tiêu Fitness (Càng cao càng tốt)", fontsize=11, labelpad=8)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(frameon=True, facecolor="white", edgecolor="#D3D3D3", fontsize=10, loc="lower right")
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_boxplot(runs_df: pd.DataFrame, out_path: Path) -> None:
    """Plot W8-F2: Boxplot comparing final best fitness distributions.

    Args:
        runs_df: DataFrame containing columns ['algo', 'best_fitness'].
        out_path: File path to save output figure.
    """
    plt.figure(figsize=(7, 5.5), dpi=300)

    algos = ["dbo", "idbo"]
    data = []
    labels = []
    colors = []

    for algo in algos:
        sub = runs_df[runs_df["algo"] == algo]
        if not sub.empty:
            data.append(sub["best_fitness"].values)
            labels.append(LABEL.get(algo, algo.upper()))
            colors.append(COLOR[algo])

    if not data:
        print("[WARN] No data available for boxplot.")
        plt.close()
        return

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

    # Overlay jittered data points and mean markers
    for idx, (vals, col) in enumerate(zip(data, colors), start=1):
        x_jitter = np.random.default_rng(idx).normal(idx, 0.04, size=len(vals))
        plt.scatter(x_jitter, vals, color=col, alpha=0.85, s=35, edgecolors="#111111", zorder=3)
        mean_val = float(np.mean(vals))
        plt.scatter(
            [idx],
            [mean_val],
            color="white",
            marker="D",
            s=55,
            edgecolors="black",
            linewidths=1.5,
            zorder=4,
            label="Mean" if idx == 1 else None,
        )

    plt.title(
        "W8-F2: Phân bố Fitness Tối ưu Thực đơn 2 Tầng (Profile P1)\n(Mộc phân vị & Giá trị trung bình qua các runs độc lập)",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    plt.ylabel("Hàm mục tiêu Fitness (Càng cao càng tốt)", fontsize=11, labelpad=8)
    plt.grid(True, linestyle=":", alpha=0.6, axis="y")
    plt.legend(frameon=True, facecolor="white", edgecolor="#D3D3D3", fontsize=10, loc="lower left")
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_radar(runs_df: pd.DataFrame, out_path: Path) -> None:
    """Plot W8-F3: Radar chart comparing nutrient fulfillment vs target P1.

    Args:
        runs_df: DataFrame containing run nutrition totals.
        out_path: File path to save output figure.
    """
    profile = get_profile_p1()
    targets = daily_all_targets(profile)

    nutrients = ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g"]
    labels = ["Calories\n(kcal)", "Protein\n(g)", "Carbs\n(g)", "Fat\n(g)", "Fiber\n(g)"]
    num_vars = len(nutrients)

    # Angles for radar plot (in radians)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Complete circle

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True), dpi=300)

    # Baseline target 100% circle
    target_vals = [100.0] * num_vars + [100.0]
    ax.plot(angles, target_vals, color="#222222", linestyle="--", linewidth=1.8, label="Mục tiêu Target P1 (100%)")

    for algo in ["dbo", "idbo"]:
        sub = runs_df[runs_df["algo"] == algo]
        if sub.empty:
            continue

        pct_vals = []
        for nut in nutrients:
            mean_nut = float(sub[nut].mean())
            tgt = float(targets[nut])
            pct = (mean_nut / tgt) * 100.0 if tgt > 0 else 100.0
            pct_vals.append(pct)

        pct_vals += pct_vals[:1]  # Complete loop

        ax.plot(
            angles,
            pct_vals,
            color=COLOR[algo],
            linewidth=2.2,
            linestyle=STYLE[algo],
            label=f"{LABEL.get(algo, algo.upper())}",
        )
        ax.fill(angles, pct_vals, color=COLOR[algo], alpha=0.18)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=10, fontweight="bold")
    ax.set_rlabel_position(30)
    ax.set_ylim(0, 140)
    ax.set_yticks([25, 50, 75, 100, 125])
    ax.set_yticklabels(["25%", "50%", "75%", "100%", "125%"], fontsize=8, color="#555555")
    ax.grid(True, linestyle=":", alpha=0.7)

    plt.title(
        "W8-F3: Radar Dinh Dưỡng Thực Đơn Tối Ưu So Với Mục Tiêu P1\n(Tỷ lệ % đáp ứng chuẩn dinh dưỡng khuyến nghị)",
        fontsize=12,
        fontweight="bold",
        pad=22,
    )
    plt.legend(frameon=True, facecolor="white", edgecolor="#D3D3D3", fontsize=9, loc="lower right", bbox_to_anchor=(1.25, 0.05))
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[SAVED] {out_path}")


def main() -> None:
    """Main execution function for plotting Week 8 results."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Week 8 Plotting: W8-F1, W8-F2, W8-F3")
    parser.add_argument("--runs-file", type=str, default="experiments/week8/two_tier_runs.csv", help="Runs CSV file")
    parser.add_argument("--history-file", type=str, default="experiments/week8/two_tier_history.csv", help="History CSV file")
    parser.add_argument("--output-dir", type=str, default="experiments/week8", help="Output directory for figures")

    args = parser.parse_args()

    runs_path = ROOT / args.runs_file
    hist_path = ROOT / args.history_file
    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not runs_path.exists() or not hist_path.exists():
        print(f"[ERROR] Required CSV files not found: {runs_path} or {hist_path}", file=sys.stderr)
        print("Please run `python scripts/experiment_week8.py` first.", file=sys.stderr)
        sys.exit(1)

    runs_df = pd.read_csv(runs_path)
    hist_df = pd.read_csv(hist_path)

    print("=" * 80)
    print("PLOTTING WEEK 8 FIGURES (W8-F1, W8-F2, W8-F3)")
    print(f"Loaded runs data: {len(runs_df)} rows from {runs_path}")
    print(f"Loaded history data: {len(hist_df)} rows from {hist_path}")
    print("=" * 80)

    plot_convergence(hist_df, out_dir / "fig_convergence_2tier_p1.png")
    plot_boxplot(runs_df, out_dir / "fig_boxplot_2tier_p1.png")
    plot_radar(runs_df, out_dir / "fig_radar_nutrition_p1.png")

    print("\n[COMPLETE] All 3 Week 8 figures generated successfully!")


if __name__ == "__main__":
    main()
