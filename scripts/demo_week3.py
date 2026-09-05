import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.constraints import validate_menu
from src.models.menu import Meal, MealType, Menu, MenuItem
from src.models.objective import evaluate_breakdown
from src.models.user_profile import ActivityLevel, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import calc_bmr, calc_calorie_target, calc_tdee, daily_targets

SAMPLE = [
    (MealType.BREAKFAST, "VN_10009", 88.0),
    (MealType.BREAKFAST, "USDA_2057257", 135.0),
    (MealType.LUNCH, "VN_1004", 171.0),
    (MealType.LUNCH, "VN_7018", 99.0),
    (MealType.DINNER, "VN_8011", 115.0),
    (MealType.DINNER, "VN_4051", 66.0),
    (MealType.SNACK, "VN_5007", 169.0),
    (MealType.SNACK, "USDA_1855534", 48.0),
]


def item_from_map(food_map: dict, food_id: str, portion_g: float) -> MenuItem:
    row = food_map[food_id]
    return MenuItem(
        food_id=food_id,
        food_name=row["food_name"],
        portion_g=portion_g,
        calories=float(row.get("calories") or 0.0),
        protein_g=float(row.get("protein_g") or 0.0),
        carbs_g=float(row.get("carbs_g") or 0.0),
        fat_g=float(row.get("fat_g") or 0.0),
        fiber_g=float(row.get("fiber_g") or 0.0),
        sodium_mg=float(row.get("sodium_mg") or 0.0),
        calcium_mg=float(row.get("calcium_mg") or 0.0),
        iron_mg=float(row.get("iron_mg") or 0.0),
        vitamin_c_mg=float(row.get("vitamin_c_mg") or 0.0),
        meal_type=str(row.get("meal_type") or ""),
    )


def build_sample_menu(food_map: dict) -> Menu:
    menu = Menu()
    grouped: dict[MealType, list[MenuItem]] = {meal_type: [] for meal_type in MealType}
    for meal_type, food_id, portion_g in SAMPLE:
        grouped[meal_type].append(item_from_map(food_map, food_id, portion_g))
    for meal_type, items in grouped.items():
        menu.meals[meal_type] = Meal(meal_type, items)
    return menu


def main() -> None:
    profile = UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        height_cm=170,
        weight_kg=65,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 2},
    )
    bmr = calc_bmr(profile)
    tdee = calc_tdee(profile)
    calorie_target = calc_calorie_target(profile)
    targets = daily_targets(profile)

    print("=== Ho so nguoi dung ===")
    print(f"Ten: {profile.name} | {profile.age} tuoi | {profile.gender.value}")
    print(f"Chieu cao: {profile.height_cm} cm | Can nang: {profile.weight_kg} kg")
    print(f"Van dong: {profile.activity_level.name} | Muc tieu: {profile.goal.value}")
    print()
    print("=== Nhu cau ===")
    print(f"BMR: {bmr:.1f} kcal")
    print(f"TDEE: {tdee:.1f} kcal")
    print(f"Calo muc tieu: {calorie_target:.1f} kcal")
    for key in ("protein_g", "carbs_g", "fat_g", "fiber_g"):
        print(f"{key}: {targets[key]:.1f}")
    print()

    food_df = load_food_db()
    food_map = build_food_map(food_df)
    menu = build_sample_menu(food_map)
    print(f"=== Thuc don mau ({len(food_df)} mon trong CSDL) ===")
    print(menu)
    print()
    print("Tong dinh duong thuc don:")
    for key in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g"):
        print(f"  {key}: {menu.total(key):.1f}")
    print()

    violations = validate_menu(menu, profile, targets)
    breakdown = evaluate_breakdown(menu, profile, targets)
    print("=== Danh gia ===")
    if violations:
        print("Vi pham:")
        for msg in violations:
            print(f"  - {msg}")
    else:
        print("Khong vi pham rang buoc.")
    print(f"energy={breakdown['energy']:.1f} macros={breakdown['macros']:.1f} "
          f"preference={breakdown['preference']:.1f} diversity={breakdown['diversity']:.1f}")
    print(f"penalty={breakdown['penalty']:.1f} fitness={breakdown['fitness']:.1f}")


if __name__ == "__main__":
    main()
