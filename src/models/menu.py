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
    meal_type: str = ""

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
        return [float(item.portion_g) for item in self.all_items()]

    def food_ids(self) -> list[str]:
        return [item.food_id for item in self.all_items()]

    @classmethod
    def decode(
        cls,
        food_ids: list[str],
        portions_g: list[float],
        food_map: dict,
        meal_counts: dict[str, int] | None = None,
    ) -> "Menu":
        if len(food_ids) != len(portions_g):
            raise ValueError("food_ids and portions_g must have the same length")
        meal_order = list(MealType)
        if meal_counts is None:
            n = len(food_ids)
            base, extra = divmod(n, len(meal_order))
            counts = [base + (1 if i < extra else 0) for i in range(len(meal_order))]
        else:
            counts = [meal_counts.get(meal_type.value, 0) for meal_type in meal_order]
            if sum(counts) != len(food_ids):
                raise ValueError("sum(meal_counts) must equal len(food_ids)")
        menu = cls()
        offset = 0
        for meal_type, count in zip(meal_order, counts):
            meal = Meal(meal_type)
            for fid, portion in zip(food_ids[offset:offset + count], portions_g[offset:offset + count]):
                row = food_map[fid]
                meal.add_item(_item_from_row(fid, portion, row))
            menu.meals[meal_type] = meal
            offset += count
        return menu

    def __repr__(self) -> str:
        parts = []
        for meal_type, meal in self.meals.items():
            names = [f"{i.food_name}({i.portion_g:.0f}g)" for i in meal.items]
            parts.append(f"{meal_type.value}: {', '.join(names) or '-'}")
        return "\n".join(parts)


def _item_from_row(food_id: str, portion_g: float, row: dict) -> MenuItem:
    return MenuItem(
        food_id=food_id,
        food_name=row["food_name"],
        portion_g=portion_g,
        calories=_num(row.get("calories")),
        protein_g=_num(row.get("protein_g")),
        carbs_g=_num(row.get("carbs_g")),
        fat_g=_num(row.get("fat_g")),
        fiber_g=_num(row.get("fiber_g")),
        sodium_mg=_num(row.get("sodium_mg")),
        calcium_mg=_num(row.get("calcium_mg")),
        iron_mg=_num(row.get("iron_mg")),
        vitamin_c_mg=_num(row.get("vitamin_c_mg")),
        meal_type=_meal_type_str(row.get("meal_type")),
    )


def _meal_type_str(value) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if text in ("", "nan", "none"):
        return ""
    return text


def _num(value) -> float:
    if value is None:
        return 0.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number != number:
        return 0.0
    return number
