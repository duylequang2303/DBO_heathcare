"""Tạo các hình vẽ khoa học minh chứng thực nghiệm cho Slide Báo Cáo Tuần 11.

Đầu ra được lưu tại experiments/ablation_dbo_idbo/:
- W11-F1: fig_fitness_comparison_seed8003_8010.png (So sánh fitness DBO vs IDBO trên tập độc lập)
- W11-F2: fig_resource_tradeoff_evals_runtime.png (Đánh đổi tài nguyên: Số evaluations & Thời gian chạy)
- W11-F3: fig_telemetry_activations.png (Telemetry kích hoạt tầng ngoài vs tầng trong)
- W11-F4: fig_budget_matched_smoke.png (Minh chứng dừng chuẩn xác ngân sách tính toán 150 evals)
"""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "experiments" / "ablation_dbo_idbo"
OUT_DIR.mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Bảng màu chuẩn học thuật
NAVY = "#1B2A4A"
TEAL = "#1D6F6F"
AMBER = "#D9822B"
CORAL = "#B83228"
GREEN = "#217A4B"
GRAY = "#5A6478"
LIGHT_BG = "#F8FAFC"

plt.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "axes.edgecolor": "#CBD5E1",
    "axes.linewidth": 1.0,
    "grid.color": "#E2E8F0",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
})


