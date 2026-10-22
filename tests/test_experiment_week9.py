"""Tests for Week 9 Multi-Option Generator, 7-Day Experiment, and Plots."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from scripts.generate_options_week9 import get_profile, get_profile_targets, plan_7days
from scripts.experiment_week9 import compute_weekly_summary, run_7day_experiment_single
from scripts.plot_week9 import plot_w9_f1_heatmap, plot_w9_f2_barchart, plot_w9_f3_radar
from src.utils.data_loader import build_food_map, load_food_db


@pytest.fixture(scope="module")
def food_data_fixture():
    """Fixture to load and cache the processed food database."""
    df = load_food_db()
    return build_food_map(df)


def test_week9_profiles_and_targets():
    """Verify configuration of P1, P2 (diabetes), and P3 (hypertension) profiles."""
    p1 = get_profile("p1")
    t1 = get_profile_targets(p1)
    assert p1.name == "Duy"

    p2 = get_profile("p2")
    t2 = get_profile_targets(p2)
    assert p2.name == "Lan"
    assert t2["sugar_g"] == 25.0

    p3 = get_profile("p3")
    t3 = get_profile_targets(p3)
    assert p3.name == "Minh"
    assert t3["sodium_mg"] == 1500.0


def test_plan_7days_smoke(food_data_fixture):
    """Verify plan_7days execution on profile P1 with small iterations."""
    p1 = get_profile("p1")
    t1 = get_profile_targets(p1)

    res = plan_7days(
        profile=p1,
        food_map=food_data_fixture,
        targets=t1,
        base_seed=9001,
        outer_iter=2,
        inner_iter=2,
        outer_agents=4,
        inner_agents=4,
        days=2,
    )

    assert "mean_fitness" in res
    assert "mean_calories" in res
    assert "diversity_pct" in res
    assert len(res["daily"]) == 2


def test_run_7day_experiment_single_smoke(food_data_fixture):
    """Verify run_7day_experiment_single execution."""
    p1 = get_profile("p1")
    t1 = get_profile_targets(p1)

    records, div_pct = run_7day_experiment_single(
        algo="idbo",
        prof_key="p1",
        run_idx=1,
        base_seed=9001,
        profile=p1,
        food_map=food_data_fixture,
        targets=t1,
        days=2,
        outer_iter=2,
        inner_iter=2,
        outer_agents=4,
        inner_agents=4,
    )

    assert len(records) == 2
    assert records[0]["algo"] == "idbo"
    assert records[0]["profile"] == "p1"
    assert isinstance(div_pct, float)


def test_compute_weekly_summary():
    """Verify summary table aggregation for week 9."""
    records = [
        {"algo": "idbo", "profile": "p1", "run": 1, "day": 1, "fitness": 80.0, "n_violations": 0, "calories": 2500.0},
        {"algo": "idbo", "profile": "p1", "run": 1, "day": 2, "fitness": 82.0, "n_violations": 0, "calories": 2480.0},
    ]
    summary = compute_weekly_summary(records, {"p1": 2490.0})
    assert len(summary) == 1
    assert summary[0]["mean_fitness_7days"] == 81.0


def test_plot_week9_smoke(tmp_path):
    """Verify that all 3 Week 9 plotting functions run without errors."""
    mock_runs = pd.DataFrame([
        {
            "algo": "idbo", "profile": "p1", "run": 1, "day": d, "fitness": 85.0, "n_violations": 0,
            "calories": 2490.0, "protein_g": 125.0, "carbs_g": 310.0, "fat_g": 72.0, "fiber_g": 30.0, "sodium_mg": 2100.0
        }
        for d in range(1, 8)
    ])
    mock_summary = pd.DataFrame([
        {"algo": "idbo", "profile": "p1", "mean_fitness_7days": 88.0, "mean_violations": 0.0, "mean_calo_deviation_pct": 0.5},
        {"algo": "idbo", "profile": "p2", "mean_fitness_7days": 84.5, "mean_violations": 0.0, "mean_calo_deviation_pct": 0.8},
        {"algo": "idbo", "profile": "p3", "mean_fitness_7days": 86.2, "mean_violations": 0.0, "mean_calo_deviation_pct": 0.6},
    ])

    f1 = tmp_path / "heatmap.png"
    f2 = tmp_path / "barchart.png"
    f3 = tmp_path / "radar.png"

    plot_w9_f1_heatmap(mock_runs, f1)
    plot_w9_f2_barchart(mock_summary, f2)
    plot_w9_f3_radar(f3)

    assert f1.exists() and f1.stat().st_size > 0
    assert f2.exists() and f2.stat().st_size > 0
    assert f3.exists() and f3.stat().st_size > 0
