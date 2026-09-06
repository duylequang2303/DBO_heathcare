from ..models.user_profile import Gender, Goal, UserProfile


def calc_bmr(profile: UserProfile) -> float:
    """Calculate Basal Metabolic Rate (BMR) using Mifflin-St Jeor formula."""
    if profile.gender.value == "male":
        return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
    return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161


def calc_tdee(profile: UserProfile) -> float:
    """Calculate Total Daily Energy Expenditure (TDEE) based on activity level."""
    return calc_bmr(profile) * profile.activity_level.value


def calc_calorie_target(profile: UserProfile) -> float:
    """Calculate target daily calories adjusted for user goal."""
    tdee = calc_tdee(profile)
    if profile.goal == Goal.LOSE_WEIGHT:
        return tdee - 500
    if profile.goal == Goal.GAIN_WEIGHT:
        return tdee + 300
    return tdee


def calc_macro_targets(calorie_target: float, goal: Goal) -> dict[str, float]:
    """Calculate macronutrient distribution (protein, carbs, fat) in grams."""
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
    """Calculate daily macro targets including gender-adjusted fiber requirements."""
    calorie_target = calc_calorie_target(profile)
    targets = calc_macro_targets(calorie_target, profile.goal)
    is_female = (profile.gender == Gender.FEMALE) or (getattr(profile.gender, "value", profile.gender) == "female")
    targets["fiber_g"] = 25.0 if is_female else 38.0
    return targets


def daily_micro_targets(profile: UserProfile) -> dict[str, float]:
    """Calculate age- and gender-aware daily micronutrient targets based on DRI tables.

    Supports adult profiles (age >= 18):
    - Sodium: <= 2300 mg (UL / CDRR)
    - Calcium: 1000 mg (18-50), 1200 mg (females > 50 or males > 70)
    - Iron: 18 mg (females 18-50), 8 mg (males and females > 50)
    - Vitamin C: 90 mg (males), 75 mg (females)
    """
    if profile.age < 18:
        raise ValueError(f"Age {profile.age} is outside supported adult age range (>= 18)")

    is_female = (profile.gender == Gender.FEMALE) or (getattr(profile.gender, "value", profile.gender) == "female")

    # Iron: 18 mg for females 18-50, 8 mg for males and females > 50
    if is_female and profile.age <= 50:
        iron_mg = 18.0
    else:
        iron_mg = 8.0

    # Calcium: 1200 mg for females > 50 and all adults > 70, otherwise 1000 mg
    if (is_female and profile.age > 50) or profile.age > 70:
        calcium_mg = 1200.0
    else:
        calcium_mg = 1000.0

    vitamin_c_mg = 75.0 if is_female else 90.0

    return {
        "sodium_mg": 2300.0,
        "calcium_mg": calcium_mg,
        "iron_mg": iron_mg,
        "vitamin_c_mg": vitamin_c_mg,
    }


def daily_all_targets(profile: UserProfile) -> dict[str, float]:
    """Combine macronutrient and micronutrient targets into a single target dictionary."""
    targets = daily_targets(profile)
    targets.update(daily_micro_targets(profile))
    return targets


