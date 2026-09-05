from .constraints import validate_menu
from .menu import Menu
from .user_profile import UserProfile

WEIGHTS = {
    "energy": 0.35,
    "macros": 0.30,
    "preference": 0.20,
    "diversity": 0.15,
}
PENALTY_PER_VIOLATION = 12.0
MAX_PENALTY = 90.0
FITNESS_MIN = -100.0
FITNESS_MAX = 100.0
MACRO_KEYS = ("protein_g", "carbs_g", "fat_g", "fiber_g")


def evaluate(menu: Menu, profile: UserProfile, targets: dict[str, float]) -> float:
    return evaluate_breakdown(menu, profile, targets)["fitness"]


def evaluate_breakdown(menu: Menu, profile: UserProfile, targets: dict[str, float]) -> dict[str, float]:
    energy = _energy_score(menu, targets["calories"])
    macros = _macro_score(menu, targets)
    preference = _preference_score(menu, profile)
    diversity = _diversity_score(menu)
    weighted = (
        energy * WEIGHTS["energy"]
        + macros * WEIGHTS["macros"]
        + preference * WEIGHTS["preference"]
        + diversity * WEIGHTS["diversity"]
    )
    violations = validate_menu(menu, profile, targets)
    penalty = min(MAX_PENALTY, PENALTY_PER_VIOLATION * len(violations))
    fitness = max(FITNESS_MIN, min(FITNESS_MAX, weighted - penalty))
    return {
        "energy": energy,
        "macros": macros,
        "preference": preference,
        "diversity": diversity,
        "weighted": weighted,
        "penalty": penalty,
        "n_violations": float(len(violations)),
        "fitness": fitness,
    }


def _energy_score(menu: Menu, calorie_target: float) -> float:
    total = menu.total("calories")
    if calorie_target == 0:
        return 0.0
    return 100.0 * max(0.0, 1.0 - abs(total - calorie_target) / calorie_target)


def _macro_score(menu: Menu, targets: dict[str, float]) -> float:
    scores = []
    for key in MACRO_KEYS:
        target = targets.get(key, 0.0)
        if target == 0:
            continue
        actual = menu.total(key)
        scores.append(100.0 * max(0.0, 1.0 - abs(actual - target) / target))
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def _preference_score(menu: Menu, profile: UserProfile) -> float:
    items = menu.all_items()
    if not items:
        return 0.0
    disliked = 0
    for item in items:
        name = item.food_name.lower()
        for token in profile.dislikes:
            if token and token.lower() in name:
                disliked += 1
                break
    dislike_score = 100.0 * (1.0 - disliked / len(items))
    likes = getattr(profile, "likes", None) or []
    if not likes:
        return dislike_score
    liked = 0
    for item in items:
        name = item.food_name.lower()
        for token in likes:
            if token and token.lower() in name:
                liked += 1
                break
    like_score = 100.0 * liked / len(items)
    return 0.6 * dislike_score + 0.4 * like_score


def _diversity_score(menu: Menu) -> float:
    items = menu.all_items()
    if not items:
        return 0.0
    names = {item.food_name.lower().strip() for item in items if item.food_name}
    return 100.0 * len(names) / len(items)
