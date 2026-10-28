"""Unit tests for scripts/validate_week9_data.py."""

from pathlib import Path
import pytest
import pandas as pd

from scripts.validate_week9_data import (
    PROFILE_STANDARDS,
    audit_calories,
    audit_fiber,
    audit_sodium,
    generate_detailed_report,
    load_weekly_runs,
    main,
    run_validation,
)


@pytest.fixture
def sample_runs_df():
    """Create a controlled DataFrame for testing audit calculations."""
    return pd.DataFrame({
        "algo": ["dbo", "dbo", "idbo", "idbo"],
        "profile": ["p1", "p1", "p2", "p3"],
        "run": [1, 1, 1, 1],
        "seed": [9001, 9001, 9001, 9001],
        "day": [1, 2, 1, 1],
        "fitness": [95.0, 96.0, 90.0, 92.0],
        "n_violations": [0, 0, 0, 0],
        "outer_perturbations": [0, 0, 1, 0],
        "outer_restarts": [0, 0, 0, 0],
        "final_inner_perturbations": [0, 0, 0, 0],
        "final_inner_restarts": [0, 0, 0, 0],
        "calories": [2500.0, 2480.0, 1180.0, 1840.0],
        "protein_g": [120.0, 125.0, 80.0, 95.0],
        "carbs_g": [310.0, 315.0, 120.0, 230.0],
        "fat_g": [80.0, 82.0, 40.0, 60.0],
        "fiber_g": [35.0, 38.0, 26.0, 30.0],
        "sugar_g_estimated": [40.0, 42.0, 15.0, 30.0],
        "sugar_is_estimated": [True, True, True, True],
        "sodium_mg": [2500.0, 3500.0, 1500.0, 2800.0],
    })


def test_load_weekly_runs(tmp_path: Path, sample_runs_df: pd.DataFrame):
    """Test loading valid and invalid CSV files."""
    csv_file = tmp_path / "test_runs.csv"
    sample_runs_df.to_csv(csv_file, index=False)

    loaded = load_weekly_runs(csv_file)
    assert len(loaded) == 4
    assert "sodium_mg" in loaded.columns

    # Test missing file
    with pytest.raises(FileNotFoundError):
        load_weekly_runs(tmp_path / "non_existent.csv")

    # Test missing required column
    bad_df = sample_runs_df.drop(columns=["sodium_mg"])
    bad_csv = tmp_path / "bad.csv"
    bad_df.to_csv(bad_csv, index=False)
    with pytest.raises(ValueError, match="Missing required columns"):
        load_weekly_runs(bad_csv)


def test_audit_sodium(sample_runs_df: pd.DataFrame):
    """Test sodium audit detects records exceeding 3000 mg."""
    viols, summary = audit_sodium(sample_runs_df, max_sodium_mg=3000.0)

    assert len(viols) == 1
    assert viols.iloc[0]["sodium_mg"] == 3500.0
    assert summary["n_violations"] == 1
    assert summary["total_days"] == 4
    assert summary["compliance_pct"] == 75.0
    assert summary["max_sodium_found"] == 3500.0


def test_audit_fiber(sample_runs_df: pd.DataFrame):
    """Test fiber audit correctly aggregates mean and tolerance percentages."""
    summary = audit_fiber(sample_runs_df, PROFILE_STANDARDS)

    assert "by_profile" in summary
    assert "p1" in summary["by_profile"]
    p1_stats = summary["by_profile"]["p1"]
    assert p1_stats["target_g"] == 38.0
    assert p1_stats["mean_g"] == pytest.approx(36.5)
    assert p1_stats["in_tolerance_pct"] == 100.0
    assert p1_stats["ge_25g_pct"] == 100.0


def test_audit_calories(sample_runs_df: pd.DataFrame):
    """Test calorie compliance calculation within ±10% margin."""
    summary = audit_calories(sample_runs_df, PROFILE_STANDARDS)

    assert summary["overall_within_10pct_pct"] == 100.0
    p1_stats = summary["by_profile"]["p1"]
    assert p1_stats["within_10pct_pct"] == 100.0
    assert p1_stats["within_5pct_pct"] == 100.0


def test_generate_detailed_report(sample_runs_df: pd.DataFrame):
    """Test enrichment of DataFrame with compliance indicator columns."""
    enriched = generate_detailed_report(sample_runs_df, PROFILE_STANDARDS)

    assert "target_calories" in enriched.columns
    assert "calorie_dev_pct" in enriched.columns
    assert "calorie_compliant_10pct" in enriched.columns
    assert "sodium_violates_3000mg" in enriched.columns

    assert enriched.loc[0, "calorie_compliant_10pct"] is True or enriched.loc[0, "calorie_compliant_10pct"] == True
    assert bool(enriched.loc[1, "sodium_violates_3000mg"]) is True


def test_run_validation_end_to_end(tmp_path: Path, sample_runs_df: pd.DataFrame):
    """Test end-to-end execution of run_validation."""
    input_csv = tmp_path / "weekly_runs.csv"
    sample_runs_df.to_csv(input_csv, index=False)
    outdir = tmp_path / "output"

    enriched_df, summary_md = run_validation(input_csv, outdir)

    assert (outdir / "validation_report.csv").exists()
    assert (outdir / "validation_summary.md").exists()
    assert "BÁO CÁO THẨM ĐỊNH" in summary_md
    assert len(enriched_df) == 4


def test_main_cli(tmp_path: Path, sample_runs_df: pd.DataFrame, monkeypatch: pytest.MonkeyPatch):
    """Test CLI entry point main() parses arguments and executes validation."""
    input_csv = tmp_path / "weekly_runs.csv"
    sample_runs_df.to_csv(input_csv, index=False)
    outdir = tmp_path / "cli_output"

    monkeypatch.setattr(
        "sys.argv",
        ["validate_week9_data.py", "--input", str(input_csv), "--outdir", str(outdir)],
    )

    main()

    assert (outdir / "validation_report.csv").exists()
    assert (outdir / "validation_summary.md").exists()