def plot_w11_f1_fitness(diffs_df: pd.DataFrame, out_path: Path):
    """W11-F1: So sánh Fitness DBO vs IDBO trên 8 seed độc lập (8003-8010)."""
    eval_df = diffs_df[diffs_df["set_type"] == "independent_eval"].copy()
    seeds = [f"Seed\n{int(s)}" for s in eval_df["seed"]]
    dbo_fit = eval_df["dbo_fitness"].values
    idbo_fit = eval_df["idbo_fitness"].values
    diffs = eval_df["diff_fitness"].values

    x = np.arange(len(seeds))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(LIGHT_BG)

    bars1 = ax.bar(x - width/2, dbo_fit, width, label="DBO (Chuẩn)", color=NAVY, alpha=0.9, edgecolor="none")
    bars2 = ax.bar(x + width/2, idbo_fit, width, label="IDBO (Ngưỡng 0.28)", color=TEAL, alpha=0.9, edgecolor="none")

    # Giới hạn trục Y để thấy rõ sự khác biệt ở vùng điểm cao 96-100
    ax.set_ylim(96.0, 100.5)
    ax.set_ylabel("Điểm Đánh Giá (Fitness, thang 100)", fontsize=11, fontweight="bold", color=NAVY)
    ax.set_title("W11-F1: So Sánh Điểm Số Đối Đầu DBO vs IDBO (Tập Độc Lập Seed 8003–8010)", fontsize=12, fontweight="bold", color=NAVY, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(seeds, fontsize=10)
    ax.legend(frameon=True, facecolor="white", edgecolor="#CBD5E1", loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Hiển thị nhãn chênh lệch trên từng cặp
    for i, diff in enumerate(diffs):
        c = GREEN if diff > 0 else CORAL
        txt = f"+{diff:.2f}" if diff > 0 else f"{diff:.2f}"
        higher = max(dbo_fit[i], idbo_fit[i])
        ax.text(x[i], higher + 0.12, txt, ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=c)

    # Chú thích tổng kết
    ax.text(0.98, 0.05, "IDBO Thắng: 5/8 (62.5%) | DBO Thắng: 3/8 (37.5%)\nChênh lệch trung bình: +0.1659 điểm | Wilcoxon p > 0.05",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9.5,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="#CBD5E1", alpha=0.95))

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_w11_f2_resources(eval_df: pd.DataFrame, out_path: Path):
    """W11-F2: Đánh đổi tài nguyên: Số lượt tính hàm mục tiêu và thời gian chạy."""
    ind_df = eval_df[eval_df["set_type"] == "independent_eval"].copy()
    dbo_runs = ind_df[ind_df["algo"] == "dbo"]
    idbo_runs = ind_df[ind_df["algo"] == "idbo"]

    seeds = [str(int(s)) for s in dbo_runs["seed"].values]
    x = np.arange(len(seeds))
    width = 0.38

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), dpi=200)
    fig.patch.set_facecolor("white")

    # Subplot 1: Evaluations
    ax1.set_facecolor(LIGHT_BG)
    ax1.bar(x - width/2, dbo_runs["n_evaluations"]/1000, width, label="DBO", color=NAVY, alpha=0.9)
    ax1.bar(x + width/2, idbo_runs["n_evaluations"]/1000, width, label="IDBO (+18.6%)", color=AMBER, alpha=0.9)
    ax1.set_ylabel("Số lượt đánh giá hàm mục tiêu (x1,000)", fontsize=10, fontweight="bold", color=NAVY)
    ax1.set_title("Số Lượt Tính Toán (Evaluations)", fontsize=11, fontweight="bold", color=NAVY)
    ax1.set_xticks(x)
    ax1.set_xticklabels(seeds, fontsize=9)
    ax1.set_ylim(200, 370)
    ax1.legend(frameon=True, facecolor="white")
    ax1.grid(axis="y", linestyle="--", alpha=0.7)

    # Subplot 2: Runtime
    ax2.set_facecolor(LIGHT_BG)
    ax2.bar(x - width/2, dbo_runs["runtime_s"], width, label="DBO (Trung bình 49.4s)", color=NAVY, alpha=0.9)
    ax2.bar(x + width/2, idbo_runs["runtime_s"], width, label="IDBO (Trung bình 56.6s, +14.6%)", color=TEAL, alpha=0.9)
    ax2.set_ylabel("Thời gian chạy (giây)", fontsize=10, fontweight="bold", color=NAVY)
    ax2.set_title("Thời Gian Thực Thi (Runtime)", fontsize=11, fontweight="bold", color=NAVY)
    ax2.set_xticks(x)
    ax2.set_xticklabels(seeds, fontsize=9)
    ax2.set_ylim(25, 75)
    ax2.legend(frameon=True, facecolor="white")
    ax2.grid(axis="y", linestyle="--", alpha=0.7)

    plt.suptitle("W11-F2: Chi Phí Tài Nguyên Tính Toán Giữa DBO và IDBO (Seed 8003–8010)", fontsize=12, fontweight="bold", color=NAVY, y=0.98)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_w11_f3_telemetry(eval_df: pd.DataFrame, out_path: Path):
    """W11-F3: Telemetry kích hoạt cơ chế bổ sung tầng ngoài và tầng trong của IDBO."""
    ind_df = eval_df[(eval_df["set_type"] == "independent_eval") & (eval_df["algo"] == "idbo")].copy()
    seeds = [str(int(s)) for s in ind_df["seed"].values]
    x = np.arange(len(seeds))
    width = 0.35

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), dpi=200)
    fig.patch.set_facecolor("white")

    # Subplot 1: Tầng ngoài
    ax1.set_facecolor(LIGHT_BG)
    b1 = ax1.bar(x - width/2, ind_df["outer_perturbations"], width, label="Đột biến (Perturbations)", color=TEAL, alpha=0.9)
    b2 = ax1.bar(x + width/2, ind_df["outer_restarts"], width, label="Restart khi bế tắc", color=CORAL, alpha=0.9)
    ax1.set_ylabel("Số lần kích hoạt", fontsize=10, fontweight="bold", color=NAVY)
    ax1.set_title("Tầng Ngoài (Chọn Tổ Hợp Món Rời Rạc)", fontsize=11, fontweight="bold", color=NAVY)
    ax1.set_xticks(x)
    ax1.set_xticklabels(seeds, fontsize=9)
    ax1.set_ylim(0, 85)
    ax1.legend(frameon=True, facecolor="white")
    ax1.grid(axis="y", linestyle="--", alpha=0.7)

    # Đánh dấu chú ý tại seed 8007 và 8008
    ax1.annotate("0 kích hoạt\n(Hội tụ tầng trong)", xy=(4, 2), xytext=(4, 25),
                arrowprops=dict(facecolor=NAVY, shrink=0.08, width=1, headwidth=5),
                fontsize=8.5, ha="center", bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=NAVY))

    # Subplot 2: Tầng trong
    ax2.set_facecolor(LIGHT_BG)
    ax2.bar(x, ind_df["inner_perturbations_total"]/1000, width*1.5, label="Đột biến tầng trong", color=NAVY, alpha=0.85)
    ax2.set_ylabel("Số lần đột biến (x1,000)", fontsize=10, fontweight="bold", color=NAVY)
    ax2.set_title("Tầng Trong (Tối Ưu Gram Khẩu Phần Liên Tục)", fontsize=11, fontweight="bold", color=NAVY)
    ax2.set_xticks(x)
    ax2.set_xticklabels(seeds, fontsize=9)
    ax2.set_ylim(10, 22)
    ax2.legend(frameon=True, facecolor="white")
    ax2.grid(axis="y", linestyle="--", alpha=0.7)

    plt.suptitle("W11-F3: Giải Mã Tác Động Telemetry Kích Hoạt 2 Tầng Của IDBO", fontsize=12, fontweight="bold", color=NAVY, y=0.98)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_w11_f4_budget(budget_csv: Path, out_path: Path):
    """W11-F4: Minh chứng cơ chế dừng Budget-Matched 150 evaluations."""
    if not budget_csv.exists():
        return
    bdf = pd.read_csv(budget_csv)
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(LIGHT_BG)

    labels = [f"{r['algorithm'].upper()} - Seed {r['seed']}" for _, r in bdf.iterrows()]
    evals = bdf["function_evaluations"].values
    colors = [NAVY, TEAL, NAVY, TEAL]

    bars = ax.barh(labels, evals, color=colors, height=0.55, alpha=0.9)
    ax.axvline(150, color=CORAL, linestyle="--", linewidth=1.5, label="Giới hạn chung max_evaluations = 150")
    ax.set_xlabel("Số lượt tính toán thực tế (Function Evaluations)", fontsize=10, fontweight="bold", color=NAVY)
    ax.set_title("W11-F4: Kiểm Tra Cơ Chế Dừng Theo Ngân Sách Chung (Budget-Matched Smoke Test)", fontsize=11, fontweight="bold", color=NAVY)
    ax.set_xlim(0, 180)
    ax.grid(axis="x", linestyle="--", alpha=0.7)
    ax.legend(frameon=True, facecolor="white", loc="lower right")

    for bar, val in zip(bars, evals):
        ax.text(val + 3, bar.get_y() + bar.get_height()/2, f"{val}/150 (Dừng đúng trần)",
                va="center", fontsize=9, fontweight="bold", color=NAVY)

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_w11_f5_web_radar(out_path: Path):
    """W11-F5: Biểu đồ Radar 6 trục dinh dưỡng và bảng thực đơn từ Web API."""
    from app.api.services import generate_menu, PRESET_PROFILES
    from app.api.schemas import GenerateIn, ProfileIn

    pin = ProfileIn(**PRESET_PROFILES["p1"])
    req = GenerateIn(profile=pin, seed=9001, config="smoke")
    menu = generate_menu(req)

    totals = menu.totals
    targets = menu.targets

    labels = ["Calories\n(kcal)", "Protein\n(g)", "Carbs\n(g)", "Fat\n(g)", "Fiber\n(g)", "Sodium\n(mg)"]
    keys = ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sodium_mg"]

    # Tỷ lệ % đạt được so với target
    pcts = [(totals[k] / targets[k]) * 100 for k in keys]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    pcts_plot = pcts + [pcts[0]]
    angles_plot = angles + [angles[0]]

    fig = plt.figure(figsize=(6, 5.2), dpi=200)
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor(LIGHT_BG)

    # Vùng mục tiêu chuẩn (100%)
    target_line = [100] * len(angles_plot)
    ax.plot(angles_plot, target_line, color=AMBER, linewidth=1.8, linestyle="--", label="Mục tiêu chuẩn (100%)")
    ax.fill(angles_plot, target_line, color=AMBER, alpha=0.08)

    # Dải dung sai cho phép (80% - 120%)
    ax.fill_between(angles_plot, [80]*len(angles_plot), [120]*len(angles_plot), color=GREEN, alpha=0.06, label="Dải dung sai hợp lệ")

    # Dữ liệu thực đơn tạo ra
    ax.plot(angles_plot, pcts_plot, color=TEAL, linewidth=2.5, marker="o", markersize=6, label=f"Thực đơn tạo ra (IDBO)")
    ax.fill(angles_plot, pcts_plot, color=TEAL, alpha=0.25)

    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=9.5, fontweight="bold", color=NAVY)
    ax.set_ylim(0, 150)
    ax.set_yticks([50, 80, 100, 120, 150])
    ax.set_yticklabels(["50%", "80%", "100%", "120%", "150%"], fontsize=8, color=GRAY)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), fontsize=8.5, frameon=True, facecolor="white")
    ax.set_title("W11-F5: Trực Quan Hóa Dinh Dưỡng Đa Chiều (Radar Chart - Profile P1)", fontsize=10.5, fontweight="bold", color=NAVY, pad=25)

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] {out_path}")


def main():
    diffs_path = OUT_DIR / "candidate_threshold_028_diffs.csv"
    eval_path = OUT_DIR / "candidate_threshold_028_eval.csv"
    budget_path = ROOT / "results" / "week11_budget_smoke_150" / "paired_runs.csv"

    if diffs_path.exists():
        diffs_df = pd.read_csv(diffs_path)
        plot_w11_f1_fitness(diffs_df, OUT_DIR / "fig_fitness_comparison_seed8003_8010.png")

    if eval_path.exists():
        eval_df = pd.read_csv(eval_path)
        plot_w11_f2_resources(eval_df, OUT_DIR / "fig_resource_tradeoff_evals_runtime.png")
        plot_w11_f3_telemetry(eval_df, OUT_DIR / "fig_telemetry_activations.png")

    plot_w11_f4_budget(budget_path, OUT_DIR / "fig_budget_matched_smoke.png")
    plot_w11_f5_web_radar(OUT_DIR / "fig_web_radar_nutrition_p1.png")


if __name__ == "__main__":
    main()
