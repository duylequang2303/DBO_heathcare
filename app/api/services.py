"""
Core API services - bridge between FastAPI and existing solver code
"""
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.user_profile import UserProfile, Gender, ActivityLevel, Goal, DietType
from src.utils.data_loader import load_food_db, build_food_map
from src.utils.nutrition import daily_all_targets
from src.algorithms.two_tier_solver import two_tier_optimize, TwoTierConfig, TwoTierResult
from src.algorithms.menu_objective import decode_result
from src.models.constraints import validate_menu
from src.models.food_selector import get_meal_order_slots
from src.utils.portion_utils import round_portions
from app.api.schemas import ProfileIn, MacroNutrition, TargetsOut, MenuItem, MenuOut

# Singleton food database
_FOOD_DB = None
_FOOD_MAP = None

def get_food_db():
    """Load food database once (singleton pattern)"""
    global _FOOD_DB, _FOOD_MAP
    if _FOOD_DB is None:
        _FOOD_DB = load_food_db()
        _FOOD_MAP = build_food_map(_FOOD_DB)
        print(f"Loaded {len(_FOOD_MAP)} foods from database")
    return _FOOD_DB, _FOOD_MAP

def profile_in_to_user_profile(profile_in: ProfileIn) -> UserProfile:
    """Convert API ProfileIn to internal UserProfile"""
    # Map API goal format to internal format
    goal_map = {
        "LOSE_WEIGHT": Goal.LOSE_WEIGHT,
        "MAINTAIN": Goal.MAINTAIN,
        "GAIN_WEIGHT": Goal.GAIN_WEIGHT
    }
    
    return UserProfile(
        name=profile_in.name,
        age=profile_in.age,
        gender=Gender(profile_in.gender),
        height_cm=profile_in.height_cm,
        weight_kg=profile_in.weight_kg,
        activity_level=ActivityLevel[profile_in.activity_level],
        goal=goal_map[profile_in.goal],
        meal_counts=profile_in.meal_counts,
        medical_conditions=profile_in.medical_conditions,
        allergies=profile_in.allergies,
        dislikes=profile_in.dislikes,
        diet_type=DietType.STANDARD
    )

def get_profiles() -> list[dict]:
    """Get 3 preset profiles P1, P2, P3"""
    return [
        {
            "id": "p1",
            "name": "Duy",
            "age": 22,
            "gender": "male",
            "height_cm": 170.0,
            "weight_kg": 65.0,
            "activity_level": "MODERATE",
            "goal": "MAINTAIN",
            "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
            "medical_conditions": ["healthy"],
            "allergies": [],
            "dislikes": []
        },
        {
            "id": "p2",
            "name": "Lan",
            "age": 45,
            "gender": "female",
            "height_cm": 158.0,
            "weight_kg": 62.0,
            "activity_level": "LIGHT",
            "goal": "LOSE_WEIGHT",
            "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
            "medical_conditions": ["diabetes"],
            "allergies": [],
            "dislikes": []
        },
        {
            "id": "p3",
            "name": "Minh",
            "age": 55,
            "gender": "male",
            "height_cm": 168.0,
            "weight_kg": 75.0,
            "activity_level": "SEDENTARY",
            "goal": "MAINTAIN",
            "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
            "medical_conditions": ["hypertension"],
            "allergies": [],
            "dislikes": []
        }
    ]

def calculate_targets(profile: UserProfile) -> dict:
    """Calculate BMR, TDEE and macro targets for a profile"""
    from src.utils.nutrition import calc_bmr, calc_tdee
    
    bmr = calc_bmr(profile)
    tdee = calc_tdee(profile)
    targets = daily_all_targets(profile)
    
    # Add condition-specific constraints
    if "diabetes" in profile.medical_conditions:
        targets["sugar_g"] = 25.0
    if "hypertension" in profile.medical_conditions:
        targets["sodium_mg"] = 1500.0
    
    return {
        "bmr": bmr,
        "tdee": tdee,
        "targets": targets
    }

