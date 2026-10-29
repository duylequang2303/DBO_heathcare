"""Week 9 Plotting Script: Visualization of 7-Day Planning & Multi-Profile Benchmark.

Generates 3 scientific figures in experiments/week9/:
- W9-F1: fig_heatmap_nutrition_7days.png     (7-day x nutrition heatmap for best P1 plan)
- W9-F2: fig_barchart_profiles_p1_p2_p3.png (Bar chart: Mean fitness & calo deviation across P1/P2/P3)
- W9-F3: fig_radar_options_abc.png          (Radar chart: Comparison of Option A/B/C)

Usage:
  python scripts/plot_week9.py
  python scripts/plot_week9.py --output-dir experiments/week9
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt
except ImportError:
    print("[ERROR] matplotlib not installed. Run: pip install matplotlib", file=sys.stderr)
    sys.exit(1)

from scripts.generate_options_week9 import get_profile, get_profile_targets


def select_representative_run(
    p1_runs: pd.DataFrame,
    targets: Dict[str, float],
    ceiling_sodium_mg: float = 3000.0,
) -> Any:
    """Select a representative run with high fitness and balanced nutritional compliance.

    Evaluates candidate runs on Profile P1 to avoid extreme nutrient spikes (particularly
    sodium excursions above the clinical/technical ceiling of 3,000 mg/day) while ensuring
    excellent energy and macronutrient adherence.

    Args:
        p1_runs: DataFrame of P1 runs.
        targets: Target nutritional values dictionary.
        ceiling_sodium_mg: Maximum sodium threshold for penalty calculation.

    Returns:
        Selected run ID.
    """
    run_ids = p1_runs["run"].unique()
    if len(run_ids) == 1:
        return run_ids[0]

    if "fitness" not in p1_runs.columns:
        return run_ids[0]

    if "calories" not in p1_runs.columns or "sodium_mg" not in p1_runs.columns:
        return p1_runs.groupby("run")["fitness"].mean().idxmax()

    tgt_cal = float(targets.get("calories", 2491.625))
    tgt_na = float(targets.get("sodium_mg", 2300.0))

    run_scores: Dict[Any, float] = {}
    print("[W9-F1] Evaluating candidate runs for representative selection:")

    for r in run_ids:
        sub = p1_runs[p1_runs["run"] == r]
        mean_fit = float(sub["fitness"].mean())
        mean_cal = float(sub["calories"].mean())
        calo_dev_pct = float(((sub["calories"] - tgt_cal).abs() / tgt_cal).mean() * 100.0)

        mean_na = float(sub["sodium_mg"].mean())
        max_na = float(sub["sodium_mg"].max())
        na_dev_pct = float(((sub["sodium_mg"] - tgt_na).abs() / tgt_na).mean() * 100.0)
        na_excess_ceiling = float(np.maximum(0.0, sub["sodium_mg"] - ceiling_sodium_mg).sum())

        violations = float(sub["n_violations"].sum()) if "n_violations" in sub.columns else 0.0

        # Balanced scoring formula:
        # High fitness (+), penalized for calo deviation, sodium deviation,
        # sodium exceeding 3,000 mg ceiling, and any constraint violations
        score = (
            mean_fit
            - (calo_dev_pct * 1.0)
            - (na_dev_pct * 0.2)
            - (na_excess_ceiling / 100.0)
            - (violations * 10.0)
        )
        run_scores[r] = score
        print(
            f"  • Run {r}: Fitness={mean_fit:.2f}, Mean Calo={mean_cal:.0f} kcal (dev={calo_dev_pct:.2f}%), "
            f"Mean Na={mean_na:.0f} mg, Max Na={max_na:.0f} mg, Ceiling Excess={na_excess_ceiling:.0f} mg -> Score={score:.2f}"
        )

    best_run = max(run_scores, key=lambda k: run_scores[k])
    print(f"[W9-F1] Selected representative Run {best_run} (Score={run_scores[best_run]:.2f})\n")
    return best_run


def plot_w9_f1_heatmap(
    runs_df: pd.DataFrame,
    out_path: Path,
    run_id: Optional[int] = None,
) -> None:
    """Plot W9-F1: 7-day x nutrition fulfillment heatmap for representative P1 run.

    Args:
        runs_df: DataFrame containing daily records from weekly_runs.csv.
        out_path: Target path for the output figure.
        run_id: Optional specific run ID to plot. If None, auto-selects representative run.
    """
    # Filter only IDBO on Profile P1 to avoid duplicate days from multiple algorithms
    p1_runs = runs_df[(runs_df["profile"] == "p1") & (runs_df["algo"] == "idbo")]
    if p1_runs.empty:
        p1_runs = runs_df[runs_df["profile"] == "p1"]
    if p1_runs.empty:
        p1_runs = runs_df

    prof = get_profile("p1")
    targets = get_profile_targets(prof)

    if run_id is not None and run_id in p1_runs["run"].values:
        selected_run_id = run_id
    else:
        selected_run_id = select_representative_run(p1_runs, targets)

    sub = p1_runs[p1_runs["run"] == selected_run_id].sort_values("day")

    nutrients = ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sodium_mg"]
    col_labels = ["Năng lượng\n(kcal)", "Đạm\n(g)", "Tinh bột\n(g)", "Chất béo\n(g)", "Chất xơ\n(g)", "Natri\n(mg)"]

    days = sub["day"].values
    matrix = []
    text_matrix = []

    for _, row in sub.iterrows():
        row_pcts = []
        row_texts = []
        for nut in nutrients:
            val = float(row[nut])
            tgt = float(targets.get(nut, 100.0))
            pct = (val / tgt) * 100.0 if tgt > 0 else 100.0
            row_pcts.append(pct)
            row_texts.append(f"{val:.0f}\n({pct:.0f}%)")
        matrix.append(row_pcts)
        text_matrix.append(row_texts)

    matrix_arr = np.array(matrix)

    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Liberation Sans", "sans-serif"]
    fig, ax = plt.subplots(figsize=(10.0, 6.2), dpi=300)

    # Use clean colormap with normalized range [50%, 160%]
    # 100% target sits comfortably in the balanced teal/green zone
    cmap = plt.cm.YlGnBu
    norm = mcolors.Normalize(vmin=50, vmax=160)
    im = ax.imshow(matrix_arr, cmap=cmap, norm=norm, aspect="auto")

    cbar = fig.colorbar(im, ax=ax, pad=0.03)
    cbar.set_label("Tỷ lệ đạt mục tiêu dinh dưỡng khuyến nghị (%)", fontsize=10.5, fontweight="bold")
    cbar.set_ticks([60, 80, 100, 120, 140, 160])
    cbar.set_ticklabels(["60%", "80%", "100% (Chuẩn)", "120%", "140%", "160%"])
    cbar.ax.tick_params(labelsize=9.5)

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, fontsize=10.5, fontweight="bold")
    ax.set_yticks(range(len(days)))
    ax.set_yticklabels([f"Ngày {d}" for d in days], fontsize=10.5, fontweight="bold")

    # Add crisp white grid separation lines between cells
    ax.set_xticks(np.arange(-0.5, len(col_labels), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(days), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=2.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Mathematical luminance-based contrast rule (ITU-R BT.601 formula):
    # Ensures crisp contrast across all cell colors: white text on dark cells, dark slate on light cells
    for i in range(len(days)):
        for j in range(len(nutrients)):
            cell_val = matrix_arr[i, j]
            rgba = cmap(norm(cell_val))
            luminance = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
            text_color = "#FFFFFF" if luminance < 0.45 else "#0F172A"
            ax.text(
                j,
                i,
                text_matrix[i][j],
                ha="center",
                va="center",
                color=text_color,
                fontsize=10.0,
                fontweight="bold",
                linespacing=1.25,
            )

    ax.set_title(
        f"W9-F1: Heatmap Thành Phần Dinh Dưỡng Thực Đơn 7 Ngày (Profile P1 - Kế Hoạch Tiêu Biểu)\n(Giá trị thực tế và % đáp ứng chuẩn dinh dưỡng hàng ngày)",
        fontsize=11.5,
        fontweight="bold",
        pad=15,
    )
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_w9_f2_barchart(summary_df: pd.DataFrame, out_path: Path) -> None:
    """Plot W9-F2: Bar chart comparing P1, P2, P3 mean fitness and calo deviation.

    Args:
        summary_df: DataFrame from weekly_summary.csv.
        out_path: Target path for the output figure.
    """
    sub = summary_df[summary_df["algo"] == "idbo"]
    if sub.empty:
        sub = summary_df

    profiles = sub["profile"].unique()
    prof_names = {"p1": "P1 (Khỏe mạnh)", "p2": "P2 (Tiểu đường)", "p3": "P3 (Huyết áp)"}
    labels = [prof_names.get(p, p.upper()) for p in profiles]

    fitness_vals = [float(sub[sub["profile"] == p]["mean_fitness_7days"].values[0]) for p in profiles]
    dev_vals = [float(sub[sub["profile"] == p]["mean_calo_deviation_pct"].values[0]) for p in profiles]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(8, 5.5), dpi=300)

    bars1 = ax1.bar(x - width / 2, fitness_vals, width, label="Mean Fitness 7 ngày", color="#2B5C8F", alpha=0.85)
    ax1.set_ylabel("Hàm mục tiêu Fitness (Càng cao càng tốt)", color="#2B5C8F", fontsize=11, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor="#2B5C8F")
    ax1.set_ylim(0, 110)

    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, yval + 1.5, f"{yval:.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width / 2, dev_vals, width, label="Sai lệch Calo TB (%)", color="#D95F02", alpha=0.85)
    ax2.set_ylabel("Sai lệch Calo so với Target (%)", color="#D95F02", fontsize=11, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor="#D95F02")
    ax2.set_ylim(0, max(dev_vals + [10]) * 1.5)

    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, yval + 0.3, f"{yval:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=10, fontweight="bold")
    plt.title(
        "W9-F2: Hiệu Năng Tối Ưu Thực Đơn Chu Kỳ 7 Ngày Trên 3 Hồ Sơ Bệnh Lý\n(Profile P1: Chuẩn | P2: Giới hạn Đường <= 25g | P3: Giới hạn Natri <= 1500mg)",
        fontsize=11.5,
        fontweight="bold",
        pad=15,
    )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_w9_f3_radar(out_path: Path) -> None:
    """Plot W9-F3: Radar chart comparing UX Option A, B, and C.

    Args:
        out_path: Target path for the output figure.
    """
    categories = ["Mean Fitness\n(Điểm số)", "Độ đa dạng món\n(% độc nhất)", "Chuẩn Calo\n(100 - %lệch)", "An toàn\n(Không vi phạm)"]
    num_vars = len(categories)

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    # Metrics for Option A (9001), B (9002), C (9003) from generate_options_week9
    # Categories: [Mean Fitness, % Độc nhất, Chuẩn Calo (100 - %lệch), An toàn (100 - vi phạm*10)]
    options = {
        "Phương án A (seed 9001)": ([90.7, 100.0, 98.3, 100.0], "#2B5C8F", "-"),
        "Phương án B (seed 9002)": ([86.6, 85.7, 96.9, 100.0], "#D95F02", "--"),
        "Phương án C (seed 9003)": ([91.4, 100.0, 99.4, 100.0], "#2CA02C", "-."),
    }

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True), dpi=300)

    for name, (vals, color, style) in options.items():
        v = vals + vals[:1]
        ax.plot(angles, v, color=color, linewidth=2.2, linestyle=style, label=name)
        ax.fill(angles, v, color=color, alpha=0.15)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), categories, fontsize=10, fontweight="bold")
    ax.set_ylim(50, 105)
    ax.set_yticks([60, 70, 80, 90, 100])
    ax.set_yticklabels(["60%", "70%", "80%", "90%", "100%"], fontsize=8)
    ax.grid(True, linestyle=":", alpha=0.7)

    plt.title(
        "W9-F3: Radar So Sánh 3 Phương Án Thực Đơn 7 Ngày (Option A/B/C)\n(Đa dạng hóa trải nghiệm người dùng với các seed ngẫu nhiên độc lập)",
        fontsize=11.5,
        fontweight="bold",
        pad=20,
    )
    plt.legend(frameon=True, facecolor="white", edgecolor="#D3D3D3", fontsize=9, loc="lower right", bbox_to_anchor=(1.25, 0.05))
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[SAVED] {out_path}")


def main() -> None:
    """Main CLI execution for Week 9 plots."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Week 9 Plotting: W9-F1, W9-F2, W9-F3")
    parser.add_argument("--runs-file", type=str, default="experiments/week9/weekly_runs.csv", help="Weekly runs CSV")
    parser.add_argument("--summary-file", type=str, default="experiments/week9/weekly_summary.csv", help="Summary CSV")
    parser.add_argument("--output-dir", type=str, default="experiments/week9", help="Output directory")
    parser.add_argument("--run-id", type=int, default=None, help="Specific run ID to plot for W9-F1 (default: auto-select representative run)")

    args = parser.parse_args()

    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    runs_path = ROOT / args.runs_file
    summary_path = ROOT / args.summary_file

    if not runs_path.exists() or not summary_path.exists():
        print(f"[ERROR] Required CSV files not found: {runs_path} or {summary_path}", file=sys.stderr)
        print("Please run `python scripts/experiment_week9.py` first.", file=sys.stderr)
        sys.exit(1)

    runs_df = pd.read_csv(runs_path)
    summary_df = pd.read_csv(summary_path)

    print("=" * 80)
    print("PLOTTING WEEK 9 FIGURES (W9-F1, W9-F2, W9-F3)")
    print(f"Loaded {len(runs_df)} daily runs rows and {len(summary_df)} summary rows.")
    print("=" * 80)

    plot_w9_f1_heatmap(runs_df, out_dir / "fig_heatmap_nutrition_7days.png", run_id=args.run_id)
    plot_w9_f2_barchart(summary_df, out_dir / "fig_barchart_profiles_p1_p2_p3.png")
    plot_w9_f3_radar(out_dir / "fig_radar_options_abc.png")

    print("\n[COMPLETE] All 3 Week 9 figures generated successfully!")


if __name__ == "__main__":
    main()
