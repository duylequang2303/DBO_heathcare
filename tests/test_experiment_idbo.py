import csv
import sys
from types import SimpleNamespace

import pytest

from scripts import experiment_idbo


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames, list(reader)


@pytest.mark.parametrize("algorithm,diversity", [("dbo", []), ("idbo", [0.2, 0.1])])
def test_run_single_preserves_optimizer_histories(monkeypatch, algorithm, diversity):
    result = SimpleNamespace(
        best_fitness=1.5, runtime_s=0.12345, n_evaluations=42, history=[3.0, 1.5]
    )
    if diversity:
        result.diversity_history = diversity
        result.n_perturbations = 2
        result.n_restarts = 1

    calls = []

    class FakeOptimizer:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def optimize(self, **kwargs):
            calls.append(kwargs)
            return result

    monkeypatch.setattr(experiment_idbo, "DBO", FakeOptimizer)
    monkeypatch.setattr(experiment_idbo, "IDBO", FakeOptimizer)

    row = experiment_idbo.run_single(algorithm, "sphere", 10, 3, 1203, 5, 2)

    assert calls[0] == {"n_agents": 5, "max_iter": 2, "behaviors": None}
    assert calls[1]["dim"] == 10
    assert calls[1]["seed"] == 1203
    assert row["algorithm"] == algorithm
    assert row["run"] == 3
    assert row["history"] is result.history
    assert row["diversity_history"] == diversity
    assert row["n_perturbations"] == (2 if diversity else 0)
    assert row["n_restarts"] == (1 if diversity else 0)


def test_run_single_rejects_unknown_algorithm():
    with pytest.raises(ValueError, match="unknown algorithm"):
        experiment_idbo.run_single("other", "sphere", 10, 1, 1, 5, 2)


@pytest.mark.parametrize("dimensions", [[2, 10], [2]])
def test_main_exports_only_dim10_histories_and_keeps_original_csvs(monkeypatch, tmp_path, dimensions):
    calls = []

    def fake_run_single(algorithm, benchmark_name, dim, run_idx, seed, **kwargs):
        calls.append((algorithm, dim, run_idx, seed))
        fitness = dim + run_idx + (1 if algorithm == "idbo" else 0)
        return {
            "algorithm": algorithm,
            "function": benchmark_name,
            "category": "unimodal",
            "dim": dim,
            "run": run_idx,
            "seed": seed,
            "best_fitness": fitness,
            "runtime_s": 0.1,
            "n_evaluations": 4,
            "n_perturbations": 0,
            "n_restarts": 0,
            "execution_order": 0,
            "history": [fitness + 2, fitness + 1, fitness],
            "diversity_history": [0.2, 0.1] if algorithm == "idbo" else [999],
        }

    monkeypatch.setattr(experiment_idbo, "run_single", fake_run_single)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "experiment_idbo.py", "--functions", "sphere", "--dims",
            *map(str, dimensions), "--runs", "2", "--algorithms", "dbo", "idbo",
            "--out-dir", str(tmp_path),
        ],
    )
    experiment_idbo.main()

    run_fields, runs = read_csv(tmp_path / "idbo_vs_dbo_runs.csv")
    assert len(runs) == 4 * len(dimensions)
    assert "history" not in run_fields
    assert "diversity_history" not in run_fields
    for dim in dimensions:
        for run_idx in (1, 2):
            pair = [row for row in runs if int(row["dim"]) == dim and int(row["run"]) == run_idx]
            assert {row["algorithm"] for row in pair} == {"dbo", "idbo"}
            assert len({row["seed"] for row in pair}) == 1
            assert {int(row["execution_order"]) for row in pair} == {1, 2}

    history_fields, history = read_csv(tmp_path / "idbo_vs_dbo_history.csv")
    diversity_fields, diversity = read_csv(tmp_path / "idbo_diversity.csv")
    assert history_fields == ["algorithm", "function", "dim", "run", "iteration", "best_fitness"]
    assert diversity_fields == ["function", "dim", "run", "iteration", "diversity"]
    assert len(history) == (12 if 10 in dimensions else 0)
    assert len(diversity) == (4 if 10 in dimensions else 0)
    if 10 in dimensions:
        for algorithm in ("dbo", "idbo"):
            for run_idx in (1, 2):
                expected_fitness = 10 + run_idx + (algorithm == "idbo")
                actual = [
                    row for row in history
                    if row["algorithm"] == algorithm and int(row["run"]) == run_idx
                ]
                assert [int(row["iteration"]) for row in actual] == [0, 1, 2]
                assert [float(row["best_fitness"]) for row in actual] == [
                    expected_fitness + 2, expected_fitness + 1, expected_fitness
                ]
    assert {row["function"] for row in diversity} <= {"sphere"}
    assert all(int(row["dim"]) == 10 for row in diversity)
    if 10 in dimensions:
        for run_idx in (1, 2):
            actual = [row for row in diversity if int(row["run"]) == run_idx]
            assert [int(row["iteration"]) for row in actual] == [1, 2]
            assert [float(row["diversity"]) for row in actual] == [0.2, 0.1]

    _, summaries = read_csv(tmp_path / "idbo_vs_dbo_summary.csv")
    assert len(summaries) == 2 * len(dimensions)
    assert all(row["runs"] == "2" for row in summaries)
    assert all(float(row["mean_n_evaluations"]) == 4 for row in summaries)
    assert len(calls) == len(runs)
