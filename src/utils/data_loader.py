from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "merged_food_nutrition.csv"

NUTRIENT_KEYS = [
    "calories",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "sodium_mg",
    "calcium_mg",
    "iron_mg",
    "vitamin_c_mg",
]


def load_food_db(path: Path | str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["food_name"] = df["food_name"].fillna("")
    for key in NUTRIENT_KEYS:
        df[key] = df[key].fillna(0.0).astype(float)
    return df


def build_food_map(df: pd.DataFrame) -> dict[str, dict]:
    return df.set_index("food_id").to_dict("index")
