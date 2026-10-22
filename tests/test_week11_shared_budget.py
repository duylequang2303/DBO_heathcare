"""Week 11: verify actual combined outer and inner evaluation limits."""
import pytest
from src.algorithms.two_tier_solver import TwoTierConfig, two_tier_optimize
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets

@pytest.fixture(scope="module")
def inputs():
    p = UserProfile(name="Test", age=22, gender=Gender.MALE, weight_kg=65,
                    height_cm=170, activity_level=ActivityLevel.MODERATE,
                    goal=Goal.MAINTAIN, diet_type=DietType.STANDARD,
                    meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 2},
                    allergies=[], dislikes=[], likes=[])
    return p, build_food_map(load_food_db()), daily_all_targets(p)

@pytest.mark.parametrize("algorithm", ["dbo", "idbo"])
@pytest.mark.parametrize("budget", [35, 60, 150])
def test_shared_budget_never_exceeded(inputs, algorithm, budget):
    p, foods, targets = inputs
    cfg = TwoTierConfig(outer_algo=algorithm, inner_algo=algorithm,
                        outer_n_agents=5, inner_n_agents=5,
                        outer_max_iter=3, inner_max_iter=3,
                        max_evaluations=budget, seed=8001)
    result = two_tier_optimize(p, foods, targets, cfg)
    assert result.function_evaluations <= budget
    assert result.function_evaluations == result.outer_evals + result.inner_evals_total
    assert len(result.inner_fitness_history) == result.outer_evals + 1
    assert result.inner_runtime_total_s >= result.final_inner_runtime_s

@pytest.mark.parametrize("algorithm", ["dbo", "idbo"])
def test_shared_budget_too_small_rejected(inputs, algorithm):
    p, foods, targets = inputs
    cfg = TwoTierConfig(outer_algo=algorithm, inner_algo=algorithm,
                        outer_n_agents=5, inner_n_agents=5,
                        max_evaluations=34)
    with pytest.raises(ValueError, match="max_evaluations"):
        two_tier_optimize(p, foods, targets, cfg)
