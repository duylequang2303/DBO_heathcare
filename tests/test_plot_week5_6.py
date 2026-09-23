import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from scripts import plot_week5_6


@pytest.fixture
def saved_figures(monkeypatch):
    figures = []
    original_savefig = plt.savefig

    def savefig(*args, **kwargs):
        figures.append(plt.gcf())
        original_savefig(*args, **kwargs)

    monkeypatch.setattr(plt, "savefig", savefig)
    return figures


def test_convergence_averages_runs_by_iteration_and_clips_zero(tmp_path, saved_figures):
    history_csv = tmp_path / "history.csv"
    pd.DataFrame([
        {"algorithm": algorithm, "function": "sphere", "dim": dim, "run": run,
         "iteration": iteration, "best_fitness": fitness}
        for algorithm, dim, run, iteration, fitness in [
            ("dbo", 10, 1, 1, 2), ("dbo", 10, 2, 1, 6),
            ("dbo", 10, 1, 0, 0), ("dbo", 10, 2, 0, 0),
            ("idbo", 10, 1, 0, 3), ("idbo", 10, 1, 1, 1),
            ("dbo", 2, 1, 1, 500),
        ]
    ]).to_csv(history_csv, index=False)
    output = tmp_path / "convergence.png"

    plot_week5_6.plot_f1_convergence(history_csv, output)

    assert output.is_file() and output.stat().st_size > 0
    figure = saved_figures[0]
    assert len(figure.axes) == 6
    sphere = figure.axes[0]
    assert sphere.get_yscale() == "log"
    assert [line.get_label() for line in sphere.lines] == ["DBO", "IDBO"]
    assert list(sphere.lines[0].get_xdata()) == [0, 1]
    assert list(sphere.lines[0].get_ydata()) == [1e-300, 4]
    assert list(sphere.lines[1].get_ydata()) == [3, 1]
    assert all(axis.get_yscale() == "log" for axis in figure.axes)


def test_boxplot_uses_selected_dimension_and_positive_dynamic_range(tmp_path, saved_figures):
    runs_csv = tmp_path / "runs.csv"
    pd.DataFrame([
        {"algorithm": algorithm, "function": function, "dim": dim, "run": run,
         "best_fitness": fitness}
        for function in plot_week5_6.FUNCTIONS_ORDER
        for algorithm, dim, run, fitness in [
            ("dbo", 10, 1, 1), ("dbo", 10, 2, 2),
            ("idbo", 10, 1, 1000 if function == "sphere" else 3),
            ("idbo", 10, 2, 2000 if function == "sphere" else 4),
            ("dbo", 2, 1, 100000),
        ]
    ]).to_csv(runs_csv, index=False)
    output = tmp_path / "boxplot.png"

    plot_week5_6.plot_f2_boxplot(runs_csv, output)

    assert output.is_file() and output.stat().st_size > 0
    axes = saved_figures[0].axes
    assert len(axes) == 6
    assert axes[0].get_yscale() == "log"
    assert axes[1].get_yscale() == "linear"
    assert [label.get_text() for label in axes[0].get_xticklabels()] == ["DBO", "IDBO"]
    assert "M=2 runs" in saved_figures[0]._suptitle.get_text()


def test_boxplot_keeps_linear_scale_when_fitness_is_nonpositive(tmp_path, saved_figures):
    runs_csv = tmp_path / "runs.csv"
    pd.DataFrame([
        {"algorithm": algorithm, "function": function, "dim": 10, "run": 1,
         "best_fitness": fitness}
        for function in plot_week5_6.FUNCTIONS_ORDER
        for algorithm, fitness in [("dbo", 0), ("idbo", 1000)]
    ]).to_csv(runs_csv, index=False)

    plot_week5_6.plot_f2_boxplot(runs_csv, tmp_path / "boxplot.png")

    assert (tmp_path / "boxplot.png").is_file()
    assert all(axis.get_yscale() == "linear" for axis in saved_figures[0].axes)


def test_diversity_averages_both_functions_and_draws_threshold(tmp_path, saved_figures):
    diversity_csv = tmp_path / "diversity.csv"
    pd.DataFrame([
        {"function": function, "dim": dim, "run": run,
         "iteration": iteration, "diversity": value}
        for function, dim, run, iteration, value in [
            ("sphere", 10, 1, 2, 0.2), ("sphere", 10, 2, 2, 0.4),
            ("sphere", 10, 1, 1, 0.5),
            ("rastrigin", 10, 1, 1, 0.7), ("rastrigin", 10, 1, 2, 0.1),
            ("sphere", 2, 1, 2, 10),
        ]
    ]).to_csv(diversity_csv, index=False)
    output = tmp_path / "diversity.png"

    plot_week5_6.plot_f3_diversity(diversity_csv, output)

    assert output.is_file() and output.stat().st_size > 0
    lines = saved_figures[0].axes[0].lines
    assert len(lines) == 3
    assert list(lines[0].get_xdata()) == [1, 2]
    assert list(lines[0].get_ydata()) == pytest.approx([0.5, 0.3])
    assert list(lines[1].get_ydata()) == pytest.approx([0.7, 0.1])
    assert list(lines[2].get_ydata()) == [1e-3, 1e-3]


@pytest.mark.parametrize("plotter", [
    plot_week5_6.plot_f1_convergence,
    plot_week5_6.plot_f2_boxplot,
    plot_week5_6.plot_f3_diversity,
])
def test_plotters_skip_missing_or_unselected_data(tmp_path, plotter, capsys):
    input_csv = tmp_path / "missing.csv"
    output = tmp_path / "not-created.png"
    plotter(input_csv, output)
    assert not output.exists()
    assert "[WARN]" in capsys.readouterr().out

    pd.DataFrame([{"dim": 2}]).to_csv(input_csv, index=False)
    plotter(input_csv, output)
    assert not output.exists()
    assert "No records found for dim=10" in capsys.readouterr().out


def test_diversity_requires_both_benchmark_functions(tmp_path, capsys):
    input_csv = tmp_path / "diversity.csv"
    pd.DataFrame([{"function": "sphere", "dim": 10, "run": 1,
                   "iteration": 1, "diversity": 0.1}]).to_csv(input_csv, index=False)
    output = tmp_path / "diversity.png"

    plot_week5_6.plot_f3_diversity(input_csv, output)

    assert not output.exists()
    assert "requires both" in capsys.readouterr().out


def test_plot_main_removes_stale_images_and_routes_csv_paths(monkeypatch, tmp_path):
    output_dir = tmp_path / "plots"
    output_dir.mkdir()
    monkeypatch.setattr(plot_week5_6, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["plot_week5_6.py", "--out-dir", "plots", "--dim", "7"])
    calls = []

    for name in ("convergence", "boxplot", "diversity"):
        (output_dir / f"fig_{name}_dim7.png").write_bytes(b"stale")

    for name in ("plot_f1_convergence", "plot_f2_boxplot", "plot_f3_diversity"):
        def capture(input_path, output_path, dim):
            assert not output_path.exists()
            calls.append((input_path.name, output_path.name, dim))

        monkeypatch.setattr(plot_week5_6, name, capture)

    plot_week5_6.main()

    assert calls == [
        ("idbo_vs_dbo_history.csv", "fig_convergence_dim7.png", 7),
        ("idbo_vs_dbo_runs.csv", "fig_boxplot_dim7.png", 7),
        ("idbo_diversity.csv", "fig_diversity_dim7.png", 7),
    ]
