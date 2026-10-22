"""Audit generated menus for obvious user-facing realism risks.

This script is diagnostic only. It does not change the dataset, solver,
objective, candidate pool, or generated menus.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.schemas import ProfileIn
from app.api.services import generate_menu, profile_in_to_user_profile

RULES = {
    "oil_or_shortening": re.compile(r"\b(oil|shortening|lard)\b", re.I),
    "powder_or_supplement": re.compile(r"\b(powder|supplement|protein mix)\b", re.I),
    "sauce_or_seasoning": re.compile(r"\b(sauce|dressing|seasoning|condiment)\b", re.I),
    "ingredient_or_component": re.compile(r"\b(crust|flour|starch|baking soda|baking powder|blend)\b", re.I),
}

PROFILES = [
    dict(name="Duy", age=22, gender="male", height_cm=170, weight_kg=65, activity_level="MODERATE", goal="MAINTAIN"),
    dict(name="Lan", age=35, gender="female", height_cm=158, weight_kg=55, activity_level="LIGHT", goal="LOSE_WEIGHT"),
    dict(name="Minh", age=28, gender="male", height_cm=175, weight_kg=75, activity_level="ACTIVE", goal="GAIN_WEIGHT"),
]


def reasons_for(name: str, portion_g: float) -> list[str]:
    reasons = [label for label, pattern in RULES.items() if pattern.search(name or "")]
    if portion_g < 25 or portion_g > 350:
        reasons.append("portion_outside_system_range")
    return reasons


def make_profile(values: dict[str, Any]) -> ProfileIn:
    return ProfileIn(
        **values,
        meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
        medical_conditions=[], allergies=[], dislikes=[],
    )


def run_audit(seeds: list[int], config: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pnum, values in enumerate(PROFILES, start=1):
        profile = profile_in_to_user_profile(make_profile(values))
        for seed in seeds:
            result = generate_menu(profile, seed, config)
            for item in result["items"]:
                name = item.name
                reasons = reasons_for(name, item.portion_g_rounded)
                rows.append({
                    "profile": f"P{pnum}", "seed": seed, "fitness": result["fitness"],
                    "slot": item.slot, "food_id": item.food_id, "food_name": name,
                    "meal_type": item.meal_type, "portion_g": item.portion_g_rounded,
                    "suspect": bool(reasons), "reasons": ";".join(reasons),
                })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[9001, 9002, 9003, 9004, 9005])
    parser.add_argument("--config", choices=["smoke", "web", "full"], default="smoke")
    parser.add_argument("--output", type=Path, default=Path("menu_realism_audit.csv"))
    args = parser.parse_args()
    rows = run_audit(args.seeds, args.config)
    with args.output.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    menu_keys = {(r["profile"], r["seed"]) for r in rows}
    bad_menu_keys = {(r["profile"], r["seed"]) for r in rows if r["suspect"]}
    reason_counts = Counter(x for r in rows for x in str(r["reasons"]).split(";") if x)
    print(f"Audited menus: {len(menu_keys)}")
    print(f"Audited items: {len(rows)}")
    print(f"Menus with obvious suspect item: {len(bad_menu_keys)}/{len(menu_keys)}")
    print(f"Suspect items: {sum(bool(r['suspect']) for r in rows)}/{len(rows)}")
    print(f"Reasons: {dict(reason_counts)}")
    print(f"CSV: {args.output}")

if __name__ == "__main__":
    main()
