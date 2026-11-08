"""Regression coverage for benchmark, dislike and cooked presentation fixes."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from scripts import run_remediation_benchmark as benchmark
from src.models.allergen_rules import is_allergen_conflict, is_dislike_conflict
from src.models.dish_category import DishRole
from src.models.dish_presentation import present_dish


@pytest.mark.parametrize('token', ['hải sản', 'hai san', 'seafood', 'đồ biển'])
def test_generic_dislikes_keep_group_matching(token):
    assert is_dislike_conflict('Tôm hấp', [token])


def test_specific_dislikes_and_exclusions():
    assert is_dislike_conflict('Cá hồi áp chảo', ['cá hồi'])
    assert not is_dislike_conflict('Cá ngừ kho', ['cá hồi'])
    assert not is_dislike_conflict('Tôm hấp', ['cá'])
    assert not is_dislike_conflict('Rau giấp cá', ['cá'])
    assert not is_dislike_conflict('Cá hồix', ['cá hồi'])
    assert is_allergen_conflict('Tôm hấp', ['cá hồi'])


@pytest.mark.parametrize('name,role', [
    ('Khoai luộc', DishRole.STAPLE), ('Gạo nấu', DishRole.STAPLE),
    ('Thịt bò xào', DishRole.MAIN_PROTEIN), ('Cá hồi áp chảo', DishRole.MAIN_PROTEIN),
    ('Trứng luộc', DishRole.MAIN_PROTEIN),
])
def test_cooked_items_keep_name_and_basis(name, role):
    result = present_dish(name, role=role)
    assert result.display_name == name
    assert result.preparation == result.ingredient_basis == 'món chín'


def test_bootstrap_empty_and_constant():
    assert all(np.isnan(benchmark.compute_bootstrap_ci(np.array([]))))
    assert benchmark.compute_bootstrap_ci(np.array([3., 3.])) == (3., 3.)


def test_random_search_rounds_with_winning_candidate_bounds(monkeypatch):
    seen_pool_sizes = []
    def pools(**kwargs):
        seen_pool_sizes.append(kwargs['min_pool_size'])
        return {}
    monkeypatch.setattr(benchmark, 'build_meal_pools', pools)
    monkeypatch.setattr(benchmark, 'get_meal_order_slots', lambda _: [0])
    candidates = iter([[0], [1], [1], [1], [1]])
    monkeypatch.setattr(benchmark, 'decode_food_selection', lambda *args: next(candidates))
    monkeypatch.setattr(benchmark, 'classify_dish_role', lambda name, *args: name)
    monkeypatch.setattr(benchmark, 'get_role_portion_bounds', lambda role: (10, 20) if role == 'winner' else (100, 200))
    monkeypatch.setattr(benchmark, 'make_menu_objective', lambda profile, ids, *args: lambda x: -10 if ids == [0] else -1)
    result = benchmark.run_random_search_baseline(SimpleNamespace(meal_counts={}),
        {0: {'food_name': 'winner'}, 1: {'food_name': 'loser'}}, {}, 10, 42)
    assert seen_pool_sizes == [benchmark.TwoTierConfig().min_pool_size]
    assert result['best_food_ids'] == [0]
    assert 10 <= result['rounded_portions_g'][0] <= 20
    assert result['rounded_fitness'] == 10


@pytest.mark.parametrize('error', [ValueError, RuntimeError])
def test_wilcoxon_failure_is_nan_and_unexpected_errors_propagate(monkeypatch, tmp_path, error):
    df = pd.read_csv(Path(benchmark.ROOT) / 'experiments/remediation_benchmark/paired_benchmark_results.csv')
    monkeypatch.setattr(benchmark, 'OUT_DIR', tmp_path)
    def fail(*args, **kwargs):
        raise error('test failure')
    monkeypatch.setattr(benchmark.stats, 'wilcoxon', fail)
    if error is RuntimeError:
        with pytest.raises(RuntimeError):
            benchmark.analyze_and_save(df)
    else:
        benchmark.analyze_and_save(df)
        report = (tmp_path / 'README.md').read_text()
        assert 'p-value = **nan**' in report
        assert 'p-value = **nan**' in report.split('IDBO vs DBO (Paired)')[1]
