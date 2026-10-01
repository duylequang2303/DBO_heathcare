"""Adapter connecting IDBO continuous optimization to the Menu objective function."""

from __future__ import annotations

from typing import Callable
import numpy as np

from src.models.menu import Menu
from src.models.objective import evaluate
from src.models.user_profile import UserProfile


def make_menu_objective(
    profile: UserProfile,
    food_ids: list[str],
    food_map: dict,
    targets: dict[str, float],
) -> Callable[[np.ndarray], float]:
    """Create a continuous minimization objective function for IDBO/DBO.

    objective(x) = -evaluate(Menu.decode(food_ids, x, food_map, meal_counts), profile, targets)
    where evaluate() returns fitness in [-100, 100] (higher is better).
    Since DBO/IDBO minimizes, objective(x) returns -fitness (lower is better).
    """
    meal_counts = profile.meal_counts
    expected_dim = sum(meal_counts.values())

    if len(food_ids) != expected_dim:
        raise ValueError(
            f"len(food_ids) ({len(food_ids)}) must match sum(meal_counts) ({expected_dim})"
        )

    cached_targets = dict(targets)

    def objective(x: np.ndarray) -> float:
        """Evaluate continuous portion vector x and return negative menu fitness."""
        if len(x) != expected_dim:
            raise ValueError(
                f"len(x) ({len(x)}) must equal dim ({expected_dim})"
            )
        portions_g = [float(val) for val in x]
        menu = Menu.decode(
            food_ids=food_ids,
            portions_g=portions_g,
            food_map=food_map,
            meal_counts=meal_counts,
        )
        score = evaluate(menu, profile, cached_targets)
        return -float(score)

    return objective


def decode_result(
    food_ids: list[str],
    x: np.ndarray,
    food_map: dict,
    meal_counts: dict[str, int],
) -> Menu:
    """Helper to decode continuous solution vector back to Menu."""
    portions_g = [float(val) for val in x]
    return Menu.decode(
        food_ids=food_ids,
        portions_g=portions_g,
        food_map=food_map,
        meal_counts=meal_counts,
    )
