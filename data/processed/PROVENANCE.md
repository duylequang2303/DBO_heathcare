# Data Provenance — data/processed/

## Lineage

- **Raw inputs:** `data/raw/vietnamese_food_composition.csv` (526 rows) + USDA food nutrition dataset (15,403 rows). Total 15,929 rows.
- **Cleaning script:** `scripts/clean_dataset.py`
- **Cleaning report:** `data/processed/cleaning_report.md`
- **Output:** `data/processed/cleaned_food_nutrition.csv` (13,709 rows after removing 2,220 rows / 13.9%).

## Cleaning summary

Filters applied (see `cleaning_report.md` for full detail):

1. Sodium `> 3000 mg/100g` (physical ceiling + unit-error removal)
2. Calories `> 900 kcal` or `< 0` per 100g
3. Macro conservation violation: individual macro `> 100g` or sum(protein+carbs+fat) `> 105g/100g`
4. Protein, carbs, fat all NaN
5. "American Indian/Alaska Native Foods & Gia vị" category removed
6. Raw/unprepared meat, poultry, game, seafood, organs removed
7. Industrial flour, starch, baking powder, tahini, drink mix removed
8. Condiments: salt, soy sauce, bouillon, broth base removed

## Column provenance

All nutrient values are per 100g. Units:
- calories: kcal/100g
- protein_g, carbs_g, fat_g, fiber_g: g/100g
- sodium_mg, calcium_mg, iron_mg, vitamin_c_mg: mg/100g

## Known limitations (§4.2, §4.5)

- **No total sugar column:** The dataset does not contain a measured `total_sugar` field. No sugar proxy (`carbs * 0.15`) is presented as measured data. Any sugar estimate must be explicitly labeled `sugar_g_estimated` / `sugar_proxy_g` with `sugar_is_estimated = True`.
- **Sodium only:** Sodium is the only condition-specific nutrient enforced (hypertension 1500 mg, general 2300 mg CDRR, ceiling 3000 mg). No diabetes/sugar safety claim is made from carbohydrate-derived estimates.
- **Raw ingredients excluded:** Raw/unprepared items and condiments are removed from the candidate pool. They are not user-facing menu items.

## Version

`1.0.0` — generated 2026-10-25.
