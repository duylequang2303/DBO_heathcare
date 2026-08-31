from ..models.user_profile import Goal, UserProfile


def calc_bmr(profile: UserProfile) -> float:
    if profile.gender.value == "male":
        return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
    return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161


def calc_tdee(profile: UserProfile) -> float:
    return calc_bmr(profile) * profile.activity_level.value


def calc_calorie_target(profile: UserProfile) -> float:
    tdee = calc_tdee(profile)
    if profile.goal == Goal.LOSE_WEIGHT:
        return tdee - 500
    if profile.goal == Goal.GAIN_WEIGHT:
        return tdee + 300
    return tdee


def calc_macro_targets(calorie_target: float, goal: Goal) -> dict[str, float]:
    if goal == Goal.LOSE_WEIGHT:
        protein_ratio, carb_ratio, fat_ratio = 0.30, 0.40, 0.30
    elif goal == Goal.GAIN_WEIGHT:
        protein_ratio, carb_ratio, fat_ratio = 0.25, 0.50, 0.25
    else:
        protein_ratio, carb_ratio, fat_ratio = 0.20, 0.50, 0.30
    return {
        "calories": calorie_target,
        "protein_g": calorie_target * protein_ratio / 4,
        "carbs_g": calorie_target * carb_ratio / 4,
        "fat_g": calorie_target * fat_ratio / 9,
    }


def daily_targets(profile: UserProfile) -> dict[str, float]:
    calorie_target = calc_calorie_target(profile)
    targets = calc_macro_targets(calorie_target, profile.goal)
    targets["fiber_g"] = 25.0 if profile.gender == "female" else 38.0
    return targets
