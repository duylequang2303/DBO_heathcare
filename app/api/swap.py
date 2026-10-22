"""
Swap functionality - replace one menu item and re-optimize portions
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.food_selector import build_meal_pools, get_meal_order_slots
from src.algorithms.idbo import IDBO
from src.algorithms.menu_objective import make_menu_objective, decode_result
from src.models.constraints import validate_menu
from src.utils.portion_utils import round_portions
from app.api.schemas import SwapIn, MenuOut, MenuItem, MacroNutrition, FoodItem
from app.api.services import get_food_db, profile_in_to_user_profile, calculate_targets

router = APIRouter()

@router.get("/foods")
async def search_foods(q: Optional[str] = Query(None), limit: int = Query(20, le=100)):
    """Search foods in database"""
    food_db, food_map = get_food_db()
    
    results = []
    count = 0
    for food_id, food in food_map.items():
        if q and q.lower() not in food.get("food_name", "").lower():
            continue
        
        results.append(FoodItem(
            food_id=food_id,
            name=food.get("food_name", "Unknown"),
            meal_type=food.get("meal_type", "all"),
            macros_per_100g=MacroNutrition(
                calories=food.get("calories", 0),
                protein_g=food.get("protein_g", 0),
                carbs_g=food.get("carbs_g", 0),
                fat_g=food.get("fat_g", 0),
                fiber_g=food.get("fiber_g", 0),
                sodium_mg=food.get("sodium_mg", 0)
            )
        ))
        count += 1
        if count >= limit:
            break
    
    return {"foods": results, "count": len(results)}

@router.post("/menu/swap", response_model=MenuOut)
async def swap_menu_item(request: SwapIn):
    """Swap one menu item and re-optimize portions"""
    try:
        user_profile = profile_in_to_user_profile(request.profile)
        _, food_map = get_food_db()
        
        # Get targets
        targets_data = calculate_targets(user_profile)
        targets = targets_data["targets"]
        
        # Get meal order and pools
        meal_order = get_meal_order_slots(user_profile.meal_counts)
        pools = build_meal_pools(food_map, user_profile.meal_counts, user_profile)
        
        # Find slot index
        if request.slot not in meal_order:
            raise HTTPException(status_code=400, detail=f"Invalid slot: {request.slot}")
        
        idx = meal_order.index(request.slot)
        pool = pools[request.slot]
        
        # Get current meal items for this meal type (breakfast, lunch, dinner, snack)
        current_meal_type = request.slot.split("_")[0]
        current_meal_food_ids = [
            fid for i, fid in enumerate(request.food_ids)
            if meal_order[i].startswith(current_meal_type)
        ]
        
        # Choose new food
        if request.new_food_id:
            new_food_id = request.new_food_id
            if new_food_id not in pool:
                raise HTTPException(status_code=400, detail="Food not valid for this slot")
            if new_food_id in current_meal_food_ids:
                raise HTTPException(status_code=400, detail="Food already in this meal")
        else:
            # Auto-select different food from pool
            candidates = [fid for fid in pool 
                         if fid != request.food_ids[idx] 
                         and fid not in current_meal_food_ids]
            if not candidates:
                raise HTTPException(status_code=409, detail="No alternative foods available")
            new_food_id = candidates[0]
        
        # Build new food_ids list
        new_food_ids = list(request.food_ids)
        new_food_ids[idx] = new_food_id
        
        # Re-optimize portions using inner solver
        inner_obj = make_menu_objective(user_profile, new_food_ids, food_map, targets)
        inner_result = IDBO(n_agents=15, max_iter=25).optimize(
            inner_obj,
            dim=len(new_food_ids),
            lb=25.0,
            ub=350.0,
            seed=request.seed
        )
        
        # Decode and validate
        menu = decode_result(new_food_ids, inner_result.best_x, food_map, user_profile.meal_counts)
        violations = validate_menu(menu, user_profile, targets)
        
        # Round portions
        rounded_portions = round_portions(inner_result.best_x, step=5)
        menu_rounded = decode_result(new_food_ids, rounded_portions, food_map, user_profile.meal_counts)
        
        # Build response
        items = []
        for i, (food_id, meal_type) in enumerate(zip(new_food_ids, meal_order)):
            food = food_map[food_id]
            portion_round = int(rounded_portions[i])
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
                name=food.get("food_name", "Unknown"),
                slot=meal_type,
                meal_type=food.get("meal_type", "all"),
                portion_g=inner_result.best_x[i],
                portion_g_rounded=portion_round,
                macros=macros
            ))
        
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
        
        return MenuOut(
            items=items,
            totals=totals,
            targets=targets_out,
            fitness=-inner_result.best_fitness,  # Convert back to positive fitness
            violations=violations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error swapping menu item: {str(e)}")
