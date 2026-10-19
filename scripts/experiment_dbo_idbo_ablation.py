"""Ablation and Diagnostic Benchmark: DBO vs IDBO on Two-Tier Healthcare Menu Optimization.

Systematically investigates why DBO and IDBO yield identical results on the
healthcare menu generation problem, recording direct diversity and stagnation
telemetry, and verifying IDBO mechanism activation under controlled conditions.

Evaluates three paired diagnostic configurations across seeds 8001..8010:
  A. baseline_short: max_iter=25, stagnation_window=25, diversity_threshold=1e-3
  B. diagnostic_balanced: max_iter=100, stagnation_window=10, diversity_threshold=0.01
  C. diagnostic_aggressive_150: max_iter=150, stagnation_window=5, diversity_threshold=0.05

Plus a Controlled Activation Check:
  - controlled_activation: max_iter=30, stagnation_window=2, diversity_threshold=0.5,
    perturbation_rate=1.0, restart_rate=1.0 (proves IDBO wiring actively fires when threshold >= 0.5)

Outputs generated in experiments/ablation_dbo_idbo/:
  - paired_runs.csv
  - summary.csv
  - paired_differences.csv
  - controlled_activation.csv
  - fig_ablation_dbo_idbo.png
  - README.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import concurrent.futures
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.menu_objective import decode_result
from src.algorithms.two_tier_solver import TwoTierConfig, TwoTierResult, two_tier_optimize
from src.models.constraints import validate_menu
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets


def get_profile_p1() -> UserProfile:
    """Return standard evaluation profile P1 (Duy, healthy male, maintenance)."""
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


@dataclass
class ConfigSpec:
    name: str
    outer_max_iter: int
    stagnation_window: int
    diversity_threshold: float
    description: str


CONFIG_SPECS: list[ConfigSpec] = [
    ConfigSpec(
        name="baseline_short",
        outer_max_iter=25,
        stagnation_window=25,
        diversity_threshold=1e-3,
        description="Baseline W8 setup: max_iter=25, stagnation_window=25, div_threshold=0.001",
    ),
    ConfigSpec(
        name="diagnostic_balanced",
        outer_max_iter=100,
        stagnation_window=10,
        diversity_threshold=0.01,
        description="Diagnostic balanced: max_iter=100, stagnation_window=10, div_threshold=0.01",
    ),
    ConfigSpec(
        name="diagnostic_aggressive_150",
        outer_max_iter=150,
        stagnation_window=5,
        diversity_threshold=0.05,
        description="Diagnostic aggressive: max_iter=150, stagnation_window=5, div_threshold=0.05",
    ),
]


def run_single_worker(
    config_name: str,
    algo: str,
    seed: int,
    outer_max_iter: int,
    stagnation_window: int,
    diversity_threshold: float,
    perturbation_rate: float = 0.2,
    restart_rate: float = 0.25,
    outer_n_agents: int = 10,
    inner_max_iter: int = 25,
    inner_n_agents: int = 10,
) -> Dict[str, Any]:
    """Execute a single run of two-tier optimization in worker process."""
    df_food = load_food_db()
    food_map = build_food_map(df_food)
    profile = get_profile_p1()
    targets = daily_all_targets(profile)

    cfg = TwoTierConfig(
        outer_algo=algo,
        outer_n_agents=outer_n_agents,
        outer_max_iter=outer_max_iter,
        inner_algo=algo,
        inner_n_agents=inner_n_agents,
        inner_max_iter=inner_max_iter,
        seed=seed,
        stagnation_window=stagnation_window,
        diversity_threshold=diversity_threshold,
        perturbation_rate=perturbation_rate,
        restart_rate=restart_rate,
    )

    t0 = time.perf_counter()
    result = two_tier_optimize(profile, food_map, targets, cfg)
    runtime_s = time.perf_counter() - t0

    menu = decode_result(result.best_food_ids, result.best_portions_g, food_map, profile.meal_counts)
    violations = validate_menu(menu, profile, targets)
    cals = menu.total("calories")

    final_fitness = result.history[-1] if result.history else result.best_fitness

    return {
        "config_name": config_name,
        "algorithm": algo,
        "seed": seed,
        "best_fitness": round(float(result.best_fitness), 4),
        "final_fitness": round(float(final_fitness), 4),
        "runtime_s": round(float(runtime_s), 2),
        "n_evaluations": result.outer_evals + result.inner_evals_total,
        "outer_perturbations": int(result.outer_perturbations),
        "outer_restarts": int(result.outer_restarts),
        "final_inner_perturbations": int(result.final_inner_perturbations),
        "final_inner_restarts": int(result.final_inner_restarts),
        "inner_perturbations_total": int(result.inner_perturbations_total),
        "inner_restarts_total": int(result.inner_restarts_total),
        "outer_min_diversity": round(float(result.outer_min_diversity), 4),
        "outer_mean_diversity": round(float(result.outer_mean_diversity), 4),
        "outer_final_diversity": round(float(result.outer_final_diversity), 4),
        "outer_max_stagnation": int(result.outer_max_stagnation),
        "outer_collapse_events": int(result.outer_collapse_events),
        "outer_n_diversity_collapse_events": int(result.outer_n_diversity_collapse_events),
        "outer_n_stagnation_events": int(result.outer_n_stagnation_events),
        "inner_min_diversity": float(result.inner_min_diversity),
        "inner_mean_diversity": float(result.inner_mean_diversity),
        "inner_final_diversity": float(result.inner_final_diversity),
        "inner_max_stagnation": int(result.inner_max_stagnation),
        "inner_n_diversity_collapse_events_total": int(result.inner_n_diversity_collapse_events_total),
        "inner_n_stagnation_events_total": int(result.inner_n_stagnation_events_total),
        "final_inner_min_diversity": float(result.final_inner_min_diversity),
        "final_inner_mean_diversity": float(result.final_inner_mean_diversity),
        "final_inner_final_diversity": float(result.final_inner_final_diversity),
        "final_inner_max_stagnation": int(result.final_inner_max_stagnation),
        "final_inner_n_diversity_collapse_events": int(result.final_inner_n_diversity_collapse_events),
        "final_inner_n_stagnation_events": int(result.final_inner_n_stagnation_events),
        "calories": round(float(cals), 2),
        "n_violations": len(violations),
    }


def compute_paired_differences(runs: list[dict[str, Any]]) -> pd.DataFrame:
    """Compute paired differences (IDBO - DBO) on matching seeds per config."""
    df = pd.DataFrame(runs)
    diff_rows = []

    configs = df["config_name"].unique()
    for cfg_name in configs:
        sub = df[df["config_name"] == cfg_name]
        seeds = sorted(sub["seed"].unique())
        for seed in seeds:
            dbo_row = sub[(sub["algorithm"] == "dbo") & (sub["seed"] == seed)]
            idbo_row = sub[(sub["algorithm"] == "idbo") & (sub["seed"] == seed)]
            if dbo_row.empty or idbo_row.empty:
                continue

            dbo_fit = float(dbo_row["best_fitness"].iloc[0])
            idbo_fit = float(idbo_row["best_fitness"].iloc[0])
            diff = round(idbo_fit - dbo_fit, 6)

            dbo_rt = float(dbo_row["runtime_s"].iloc[0])
            idbo_rt = float(idbo_row["runtime_s"].iloc[0])

            idbo_pert = int(idbo_row["outer_perturbations"].iloc[0])
            idbo_rest = int(idbo_row["outer_restarts"].iloc[0])
            min_div = float(idbo_row["outer_min_diversity"].iloc[0])
            max_stag = int(idbo_row["outer_max_stagnation"].iloc[0])
            collapses = int(idbo_row["outer_collapse_events"].iloc[0])

            if abs(diff) < 1e-6:
                outcome = "TIE"
            elif diff > 0:
                outcome = "IDBO_WIN"
            else:
                outcome = "DBO_WIN"

            diff_rows.append({
                "config_name": cfg_name,
                "seed": seed,
                "dbo_fitness": dbo_fit,
                "idbo_fitness": idbo_fit,
                "diff_fitness": diff,
                "dbo_runtime_s": dbo_rt,
                "idbo_runtime_s": idbo_rt,
                "idbo_outer_pert": idbo_pert,
                "idbo_outer_rest": idbo_rest,
                "idbo_min_diversity": min_div,
                "idbo_max_stagnation": max_stag,
                "idbo_collapse_events": collapses,
                "outcome": outcome,
            })

    return pd.DataFrame(diff_rows)


def compute_summary_table(
    runs: list[dict[str, Any]],
    diff_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute comprehensive summary stats grouped by (config_name, algorithm)."""
    df = pd.DataFrame(runs)
    summary_rows = []

    configs = df["config_name"].unique()
    for cfg_name in configs:
        cfg_sub = df[df["config_name"] == cfg_name]
        cfg_diffs = diff_df[diff_df["config_name"] == cfg_name] if not diff_df.empty else pd.DataFrame()

        n_wins = int((cfg_diffs["outcome"] == "IDBO_WIN").sum()) if not cfg_diffs.empty else 0
        n_ties = int((cfg_diffs["outcome"] == "TIE").sum()) if not cfg_diffs.empty else 0
        n_losses = int((cfg_diffs["outcome"] == "DBO_WIN").sum()) if not cfg_diffs.empty else 0
        mean_diff = float(cfg_diffs["diff_fitness"].mean()) if not cfg_diffs.empty else 0.0

        for algo in ["dbo", "idbo"]:
            sub = cfg_sub[cfg_sub["algorithm"] == algo]
            if sub.empty:
                continue

            fits = sub["best_fitness"].astype(float).values
            runtimes = sub["runtime_s"].astype(float).values
            n_runs = len(sub)
            std_val = float(np.std(fits, ddof=1)) if n_runs > 1 else 0.0

            total_outer_pert = int(sub["outer_perturbations"].sum())
            total_outer_rest = int(sub["outer_restarts"].sum())
            total_inner_pert = int(sub["final_inner_perturbations"].sum())
            total_inner_rest = int(sub["final_inner_restarts"].sum())

            mean_min_div = float(sub["outer_min_diversity"].mean())
            mean_div = float(sub["outer_mean_diversity"].mean())
            max_stag = int(sub["outer_max_stagnation"].max())
            total_collapses = int(sub["outer_collapse_events"].sum())

            summary_rows.append({
                "config_name": cfg_name,
                "algorithm": algo,
                "runs": n_runs,
                "best_fitness": round(float(np.max(fits)), 4),
                "mean_fitness": round(float(np.mean(fits)), 4),
                "median_fitness": round(float(np.median(fits)), 4),
                "std_fitness": round(std_val, 4),
                "worst_fitness": round(float(np.min(fits)), 4),
                "mean_runtime_s": round(float(np.mean(runtimes)), 2),
                "total_outer_perturbations": total_outer_pert,
                "mean_outer_perturbations": round(total_outer_pert / n_runs, 2),
                "total_outer_restarts": total_outer_rest,
                "mean_outer_restarts": round(total_outer_rest / n_runs, 2),
                "total_final_inner_perturbations": total_inner_pert,
                "total_final_inner_restarts": total_inner_rest,
                "mean_min_diversity": round(mean_min_div, 4),
                "mean_diversity": round(mean_div, 4),
                "max_stagnation": max_stag,
                "total_collapse_events": total_collapses,
                **{f"mean_{col}": round(float(sub[col].mean()), 6) for col in sub.columns if col in (
                    "outer_final_diversity", "outer_n_diversity_collapse_events", "outer_n_stagnation_events",
                    "inner_min_diversity", "inner_mean_diversity", "inner_final_diversity", "inner_max_stagnation",
                    "inner_n_diversity_collapse_events_total", "inner_n_stagnation_events_total",
                    "final_inner_min_diversity", "final_inner_mean_diversity", "final_inner_final_diversity",
                    "final_inner_max_stagnation", "final_inner_n_diversity_collapse_events",
                    "final_inner_n_stagnation_events", "inner_perturbations_total", "inner_restarts_total")},
                "idbo_wins": n_wins if algo == "idbo" else 0,
                "idbo_ties": n_ties if algo == "idbo" else n_runs,
                "idbo_losses": n_losses if algo == "idbo" else 0,
                "mean_paired_difference": round(mean_diff, 4) if algo == "idbo" else 0.0,
            })

    return pd.DataFrame(summary_rows)


