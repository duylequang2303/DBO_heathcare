import pytest

from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.nutrition import (
    calc_bmr,
    calc_calorie_target,
    calc_macro_targets,
    calc_tdee,
    daily_all_targets,
    daily_micro_targets,
    daily_targets,
)


@pytest.fixture
def male_profile():
    return UserProfile(
        name="Dang",
        age=22,
        gender=Gender.MALE,
        height_cm=170.0,
        weight_kg=65.0,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
    )


@pytest.fixture
def female_profile():
    return UserProfile(
        name="Lan",
        age=30,
        gender=Gender.FEMALE,
        height_cm=160.0,
        weight_kg=55.0,
        activity_level=ActivityLevel.LIGHT,
        goal=Goal.LOSE_WEIGHT,
    )


# --- UserProfile tests ---


def test_user_profile_defaults(male_profile):
    assert male_profile.medical_conditions == []
    assert male_profile.diet_type == DietType.STANDARD
    assert male_profile.allergies == []
    assert male_profile.dislikes == []
    assert male_profile.likes == []


def test_user_profile_custom_diet_and_conditions():
    profile = UserProfile(
        name="CustomUser",
        age=45,
        gender=Gender.MALE,
        height_cm=175.0,
        weight_kg=78.0,
        activity_level=ActivityLevel.SEDENTARY,
        goal=Goal.LOSE_WEIGHT,
        diet_type=DietType.VEGETARIAN,
        medical_conditions=["diabetes", "hypertension"],
    )
    assert profile.diet_type == DietType.VEGETARIAN
    assert "diabetes" in profile.medical_conditions
    assert "hypertension" in profile.medical_conditions


def test_user_profile_positional_order():
    counts = {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1}
    profile = UserProfile(
        "PosUser", 25, Gender.MALE, 175.0, 70.0, ActivityLevel.MODERATE,
        Goal.MAINTAIN, [], [], [], counts
    )
    assert profile.meal_counts == counts
    assert profile.medical_conditions == []
    assert profile.diet_type == DietType.STANDARD



# --- BMR tests (Mifflin-St Jeor) ---


def test_bmr_male(male_profile):
    # Male formula: 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    # 10*65 + 6.25*170 - 5*22 + 5 = 650 + 1062.5 - 110 + 5 = 1607.5
    expected = 10 * 65.0 + 6.25 * 170.0 - 5 * 22 + 5
    assert calc_bmr(male_profile) == pytest.approx(expected)
    assert calc_bmr(male_profile) == pytest.approx(1607.5)


def test_bmr_female(female_profile):
    # Female formula: 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    # 10*55 + 6.25*160 - 5*30 - 161 = 550 + 1000 - 150 - 161 = 1239.0
    expected = 10 * 55.0 + 6.25 * 160.0 - 5 * 30 - 161
    assert calc_bmr(female_profile) == pytest.approx(expected)
    assert calc_bmr(female_profile) == pytest.approx(1239.0)


def test_bmr_positive(male_profile, female_profile):
    assert calc_bmr(male_profile) > 0
    assert calc_bmr(female_profile) > 0


# --- TDEE tests ---


def test_tdee_calculation(male_profile):
    bmr = calc_bmr(male_profile)
    for level, factor in [
        (ActivityLevel.SEDENTARY, 1.2),
        (ActivityLevel.LIGHT, 1.375),
        (ActivityLevel.MODERATE, 1.55),
        (ActivityLevel.ACTIVE, 1.725),
        (ActivityLevel.VERY_ACTIVE, 1.9),
    ]:
        male_profile.activity_level = level
        assert calc_tdee(male_profile) == pytest.approx(bmr * factor)


# --- Calorie target tests ---


def test_calorie_target_maintain(male_profile):
    male_profile.goal = Goal.MAINTAIN
    assert calc_calorie_target(male_profile) == pytest.approx(calc_tdee(male_profile))


def test_calorie_target_lose_weight(male_profile):
    male_profile.goal = Goal.LOSE_WEIGHT
    assert calc_calorie_target(male_profile) == pytest.approx(calc_tdee(male_profile) - 500)


def test_calorie_target_gain_weight(male_profile):
    male_profile.goal = Goal.GAIN_WEIGHT
    assert calc_calorie_target(male_profile) == pytest.approx(calc_tdee(male_profile) + 300)


