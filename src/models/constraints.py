from ..models.menu import Menu, MenuItem, MealType
from ..models.user_profile import UserProfile

PORTION_RANGE = {"min": 25.0, "max": 350.0}
ENERGY_TOLERANCE = 0.10


def validate_menu(menu: Menu, profile: UserProfile, targets: dict[str, float]) -> list[str]:
    violations: list[str] = []
    violations += _check_energy(menu, targets["calories"])
    violations += _check_macros(menu, targets)
    violations += _check_meal_count(menu, profile.meal_counts)
    violations += _check_portion(menu)
    violations += _check_dislikes(menu, profile.dislikes)
    return violations


def _check_energy(menu: Menu, calorie_target: float) -> list[str]:
    total = menu.total("calories")
    low = calorie_target * (1 - ENERGY_TOLERANCE)
    high = calorie_target * (1 + ENERGY_TOLERANCE)
    if not (low <= total <= high):
        return [f"energy {total:.0f} kcal outside [{low:.0f}, {high:.0f}]"]
    return []


def _check_macros(menu: Menu, targets: dict[str, float]) -> list[str]:
    issues = []
    for key, tol in [("protein_g", 0.15), ("carbs_g", 0.15), ("fat_g", 0.20), ("fiber_g", 0.30)]:
        actual = menu.total(key)
        target = targets.get(key, 0.0)
        low = target * (1 - tol)
        high = target * (1 + tol)
        if not (low <= actual <= high):
            issues.append(f"{key}: {actual:.1f} outside [{low:.1f}, {high:.1f}]")
    return issues


def _check_meal_count(menu: Menu, meal_counts: dict[str, int]) -> list[str]:
    issues = []
    for meal_type in MealType:
        actual = len(menu.meals[meal_type].items)
        expected = meal_counts.get(meal_type.value, 1)
        if actual != expected:
            issues.append(f"{meal_type.value}: {actual} items (expected {expected})")
    return issues


def _check_portion(menu: Menu) -> list[str]:
    issues = []
    for item in menu.all_items():
        if not (PORTION_RANGE["min"] <= item.portion_g <= PORTION_RANGE["max"]):
            issues.append(f"{item.food_name}: portion {item.portion_g:.0f}g out of range")
    return issues


def _check_dislikes(menu: Menu, dislikes: list[str]) -> list[str]:
    issues = []
    for item in menu.all_items():
        for token in dislikes:
            if token.lower() in item.food_name.lower():
                issues.append(f"{item.food_name}: contains disliked '{token}'")
    return issues
