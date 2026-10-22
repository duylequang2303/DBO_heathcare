"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional

class ProfileIn(BaseModel):
    """User profile input schema"""
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=1, le=120)
    gender: Literal["male", "female"]
    height_cm: float = Field(..., gt=50, le=250)
    weight_kg: float = Field(..., gt=20, le=400)
    activity_level: Literal["SEDENTARY", "LIGHT", "MODERATE", "ACTIVE", "VERY_ACTIVE"]
    goal: Literal["LOSE_WEIGHT", "MAINTAIN", "GAIN_WEIGHT"]
    meal_counts: dict[str, int] = Field(default={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1})
    medical_conditions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)

class MacroNutrition(BaseModel):
    """Macro nutrition data"""
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float = 0.0

class TargetsOut(BaseModel):
    """Nutrition targets output"""
    bmr: float
    tdee: float
    targets: MacroNutrition

class MenuItem(BaseModel):
    """Single menu item"""
    food_id: str
    name: str
    slot: str
    meal_type: str
    portion_g: float
    portion_g_rounded: int
    macros: MacroNutrition

class MenuOut(BaseModel):
    """Complete menu output"""
    items: list[MenuItem]
    totals: MacroNutrition
    targets: MacroNutrition
    fitness: float
    violations: list[str]
    diversity_pct: Optional[float] = None

class GenerateIn(BaseModel):
    """Menu generation request"""
    profile: ProfileIn
    seed: int = Field(default=9001, ge=0)
    config: Literal["smoke", "web", "full"] = "web"

class SwapIn(BaseModel):
    """Menu swap request"""
    profile: ProfileIn
    food_ids: list[str]
    portions_g: list[float]
    slot: str
    new_food_id: Optional[str] = None
    seed: int = Field(default=9001, ge=0)

class FoodItem(BaseModel):
    """Food search result"""
    food_id: str
    name: str
    meal_type: str
    macros_per_100g: MacroNutrition
