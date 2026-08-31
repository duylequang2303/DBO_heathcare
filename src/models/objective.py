from ..models.menu import Menu
from ..models.user_profile import UserProfile
from .constraints import validate_menu

WEIGHTS = {
    "energy": 1.0,
    "macros": 0.8,
    "preference": 0.6,
    "diversity": 0.4,
    "constraint_penalty": 10.0,
}


def evaluate(menu: Menu, profile: UserProfile, targets: dict[str, float]) -> float:
    score = 0.0
    score += _energy_score(menu, targets["calories"]) * WEIGHTS["energy"]
    score += _macro_score(menu, targets) * WEIGHTS["macros"]
    score += _preference_score(menu, profile) * WEIGHTS["preference"]
    score += _diversity_score(menu) * WEIGHTS["diversity"]
    violations = validate_menu(menu, profile, targets)
    score -= WEIGHTS["constraint_penalty"] * len(violations)
    return score


def _energy_score(menu: Menu, calorie_target: float) -> float:
    total = menu.total("calories")
    if calorie_target == 0:
        return 0.0
    return 100.0 * max(0.0, 1.0 - abs(total - calorie_target) / calorie_target)


def _macro_score(menu: Menu, targets: dict[str, float]) -> float:
    total_score = 0.0
    for key in ["protein_g", "carbs_g", "fat_g", "fiber_g"]:
        target = targets.get(key, 0.0)
        if target == 0:
            continue
        actual = menu.total(key)
        deviation = abs(actual - target) / target
        total_score += 100.0 * max(0.0, 1.0 - deviation)
    return total_score / 4.0


def _preference_score(menu: Menu, profile: UserProfile) -> float:
    items = menu.all_items()
    if not items:
        return 0.0
    disliked = 0
    for item in items:
        for token in profile.dislikes:
            if token.lower() in item.food_name.lower():
                disliked += 1
                break
    return 100.0 * (1.0 - disliked / len(items))


def _diversity_score(menu: Menu) -> float:
    names = {item.food_name.lower() for item in menu.all_items()}
    total = len(menu.all_items())
    if total == 0:
        return 0.0
    return 100.0 * len(names) / total