def _exec_controlled_task(arg: tuple) -> dict[str, Any]:
    cfg_name, algo, seed, o_iter, s_win, d_th, p_rate, r_rate, o_ag, i_iter, i_ag = arg
    return run_single_worker(
        config_name=cfg_name,
        algo=algo,
        seed=seed,
        outer_max_iter=o_iter,
        stagnation_window=s_win,
        diversity_threshold=d_th,
        perturbation_rate=p_rate,
        restart_rate=r_rate,
        outer_n_agents=o_ag,
        inner_max_iter=i_iter,
        inner_n_agents=i_ag,
    )


def run_controlled_activation_check(
    seeds: list[int] = [8001, 8002, 8003],
    workers: int = 3,
) -> pd.DataFrame:
    """Run controlled activation test with diversity_threshold=0.5 to verify Two-Tier IDBO wiring."""
    print("\n" + "=" * 80)
    print("CONTROLLED ACTIVATION CHECK: VERIFYING IDBO WIRING IN TWO-TIER SOLVER")
    print("Config: max_iter=30, stag_window=2, div_threshold=0.50, pert_rate=1.0, rest_rate=1.0")
    print(f"Seeds: {seeds}")
    print("=" * 80)

    tasks = [
        ("controlled_activation", "idbo", s, 30, 2, 0.50, 1.0, 1.0, 10, 25, 10)
        for s in seeds
    ]

    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(workers, len(tasks))) as ex:
        for res in ex.map(_exec_controlled_task, tasks):
            results.append(res)
            print(
                f"[CONTROLLED] Seed {res['seed']} -> Fitness: {res['best_fitness']:>7.4f} | "
                f"Outer Pert: {res['outer_perturbations']} | Outer Rest: {res['outer_restarts']} | "
                f"Inner Pert: {res['inner_perturbations_total']} | Inner Rest: {res['inner_restarts_total']} | "
                f"Min Diversity: {res['outer_min_diversity']:.4f} | Collapse Events: {res['outer_collapse_events']}",
                flush=True,
            )

    df_act = pd.DataFrame(results)
    df_act["wiring_verified"] = (df_act["outer_perturbations"] > 0) | (df_act["outer_restarts"] > 0)
    return df_act