def get_config_for_mode(mode: str) -> TwoTierConfig:
    """Get solver config for different modes"""
    if mode == "smoke":
        return TwoTierConfig(
            outer_algo="idbo",
            outer_n_agents=6,
            outer_max_iter=5,
            inner_algo="idbo",
            inner_n_agents=6,
            inner_max_iter=5,
        )
    elif mode == "web":
        return TwoTierConfig(
            outer_algo="idbo",
            outer_n_agents=10,
            outer_max_iter=25,
            inner_algo="idbo",
            inner_n_agents=10,
            inner_max_iter=25,
        )
    else:  # full
        return TwoTierConfig(
            outer_algo="idbo",
            outer_n_agents=20,
            outer_max_iter=100,
            inner_algo="idbo",
            inner_n_agents=15,
            inner_max_iter=50,
        )

def generate_menu(profile: UserProfile, seed: int, config_mode: str = "web") -> dict:
    """Generate menu using two_tier_optimize"""
    _, food_map = get_food_db()
    
    # Calculate targets
    targets_data = calculate_targets(profile)
    targets = targets_data["targets"]
    
    # Get config
    config = get_config_for_mode(config_mode)
    config.seed = seed
    
    # Run solver
    result: TwoTierResult = two_tier_optimize(profile, food_map, targets, config)
    
    # Decode result
    menu = decode_result(
        result.best_food_ids,
        result.best_portions_g,
        food_map,
        profile.meal_counts
    )
    
    # Validate
    violations = validate_menu(menu, profile, targets)
    
    # Round portions for display
    rounded_portions = round_portions(result.best_portions_g, step=5)
    menu_rounded = decode_result(
        result.best_food_ids,
        rounded_portions,
        food_map,
        profile.meal_counts
    )
    
    # Build response
    meal_order = get_meal_order_slots(profile.meal_counts)
    items = []
    for idx, (food_id, meal_type) in enumerate(zip(result.best_food_ids, meal_order)):
        food = food_map[food_id]
        portion_orig = result.best_portions_g[idx]
        portion_round = int(rounded_portions[idx])
        
        # Calculate macros for rounded portion
        factor = portion_round / 100.0
        macros = MacroNutrition(
            calories=food.get("calories", 0) * factor,
            protein_g=food.get("protein_g", 0) * factor,
            carbs_g=food.get("carbs_g", 0) * factor,
            fat_g=food.get("fat_g", 0) * factor,
            fiber_g=food.get("fiber_g", 0) * factor,
            sodium_mg=food.get("sodium_mg", 0) * factor
        )
        
        items.append(MenuItem(
            food_id=food_id,
            name=food.get("name", "Unknown"),
            slot=meal_type,
            meal_type=food.get("meal_type", "all"),
            portion_g=portion_orig,
            portion_g_rounded=portion_round,
            macros=macros
        ))
    
    # Calculate totals from rounded menu
    totals = MacroNutrition(
        calories=menu_rounded.total("calories"),
        protein_g=menu_rounded.total("protein_g"),
        carbs_g=menu_rounded.total("carbs_g"),
        fat_g=menu_rounded.total("fat_g"),
        fiber_g=menu_rounded.total("fiber_g"),
        sodium_mg=menu_rounded.total("sodium_mg")
    )
    
    targets_out = MacroNutrition(
        calories=targets.get("calories", 0),
        protein_g=targets.get("protein_g", 0),
        carbs_g=targets.get("carbs_g", 0),
        fat_g=targets.get("fat_g", 0),
        fiber_g=targets.get("fiber_g", 0),
        sodium_mg=targets.get("sodium_mg", 2300)
    )
    
    return {
        "items": items,
        "totals": totals,
        "targets": targets_out,
        "fitness": result.best_fitness,
        "violations": violations,
        "runtime_s": result.runtime_s
    }
