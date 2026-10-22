import numpy as np
import pytest
from src.algorithms.dbo import DBO
from src.algorithms.idbo import IDBO
from src.algorithms.two_tier_solver import TwoTierConfig

@pytest.mark.parametrize('solver', [DBO, IDBO])
@pytest.mark.parametrize('limit', [8, 9, 16, 27])
def test_budget_never_exceeded(solver, limit):
    kwargs = {'n_agents': 8, 'max_iter': 30, 'max_evaluations': limit}
    if solver is IDBO:
        kwargs.update(diversity_threshold=0.9, stagnation_window=1)
    result = solver(**kwargs).optimize(lambda x: float(np.sum(x*x)), 3, -2, 2, seed=8001)
    assert 8 <= result.n_evaluations <= limit
    assert np.isfinite(result.best_fitness)

@pytest.mark.parametrize('solver', [DBO, IDBO])
def test_reject_budget_below_population(solver):
    with pytest.raises(ValueError, match='max_evaluations'):
        solver(n_agents=8, max_evaluations=7)

def test_thresholds_independent_config():
    cfg = TwoTierConfig(outer_diversity_threshold=0.28, inner_diversity_threshold=0.11)
    assert cfg.outer_diversity_threshold == 0.28
    assert cfg.inner_diversity_threshold == 0.11
