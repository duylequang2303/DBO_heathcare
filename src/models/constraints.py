from .menu import MealType, Menu
from .user_profile import UserProfile
from .dish_category import classify_dish_role, get_role_portion_bounds

PORTION_RANGE = {"min": 25.0, "max": 350.0}
ENERGY_TOLERANCE = 0.10
MACRO_TOLERANCE = {
    "protein_g": 0.15,
    "carbs_g": 0.15,
    "fat_g": 0.20,
    "fiber_g": 0.30,
}
DEFAULT_MAX_SODIUM_MG: float = 2300.0  # DRI CDRR ceiling for healthy adults (mg/day)
HYPERTENSION_MAX_SODIUM_MG: float = 1500.0  # AHA / clinical guideline for hypertension (mg/day)
MAX_SODIUM_TOLERANCE_MG: float = 3000.0  # Technical upper tolerance ceiling (mg/day)
MEAL_TYPE_ALLOWED = {
    MealType.BREAKFAST: {"breakfast"},
    MealType.SNACK: {"snack"},
    MealType.LUNCH: {"all"},
    MealType.DINNER: {"all"},
}


def validate_menu(
    menu: Menu,
    profile: UserProfile,
    targets: dict[str, float],
    food_map: dict | None = None,
) -> list[str]:
    violations: list[str] = []
    violations += _check_energy(menu, targets["calories"])
    violations += _check_macros(menu, targets)
    violations += _check_medical_constraints(menu, profile, targets)
    violations += _check_meal_count(menu, profile.meal_counts)
    violations += _check_portion(menu, food_map)
    violations += _check_dislikes(menu, profile.dislikes)
    violations += _check_allergies(menu, profile.allergies)
    violations += _check_duplicates(menu)
    violations += _check_meal_type(menu)
    return violations


def is_feasible(
    menu: Menu, profile: UserProfile, targets: dict[str, float], food_map: dict | None = None
) -> bool:
    return len(validate_menu(menu, profile, targets, food_map)) == 0


def _check_energy(menu: Menu, calorie_target: float) -> list[str]:
    total = menu.total("calories")
    low = calorie_target * (1 - ENERGY_TOLERANCE)
    high = calorie_target * (1 + ENERGY_TOLERANCE)
    if not (low <= total <= high):
        return [f"energy {total:.0f} kcal outside [{low:.0f}, {high:.0f}]"]
    return []


def _check_macros(menu: Menu, targets: dict[str, float]) -> list[str]:
    issues = []
    for key, tol in MACRO_TOLERANCE.items():
        actual = menu.total(key)
        target = targets.get(key, 0.0)
        low = target * (1 - tol)
        high = target * (1 + tol)
        if not (low <= actual <= high):
            issues.append(f"{key}: {actual:.1f} outside [{low:.1f}, {high:.1f}]")
    return issues


def _check_sodium(
    menu: Menu, profile: UserProfile, targets: dict[str, float]
) -> list[str]:
    """Validate sodium against clinical condition limits and general DRI CDRR ceilings.

    - Hypertension: Enforces stricter clinical target (min of targets['sodium_mg'] and 1500 mg).
    - General/Healthy/Other: Enforces DRI CDRR ceiling (targets['sodium_mg'] or 2300 mg, capped at 3000 mg).
    """
    conditions = {str(value).strip().lower() for value in profile.medical_conditions}
    issues: list[str] = []
    if "hypertension" in conditions:
        limit = min(float(targets.get("sodium_mg", HYPERTENSION_MAX_SODIUM_MG)), HYPERTENSION_MAX_SODIUM_MG)
    elif "sodium_mg" in targets:
        limit = min(float(targets["sodium_mg"]), MAX_SODIUM_TOLERANCE_MG)
    else:
        limit = DEFAULT_MAX_SODIUM_MG

    actual = menu.total("sodium_mg")
    if actual > limit:
        issues.append(f"sodium_mg: {actual:.1f} exceeds {limit:.1f}")
    return issues


def _check_medical_constraints(
    menu: Menu, profile: UserProfile, targets: dict[str, float]
) -> list[str]:
    """Validate only condition constraints backed by nutrients in the dataset.

    Sodium is available in the merged database and enforced for all profiles
    (with clinical restrictions for hypertension and general DRI CDRR ceiling
    for healthy/other profiles). The current dataset has no total-sugar column,
    so diabetes must not be declared safe from a carbohydrate-derived sugar estimate.
    """
    return _check_sodium(menu, profile, targets)

def _check_meal_count(menu: Menu, meal_counts: dict[str, int]) -> list[str]:
    issues = []
    for meal_type in MealType:
        actual = len(menu.meals[meal_type].items)
        expected = meal_counts.get(meal_type.value, 1)
        if actual != expected:
            issues.append(f"{meal_type.value}: {actual} items (expected {expected})")
    return issues


def _check_portion(menu: Menu, food_map: dict | None = None) -> list[str]:
    issues = []
    for item in menu.all_items():
        if food_map is not None:
            row = food_map.get(item.food_id, {})
            role = classify_dish_role(item.food_name, str(row.get("category", "")))
            low, high = get_role_portion_bounds(role)
        else:
            low, high = PORTION_RANGE["min"], PORTION_RANGE["max"]
        if not (low <= item.portion_g <= high):
            issues.append(
                f"{item.food_name}: portion {item.portion_g:.0f}g out of range [{low:.0f}, {high:.0f}]"
            )
    return issues


def _check_dislikes(menu: Menu, dislikes: list[str]) -> list[str]:
    return _match_tokens(menu, dislikes, "disliked")


def _check_allergies(menu: Menu, allergies: list[str]) -> list[str]:
    return _match_tokens(menu, allergies, "allergen")


def _match_tokens(menu: Menu, tokens: list[str], label: str) -> list[str]:
    issues = []
    for item in menu.all_items():
        name = item.food_name.lower()
        for token in tokens:
            if token and token.lower() in name:
                issues.append(f"{item.food_name}: contains {label} '{token}'")
    return issues


def _check_duplicates(menu: Menu) -> list[str]:
    issues = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for item in menu.all_items():
        if item.food_id in seen_ids:
            issues.append(f"duplicate food_id {item.food_id}")
        seen_ids.add(item.food_id)
        name = item.food_name.lower().strip()
        if name and name in seen_names:
            issues.append(f"duplicate food_name {item.food_name}")
        if name:
            seen_names.add(name)
    return issues


def _check_meal_type(menu: Menu) -> list[str]:
    issues = []
    for meal_type, meal in menu.meals.items():
        allowed = MEAL_TYPE_ALLOWED[meal_type]
        for item in meal.items:
            item_type = getattr(item, "meal_type", "") or ""
            if not item_type:
                continue
            if item_type not in allowed:
                issues.append(
                    f"{item.food_name}: meal_type '{item_type}' not allowed in {meal_type.value}"
                )
    return issues
