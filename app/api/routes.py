"""
API routes for menu generation and targets calculation
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import asyncio

from app.api.schemas import ProfileIn, TargetsOut, GenerateIn, MenuOut, MacroNutrition
from app.api.services import (
    get_profiles,
    profile_in_to_user_profile,
    calculate_targets,
    generate_menu
)

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "DBO Healthcare Menu API"}

@router.get("/profiles")
async def list_profiles():
    """Get preset profiles P1, P2, P3"""
    return {"profiles": get_profiles()}

@router.post("/targets", response_model=TargetsOut)
async def compute_targets(profile: ProfileIn):
    """Calculate BMR, TDEE and nutrition targets for a profile"""
    try:
        user_profile = profile_in_to_user_profile(profile)
        result = calculate_targets(user_profile)
        
        targets_macro = MacroNutrition(
            calories=result["targets"].get("calories", 0),
            protein_g=result["targets"].get("protein_g", 0),
            carbs_g=result["targets"].get("carbs_g", 0),
            fat_g=result["targets"].get("fat_g", 0),
            fiber_g=result["targets"].get("fiber_g", 0),
            sodium_mg=result["targets"].get("sodium_mg", 2300)
        )
        
        return TargetsOut(
            bmr=result["bmr"],
            tdee=result["tdee"],
            targets=targets_macro
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating targets: {str(e)}")

@router.post("/menu/generate", response_model=MenuOut)
async def create_menu(request: GenerateIn):
    """Generate a personalized menu using IDBO solver"""
    try:
        user_profile = profile_in_to_user_profile(request.profile)
        
        # Run solver in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            generate_menu,
            user_profile,
            request.seed,
            request.config
        )
        
        return MenuOut(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating menu: {str(e)}")
