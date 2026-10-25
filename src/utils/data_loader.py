from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
CLEANED_DATA_PATH = PROCESSED_DIR / "cleaned_food_nutrition.csv"
LEGACY_DATA_PATH = PROCESSED_DIR / "merged_food_nutrition.csv"

# Legacy path kept as default to ensure backward compatibility with historical tests (len >= 15000)
DATA_PATH = LEGACY_DATA_PATH

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
