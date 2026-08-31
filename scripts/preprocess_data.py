import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "merged_food_nutrition.csv"

NUTRIENT_KEYS = [
    "calories", "protein_g", "carbs_g", "fat_g", "fiber_g",
    "sodium_mg", "calcium_mg", "iron_mg", "vitamin_c_mg",
]

DROP_CATEGORIES = {
    "alcohol", "baby foods", "baking", "baking additives & extracts",
    "baking decorations & dessert toppings", "baking needs",
    "baking/cooking mixes/supplies", "beverages", "biscuits cracker",
    "biscuits kids", "biscuits/cookies", "biscuits/cookies (shelf stable)",
    "bread & muffin mixes", "breakfast drinks", "cake, cookie & cupcake mixes",
    "cakes, cupcakes, snack cakes", "candy", "cereal/muesli bars",
    "chewing gum & mints", "children's nutritional supplements",
    "chips, pretzels & snacks", "chips/crisps/snack mixes - natural/extruded (shelf stable)",
    "chocolate", "coffee",     "confectionery products", "cookies & biscuits", "crackers & biscotti",
    "croissants, sweet rolls, muffins & other pastries", "desserts & custard",
    "desserts/dessert sauces/toppings", "digestive & fiber supplements",
    "dips & salsa", "dressings/dips (shelf stable)",
    "drinks - juices, drinks and cordials", "drinks - powdered",
    "drinks - soft drinks", "energy, protein & muscle recovery drinks",
    "fats edible", "fats and oils", "flavored snack crackers",
    "food/beverage/tobacco variety packs",
    "fruit & vegetable juice, nectars & fruit drinks",
    "gelatin, gels, pectins & desserts", "granulated, brown & powdered sugar",
    "gravy mix", "green supplements", "health care", "herbal supplements",
    "herbs & spices", "herbs/spices/extracts", "honey",
    "ice cream & frozen yogurt", "iced & bottle tea", "jam, jelly & fruit spreads",
    "ketchup, mustard, bbq & cheese sauce", "liquid water enhancer",
    "lunch snacks & combinations", "meal replacement supplements",
    "mexican dinner mixes", "milk additives", "non alcoholic beverages  ready to drink",
    "non alcoholic beverages - not ready to drink",
    "non alcoholic beverages - ready to drink", "oils edible",
    "oriental, mexican & ethnic sauces", "other condiments",
    "other cooking sauces", "other drinks", "other frozen desserts",
    "other snacks", "pasta dinners", "pastry shells & fillings",
    "pickles, olives, peppers & relishes", "pickles/relishs/chutneys/olives",
    "pizza mixes & other dry dinners", "plant based water",
    "popcorn (shelf stable)", "popcorn, peanuts, seeds & related snacks",
    "powdered drinks", "prepared pasta & pizza sauces", "puddings & custards",
    "puddings and desserts", "salad dressing & mayonnaise",
    "sauces/spreads/dips/condiments",
    "seasoning mixes, salts, marinades & tenderizers", "snack foods - cereal snacks",
    "snack, energy & granola bars", "snacks", "soda",
    "soups, sauces, and gravies", "specialty formula supplements",
    "spices and herbs", "sport drinks", "spreads",
    "sugars/sugar substitute products", "sweet bakery products",
    "sweet spreads", "sweets", "syrups & molasses",
    "tea - bags, loose leaf, speciality", "tea bags",
    "vegetable & cooking oils", "water", "weight control", "wholesome snacks",
}

BREAKFAST_KEYWORDS = [
    "breakfast", "cereal", "bread", "buns", "bagel", "pancake",
    "waffle", "french toast", "muffin", "oatmeal", "toast",
]

SNACK_KEYWORDS = [
    "yogurt", "yoghurt", "fruit", "nut", "seed", "appetizer",
    "hors d'oeuvres",
]


def assign_meal_type(category) -> str:
    if pd.isna(category):
        return "all"
    c = str(category).lower()
    if any(k in c for k in BREAKFAST_KEYWORDS):
        return "breakfast"
    if any(k in c for k in SNACK_KEYWORDS):
        return "snack"
    return "all"


