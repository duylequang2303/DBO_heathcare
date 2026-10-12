"""Tests for Week 8 Experiment and Plotting Scripts."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from scripts.experiment_week8 import (
    compute_summary_table,
    get_profile_p1,
    run_single_experiment,
    save_selected_foods_txt,
)
from scripts.plot_week8 import plot_boxplot, plot_convergence, plot_radar
from src.algorithms.two_tier_solver import TwoTierResult
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets


@pytest.fixture(scope="module")
def food_data_fixture():
    df = load_food_db()
    return build_food_map(df)


def test_get_profile_p1():
    """Verify profile P1 configuration and meal counts."""
    profile = get_profile_p1()
    assert profile.name == "Duy"
    assert sum(profile.meal_counts.values()) == 8
    assert "breakfast" in profile.meal_counts


def test_run_single_experiment_smoke(food_data_fixture):
    """Verify single experiment execution with minimal valid iterations (n_agents >= 4)."""
    profile = get_profile_p1()
    targets = daily_all_targets(profile)

    run_row, hist_rows, result = run_single_experiment(
        algo="idbo",
        run_idx=1,
        seed=8001,
        profile=profile,
        food_map=food_data_fixture,
        targets=targets,
        outer_max_iter=2,
        outer_n_agents=4,
        inner_max_iter=2,
        inner_n_agents=4,
    )

    assert run_row["algo"] == "idbo"
    assert run_row["run"] == 1
    assert "best_fitness" in run_row
    assert "runtime_s" in run_row
    assert len(hist_rows) == 3  # iters 0, 1, 2
    assert isinstance(result, TwoTierResult)


def test_compute_summary_table():
    """Verify statistical summary aggregation."""
    mock_runs = [
        {"algo": "idbo", "profile": "p1", "best_fitness": 90.0, "runtime_s": 1.0, "n_violations": 0},
        {"algo": "idbo", "profile": "p1", "best_fitness": 80.0, "runtime_s": 2.0, "n_violations": 1},
        {"algo": "dbo", "profile": "p1", "best_fitness": 70.0, "runtime_s": 1.5, "n_violations": 2},
    ]
    summary = compute_summary_table(mock_runs)
    assert len(summary) == 2

    idbo_sum = [s for s in summary if s["algo"] == "idbo"][0]
    assert idbo_sum["runs"] == 2
    assert idbo_sum["best"] == 90.0
    assert idbo_sum["worst"] == 80.0
    assert idbo_sum["mean"] == 85.0


def test_save_selected_foods_txt(tmp_path, food_data_fixture):
    """Verify selected foods text file output format."""
    profile = get_profile_p1()
    sample_ids = list(food_data_fixture.keys())[:8]
    portions = np.array([103.2, 74.8, 150.1, 80.0, 200.0, 50.0, 120.0, 95.0])
    res = TwoTierResult(
        best_food_ids=sample_ids,
        best_portions_g=portions,
        best_fitness=88.5,
        history=[88.5],
        outer_evals=10,
        inner_evals_total=50,
        runtime_s=0.5,
    )
    txt_path = tmp_path / "test_selected.txt"
    save_selected_foods_txt(res, food_data_fixture, profile.meal_counts, txt_path)

    assert txt_path.exists()
    lines = txt_path.read_text(encoding="utf-8").strip().split("\n")
    assert lines[0] == "food_id\tfood_name\tmeal_slot\tgram_rounded"
    assert len(lines) == 9  # 1 header + 8 items


def test_plots_smoke(tmp_path):
    """Verify that plotting functions generate valid PNG files without error."""
    runs_df = pd.DataFrame([
        {"algo": "dbo", "best_fitness": 75.0, "calories": 2400.0, "protein_g": 120.0, "carbs_g": 300.0, "fat_g": 70.0, "fiber_g": 30.0},
        {"algo": "dbo", "best_fitness": 78.0, "calories": 2420.0, "protein_g": 125.0, "carbs_g": 310.0, "fat_g": 72.0, "fiber_g": 32.0},
        {"algo": "idbo", "best_fitness": 88.0, "calories": 2450.0, "protein_g": 130.0, "carbs_g": 320.0, "fat_g": 75.0, "fiber_g": 35.0},
        {"algo": "idbo", "best_fitness": 92.0, "calories": 2460.0, "protein_g": 132.0, "carbs_g": 318.0, "fat_g": 74.0, "fiber_g": 34.0},
    ])
    hist_df = pd.DataFrame([
        {"algo": "dbo", "outer_iter": 0, "best_fitness": 60.0},
        {"algo": "dbo", "outer_iter": 1, "best_fitness": 75.0},
        {"algo": "idbo", "outer_iter": 0, "best_fitness": 65.0},
        {"algo": "idbo", "outer_iter": 1, "best_fitness": 90.0},
    ])

    f1 = tmp_path / "conv.png"
    f2 = tmp_path / "box.png"
    f3 = tmp_path / "radar.png"

    plot_convergence(hist_df, f1)
    plot_boxplot(runs_df, f2)
    plot_radar(runs_df, f3)

    assert f1.exists() and f1.stat().st_size > 0
    assert f2.exists() and f2.stat().st_size > 0
    assert f3.exists() and f3.stat().st_size > 0