def plot_ablation_figure(
    runs_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    controlled_df: pd.DataFrame,
    out_path: Path,
) -> None:
    """Generate high quality diagnostic visualization with measured diversity."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=150)

    spec_map = {spec.name: spec for spec in CONFIG_SPECS}
    configs = [spec.name for spec in CONFIG_SPECS
               if spec.name in set(runs_df["config_name"])]
    if not configs:
        raise ValueError("No benchmark configurations available to plot")
    cfg_labels = [f"{name}\n{spec_map[name].outer_max_iter} iterations" for name in configs]

    x = np.arange(len(configs))
    width = 0.35

    dbo_means = []
    idbo_means = []
    dbo_stds = []
    idbo_stds = []

    for cfg in configs:
        d_sub = runs_df[(runs_df["config_name"] == cfg) & (runs_df["algorithm"] == "dbo")]
        i_sub = runs_df[(runs_df["config_name"] == cfg) & (runs_df["algorithm"] == "idbo")]

        dbo_means.append(d_sub["best_fitness"].mean() if not d_sub.empty else 0)
        idbo_means.append(i_sub["best_fitness"].mean() if not i_sub.empty else 0)
        dbo_stds.append(d_sub["best_fitness"].std() if len(d_sub) > 1 else 0)
        idbo_stds.append(i_sub["best_fitness"].std() if len(i_sub) > 1 else 0)

    rects1 = axes[0].bar(x - width / 2, dbo_means, width, yerr=dbo_stds, label="DBO", color="#3b82f6", alpha=0.9, capsize=4)
    rects2 = axes[0].bar(x + width / 2, idbo_means, width, yerr=idbo_stds, label="IDBO", color="#10b981", alpha=0.9, capsize=4)

    axes[0].set_ylabel("Mean Best Fitness (Thang điểm 0–100)")
    axes[0].set_title(f"A. Fitness DBO / IDBO ({runs_df['seed'].nunique()} seeds)", fontsize=11, fontweight="bold")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(cfg_labels, fontsize=9)
    axes[0].set_ylim(85, 102)
    axes[0].grid(axis="y", linestyle="--", alpha=0.5)
    axes[0].legend(loc="lower left")

    for rect in rects1:
        h = rect.get_height()
        axes[0].annotate(f"{h:.2f}",
                         xy=(rect.get_x() + rect.get_width() / 2, h),
                         xytext=(0, 3), textcoords="offset points",
                         ha="center", va="bottom", fontsize=8, color="#1e3a8a", fontweight="bold")
    for rect in rects2:
        h = rect.get_height()
        axes[0].annotate(f"{h:.2f}",
                         xy=(rect.get_x() + rect.get_width() / 2, h),
                         xytext=(0, 3), textcoords="offset points",
                         ha="center", va="bottom", fontsize=8, color="#065f46", fontweight="bold")

    # Subplot 2: Swarm Diversity (Measured vs Thresholds)
    idbo_sum = summary_df[summary_df["algorithm"] == "idbo"]
    min_divs = [idbo_sum[idbo_sum["config_name"] == c]["mean_min_diversity"].values[0] for c in configs]
    thresholds = [spec_map[c].diversity_threshold for c in configs]

    axes[1].plot(x, min_divs, "o-", color="#8b5cf6", linewidth=2.5, markersize=8, label="Min Diversity Đo Thực Tế")
    axes[1].plot(x, thresholds, "s--", color="#ef4444", linewidth=2.0, markersize=7, label="Ngưỡng Kích Hoạt (Threshold)")

    # Plot controlled activation reference
    ctrl_min_div = controlled_df["outer_min_diversity"].mean() if not controlled_df.empty else 0.25
    axes[1].axhline(y=0.50, color="#f59e0b", linestyle=":", linewidth=2, label="Ngưỡng Controlled Act. (0.50)")

    axes[1].set_ylabel("Độ Đa Dạng Quần Thể (Normalized Std / Span)")
    axes[1].set_title("B. Bằng Chứng Trực Tiếp: Độ Đa Dạng Thực Tế vs Ngưỡng Kích Hoạt", fontsize=11, fontweight="bold")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(cfg_labels, fontsize=9)
    axes[1].set_ylim(-0.02, 0.58)
    axes[1].grid(True, linestyle="--", alpha=0.5)
    axes[1].legend(loc="center right")

    for idx, (m_div, th) in enumerate(zip(min_divs, thresholds)):
        axes[1].annotate(f"Min: {m_div:.3f}", xy=(x[idx], m_div), xytext=(0, 8),
                         textcoords="offset points", ha="center", fontsize=8.5, color="#5b21b6", fontweight="bold")
        axes[1].annotate(f"Th: {th}", xy=(x[idx], th), xytext=(0, -12),
                         textcoords="offset points", ha="center", fontsize=8.5, color="#b91c1c")

    # No hard-coded conclusions: figures reflect only rows actually measured.
    axes[1].annotate(
        f"Measured: {runs_df['seed'].nunique()} seed(s); verify activation in CSV",
        xy=(0.5, 0.9), xycoords="axes fraction", ha="center", fontsize=9,
    )

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()


def generate_readme(
    summary_df: pd.DataFrame,
    diff_df: pd.DataFrame,
    controlled_df: pd.DataFrame,
    out_path: Path,
) -> None:
    """Report measured data only; never embed historical ten-seed claims."""
    seeds = sorted(int(x) for x in diff_df["seed"].unique()) if not diff_df.empty else []
    lines = [
        "# DBO vs IDBO - Telemetry benchmark",
        "",
        f"Measured paired seeds: {seeds} ({len(seeds)} seed(s)).",
        "Only the rows in this output directory support the findings below.",
        "Do not interpret a partial run as a ten-seed result.",
        "",
        "## Summary (measured)", "", "```", summary_df.to_string(index=False), "```", "",
        "## Paired differences (measured)", "", "```", diff_df.to_string(index=False), "```", "",
        "## Controlled activation (measured)", "", "```",
        controlled_df.to_string(index=False) if not controlled_df.empty else "Not run", "```", "",
        "Fitness ties and mechanism activation must be interpreted per configuration and seed.",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _atomic_csv(df: pd.DataFrame, path: Path) -> None:
    """Save complete checkpoint atomically, avoiding truncated CSV on interruption."""
    tmp = path.with_name(path.name + ".tmp")
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, path)


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL,
            text=True, timeout=5,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def _config_hash(spec: ConfigSpec, algo: str) -> str:
    # Include the experiment implementation itself to detect changes between runs.
    payload = {
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "config": spec.__dict__, "algo": algo,
        "outer_n_agents": 10, "inner_max_iter": 25, "inner_n_agents": 10,
        "perturbation_rate": 0.2, "restart_rate": 0.25,
        "profile": "P1", "benchmark_schema": 2,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _run_key(row: dict[str, Any]) -> tuple[str, str, int]:
    return (str(row["config_name"]), str(row["algorithm"]), int(row["seed"]))


def _write_outputs(runs: list[dict[str, Any]], out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ordered = sorted(runs, key=_run_key)
    runs_df = pd.DataFrame(ordered)
    _atomic_csv(runs_df, out_dir / "paired_runs.csv")
    diff_df = compute_paired_differences(ordered)
    _atomic_csv(diff_df, out_dir / "paired_differences.csv")
    summary_df = compute_summary_table(ordered, diff_df)
    _atomic_csv(summary_df, out_dir / "summary.csv")
    return runs_df, diff_df, summary_df


def _execute_task(task_args: tuple[ConfigSpec, str, int]) -> dict[str, Any]:
    spec, algo, seed = task_args
    return run_single_worker(
        config_name=spec.name,
        algo=algo,
        seed=seed,
        outer_max_iter=spec.outer_max_iter,
        stagnation_window=spec.stagnation_window,
        diversity_threshold=spec.diversity_threshold,
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="DBO vs IDBO Ablation Diagnostic Benchmark")
    parser.add_argument("--smoke", action="store_true", help="Use seeds 8001, 8002")
    parser.add_argument("--seeds", nargs="+", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--output-dir", default="experiments/ablation_dbo_idbo")
    parser.add_argument("--config", choices=[c.name for c in CONFIG_SPECS], default=None,
                        help="Run only this configuration (default: all three)")
    parser.add_argument("--resume", action="store_true", help="Skip previously saved compatible runs")
    parser.add_argument("--skip-controlled", action="store_true", help="Skip controlled activation check")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be >= 1")
    if args.smoke and args.seeds is not None:
        parser.error("Use either --smoke or --seeds, not both")

    seeds = [8001, 8002] if args.smoke else (args.seeds if args.seeds else list(range(8001, 8011)))
    if len(set(seeds)) != len(seeds):
        parser.error("Duplicate seeds are not allowed")
    specs = [c for c in CONFIG_SPECS if args.config is None or c.name == args.config]
    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    paired_file = out_dir / "paired_runs.csv"
    commit = _git_commit()
    hash_map = {(c.name, a): _config_hash(c, a) for c in specs for a in ("dbo", "idbo")}

    print(f"[BENCHMARK] seeds={seeds}, configs={[c.name for c in specs]}, workers={args.workers}")
    print(f"[OUTPUT] {out_dir}")
    print(f"[GIT COMMIT] {commit}")

    existing: dict[tuple[str, str, int], dict[str, Any]] = {}
    if args.resume and paired_file.exists():
        prior = pd.read_csv(paired_file, keep_default_na=False)
        for row in prior.to_dict(orient="records"):
            key = _run_key(row)
            if key in existing:
                raise RuntimeError(f"Duplicate checkpoint row: {key}")
            if "config_hash" not in row or "git_commit" not in row:
                raise RuntimeError("Old CSV has no provenance; choose a NEW --output-dir")
            if row["config_name"] in {c.name for c in specs}:
                expected = hash_map[(row["config_name"], row["algorithm"])]
                if row["config_hash"] != expected or row["git_commit"] != commit:
                    raise RuntimeError(f"Checkpoint provenance mismatch for {key}; use a NEW --output-dir")
            existing[key] = row
        print(f"[RESUME] Loaded {len(existing)} checkpoint rows")
    elif paired_file.exists():
        raise RuntimeError(f"Output already has paired_runs.csv: {paired_file}. Use --resume or a NEW directory")

    ctrl_file = out_dir / "controlled_activation.csv"
    if args.skip_controlled:
        ctrl_df = pd.read_csv(ctrl_file) if ctrl_file.exists() else pd.DataFrame()
        print("[CONTROLLED] Skipped by request")
    elif args.resume and ctrl_file.exists():
        ctrl_df = pd.read_csv(ctrl_file)
        print("[CONTROLLED] Reusing existing controlled_activation.csv")
    else:
        ctrl_seeds = [8001] if args.smoke else [8001, 8002, 8003]
        ctrl_df = run_controlled_activation_check(seeds=ctrl_seeds, workers=min(args.workers, len(ctrl_seeds)))
        ctrl_df["git_commit"] = commit
        ctrl_df["config_hash"] = hashlib.sha256(json.dumps({
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "controlled": [30, 2, 0.50, 1.0, 1.0, 10, 25, 10],
        }, sort_keys=True).encode()).hexdigest()
        _atomic_csv(ctrl_df, ctrl_file)
        print(f"[SAVED] {ctrl_file}")

    tasks = [(spec, algo, seed) for spec in specs for seed in seeds for algo in ("dbo", "idbo")]
    pending = [t for t in tasks if (t[0].name, t[1], t[2]) not in existing]
    print(f"[TASKS] {len(tasks)} requested, {len(pending)} pending, {len(tasks)-len(pending)} skipped")
    all_rows = dict(existing)
    start = time.perf_counter()
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(_execute_task, t): t for t in pending}
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                result = future.result()
                key = _run_key(result)
                result["git_commit"] = commit
                result["config_hash"] = hash_map[(result["config_name"], result["algorithm"])]
                all_rows[key] = result
                _write_outputs(list(all_rows.values()), out_dir)
                print(f"[{i}/{len(pending)}] {key} fitness={result['best_fitness']:.4f} "
                      f"min_div={result['outer_min_diversity']:.4f} "
                      f"pert={result['outer_perturbations']} rest={result['outer_restarts']} [SAVED]", flush=True)
    except KeyboardInterrupt:
        print("[INTERRUPTED] Completed runs are saved. Re-run with --resume.", flush=True)
        raise SystemExit(130)

    if not all_rows:
        print("[INFO] No completed runs available")
        return
    runs_df, diff_df, summary_df = _write_outputs(list(all_rows.values()), out_dir)
    selected = runs_df[runs_df["config_name"].isin([c.name for c in specs]) & runs_df["seed"].isin(seeds)]
    expected_keys = {(s.name, a, seed) for s in specs for seed in seeds for a in ("dbo", "idbo")}
    complete = expected_keys.issubset(set(map(_run_key, selected.to_dict(orient="records"))))
    if complete:
        # Plot/report only requested selection, not unrelated previous runs in the folder.
        selected_rows = selected.to_dict(orient="records")
        selected_diff = compute_paired_differences(selected_rows)
        selected_summary = compute_summary_table(selected_rows, selected_diff)
        plot_ablation_figure(selected, selected_summary, ctrl_df, out_dir / "fig_ablation_dbo_idbo.png")
        generate_readme(selected_summary, selected_diff, ctrl_df, out_dir / "README.md")
        print(f"[SUCCESS] {len(pending)} new runs; {len(expected_keys)} requested runs complete in {time.perf_counter()-start:.1f}s")
    else:
        print("[PARTIAL] CSV checkpoint saved; resume to complete the requested runs")


if __name__ == "__main__":
    main()