# --- Macro targets tests ---


def test_macro_targets_lose_weight():
    targets = calc_macro_targets(2000.0, Goal.LOSE_WEIGHT)
    assert targets["calories"] == 2000.0
    assert targets["protein_g"] == pytest.approx(2000.0 * 0.30 / 4)
    assert targets["carbs_g"] == pytest.approx(2000.0 * 0.40 / 4)
    assert targets["fat_g"] == pytest.approx(2000.0 * 0.30 / 9)


def test_macro_targets_gain_weight():
    targets = calc_macro_targets(2500.0, Goal.GAIN_WEIGHT)
    assert targets["calories"] == 2500.0
    assert targets["protein_g"] == pytest.approx(2500.0 * 0.25 / 4)
    assert targets["carbs_g"] == pytest.approx(2500.0 * 0.50 / 4)
    assert targets["fat_g"] == pytest.approx(2500.0 * 0.25 / 9)


def test_macro_targets_maintain():
    targets = calc_macro_targets(2200.0, Goal.MAINTAIN)
    assert targets["calories"] == 2200.0
    assert targets["protein_g"] == pytest.approx(2200.0 * 0.20 / 4)
    assert targets["carbs_g"] == pytest.approx(2200.0 * 0.50 / 4)
    assert targets["fat_g"] == pytest.approx(2200.0 * 0.30 / 9)


# --- Daily targets & Fiber tests ---


def test_fiber_target_male(male_profile):
    targets = daily_targets(male_profile)
    assert targets["fiber_g"] == 38.0


def test_fiber_target_female(female_profile):
    targets = daily_targets(female_profile)
    assert targets["fiber_g"] == 25.0


def test_daily_targets_all_keys(male_profile):
    targets = daily_targets(male_profile)
    for key in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g"):
        assert key in targets
        assert targets[key] > 0


# --- Micro targets tests ---


def test_daily_micro_targets_male(male_profile):
    micro = daily_micro_targets(male_profile)
    assert micro["sodium_mg"] == 2300.0
    assert micro["calcium_mg"] == 1000.0
    assert micro["iron_mg"] == 8.0
    assert micro["vitamin_c_mg"] == 90.0


def test_daily_micro_targets_female(female_profile):
    micro = daily_micro_targets(female_profile)
    assert micro["sodium_mg"] == 2300.0
    assert micro["calcium_mg"] == 1000.0
    assert micro["iron_mg"] == 18.0
    assert micro["vitamin_c_mg"] == 75.0


def test_daily_micro_targets_older_female():
    profile = UserProfile(
        name="ElderFemale",
        age=55,
        gender=Gender.FEMALE,
        height_cm=158.0,
        weight_kg=52.0,
        activity_level=ActivityLevel.LIGHT,
    )
    micro = daily_micro_targets(profile)
    assert micro["iron_mg"] == 8.0  # post-menopause
    assert micro["calcium_mg"] == 1200.0  # female > 50


def test_daily_micro_targets_older_male():
    profile = UserProfile(
        name="ElderMale",
        age=75,
        gender=Gender.MALE,
        height_cm=168.0,
        weight_kg=60.0,
        activity_level=ActivityLevel.SEDENTARY,
    )
    micro = daily_micro_targets(profile)
    assert micro["iron_mg"] == 8.0
    assert micro["calcium_mg"] == 1200.0  # male > 70


def test_daily_micro_targets_rejects_under_18():
    child = UserProfile(
        name="Child",
        age=16,
        gender=Gender.MALE,
        height_cm=160.0,
        weight_kg=50.0,
        activity_level=ActivityLevel.MODERATE,
    )
    with pytest.raises(ValueError, match="outside supported adult age range"):
        daily_micro_targets(child)



# --- Daily all targets tests ---


def test_daily_all_targets_combination(male_profile):
    all_targets = daily_all_targets(male_profile)
    expected_keys = {
        "calories",
        "protein_g",
        "carbs_g",
        "fat_g",
        "fiber_g",
        "sodium_mg",
        "calcium_mg",
        "iron_mg",
        "vitamin_c_mg",
    }
    assert expected_keys.issubset(set(all_targets.keys()))
    for k in expected_keys:
        assert all_targets[k] > 0
