from dataclasses import dataclass, field
from enum import Enum


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(Enum):
    SEDENTARY = 1.2
    LIGHT = 1.375
    MODERATE = 1.55
    ACTIVE = 1.725
    VERY_ACTIVE = 1.9


class Goal(Enum):
    LOSE_WEIGHT = "lose_weight"
    MAINTAIN = "maintain"
    GAIN_WEIGHT = "gain_weight"


@dataclass
class UserProfile:
    name: str
    age: int
    gender: Gender
    height_cm: float
    weight_kg: float
    activity_level: ActivityLevel
    goal: Goal = Goal.MAINTAIN
    allergies: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)
    meal_counts: dict[str, int] = field(default_factory=lambda: {
        "breakfast": 1,
        "lunch": 1,
        "dinner": 1,
        "snack": 1,
    })
