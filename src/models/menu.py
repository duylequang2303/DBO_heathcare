from dataclasses import dataclass
from enum import Enum


class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


@dataclass
class MenuItem:
    food_id: str
    food_name: str
    portion_g: float
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0
    sodium_mg: float = 0.0
    calcium_mg: float = 0.0
    iron_mg: float = 0.0
    vitamin_c_mg: float = 0.0

    def nutrient(self, key: str) -> float:
        per_100g = getattr(self, key)
        return per_100g * self.portion_g / 100.0


class Meal:
    def __init__(self, meal_type: MealType, items: list[MenuItem] | None = None):
        self.meal_type = meal_type
        self.items: list[MenuItem] = items or []

    def total(self, key: str) -> float:
        return sum(item.nutrient(key) for item in self.items)

    def add_item(self, item: MenuItem) -> None:
        self.items.append(item)


class Menu:
    def __init__(self, meals: dict[MealType, Meal] | None = None):
        self.meals: dict[MealType, Meal] = meals or {
            meal_type: Meal(meal_type) for meal_type in MealType
        }

    def total(self, key: str) -> float:
        return sum(meal.total(key) for meal in self.meals.values())

    def all_items(self) -> list[MenuItem]:
        return [item for meal in self.meals.values() for item in meal.items]

    def encode(self) -> list[float]:
        flat: list[float] = []
        for item in self.all_items():
            flat.append(float(item.portion_g))
        return flat

    @classmethod
    def decode(cls, food_ids: list[str], portions_g: list[float], food_map: dict) -> "Menu":
        menu = cls()
        chunks = [food_ids[i::4] for i in range(4)]
        pchunks = [portions_g[i::4] for i in range(4)]
        for idx, meal_type in enumerate(MealType):
            meal = Meal(meal_type)
            for fid, portion in zip(chunks[idx], pchunks[idx]):
                row = food_map[fid]
                meal.add_item(MenuItem(
                    food_id=fid,
                    food_name=row["food_name"],
                    portion_g=portion,
                    calories=row["calories"],
                    protein_g=row["protein_g"],
                    carbs_g=row["carbs_g"],
                    fat_g=row["fat_g"],
                    fiber_g=row["fiber_g"],
                    sodium_mg=row["sodium_mg"],
                    calcium_mg=row["calcium_mg"],
                    iron_mg=row["iron_mg"],
                    vitamin_c_mg=row["vitamin_c_mg"],
                ))
            menu.meals[meal_type] = meal
        return menu

    def __repr__(self) -> str:
        parts = []
        for meal_type, meal in self.meals.items():
            names = [f"{i.food_name}({i.portion_g:.0f}g)" for i in meal.items]
            parts.append(f"{meal_type.value}: {', '.join(names) or '-'}")
        return "\n".join(parts)