VN_MEAL_TYPE = {
    "Đồ ngọt (đường, bánh, mứt, kẹo)": "snack",
    "Nước giải khát, bia, rượu": "snack",
    "Quả chín": "snack",
    "Hạt, quả giàu đạm, béo và sản phẩm chế biến": "snack",
    "Sữa và sản phẩm chế biến": "breakfast",
}


def assign_vn_meal_type(group_name) -> str:
    if pd.isna(group_name):
        return "all"
    return VN_MEAL_TYPE.get(str(group_name), "all")


def clean_usda(usda: pd.DataFrame) -> pd.DataFrame:
    usda = usda.copy()
    bad_energy = usda["calories"] > 900
    usda.loc[bad_energy, "calories"] = usda.loc[bad_energy, "calories"] / 4.184
    usda = usda[usda["calories"] <= 1000]
    usda = usda[usda["calories"] > 0]
    usda["calories"] = usda["calories"].round(1)
    usda = usda[~usda["food_category"].fillna("").str.strip().str.lower().isin(DROP_CATEGORIES)]
    name_l = usda["food_name"].fillna("").str.lower()
    usda = usda[~name_l.str.contains("juice|nectar", regex=True)]
    out = pd.DataFrame({
        "food_id": "USDA_" + usda["fdc_id"].astype(str),
        "food_name": usda["food_name"],
        "category": usda["food_category"],
        "meal_type": usda["food_category"].map(assign_meal_type),
        "serving_size_g": 100.0,
        "calories": usda["calories"],
        "protein_g": usda["protein_g"],
        "carbs_g": usda["carbs_g"],
        "fat_g": usda["fat_g"],
        "fiber_g": usda["fiber_g"],
        "sodium_mg": usda["sodium_mg"],
        "calcium_mg": usda["calcium_mg"],
        "iron_mg": usda["iron_mg"],
        "vitamin_c_mg": usda["vitamin_c_mg"],
        "source": "usda",
        "name_en": usda["food_name"],
    })
    return out


def clean_vn(vn: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "food_id": "VN_" + vn["food_code"].astype(str),
        "food_name": vn["name_vi"],
        "category": vn["group_name"],
        "meal_type": vn["group_name"].map(assign_vn_meal_type),
        "serving_size_g": 100.0,
        "calories": vn["energy_kcal"],
        "protein_g": vn["protein_g"],
        "carbs_g": vn["carb_g"],
        "fat_g": vn["fat_g"],
        "fiber_g": vn["fiber_g"],
        "sodium_mg": vn["sodium_mg"],
        "calcium_mg": vn["calcium_mg"],
        "iron_mg": vn["iron_mg"],
        "vitamin_c_mg": vn["vitc_mg"],
        "source": "vietnamese",
        "name_en": vn["name_en"],
    })
    return out


def dedup_best(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    completeness = df[keys].notna().sum(axis=1)
    df = df.copy()
    df["_quality"] = completeness
    df = df.sort_values(["_quality", "food_id"])
    df = df.drop_duplicates(subset=["food_name"], keep="last")
    return df.drop(columns="_quality").reset_index(drop=True)


def main() -> None:
    usda = pd.read_csv(RAW_DIR / "comprehensive_foods_usda.csv")
    vn = pd.read_csv(RAW_DIR / "vietnamese_food_composition.csv", encoding="utf-8-sig")

    usda_out = clean_usda(usda)
    vn_out = clean_vn(vn)

    merged = pd.concat([usda_out, vn_out], ignore_index=True)
    merged = dedup_best(merged, NUTRIENT_KEYS)

    merged.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"USDA rows: raw={len(usda)} cleaned={len(usda_out)}")
    print(f"VN rows: {len(vn_out)}")
    print(f"After dedup: {len(merged)}")
    print(f"meal_type distribution:\n{merged['meal_type'].value_counts().to_string()}")
    print(f"source distribution:\n{merged['source'].value_counts().to_string()}")
    print(f"columns: {list(merged.columns)}")
    print(f"dup names remaining: {merged['food_name'].duplicated().sum()}")
    print(f"missing rate:\n{merged[NUTRIENT_KEYS].isna().mean().round(3).to_string()}")


if __name__ == "__main__":
    main()
