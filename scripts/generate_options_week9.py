"""Week 9 Options Generator: Multi-Option UX for Weekly Menu (Option A/B/C).

Generates 3 distinct 7-day meal plans for a user profile using seeds 9001, 9002, 9003.
Outputs a structured side-by-side comparison table showing:
- Daily meal selections (breakfast, lunch, dinner, snack)
- Fitness score per option
- Calorie deviation vs target
- Percentage of unique main dishes

Usage:
  python scripts/generate_options_week9.py --profile p1 --options 3 --days 7
  python scripts/generate_options_week9.py --smoke
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.menu_objective import decode_result
from src.algorithms.two_tier_solver import TwoTierConfig, TwoTierResult, two_tier_optimize
from src.models.constraints import validate_menu
from src.models.diversity_penalty import calculate_unique_main_dish_pct, diversity_penalty
from src.models.food_selector import get_meal_order_slots
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets
from src.utils.portion_utils import round_portions


def get_profile(name: str) -> UserProfile:
    """Return configured profile for p1, p2, or p3.

    Args:
        name: Profile key ('p1', 'p2', 'p3').

    Returns:
        UserProfile: Target profile.
    """
    key = name.lower()
    if key == "p2":
        return UserProfile(
            name="Lan",
            age=45,
            gender=Gender.FEMALE,
            weight_kg=62.0,
            height_cm=158.0,
            activity_level=ActivityLevel.LIGHT,
            goal=Goal.LOSE_WEIGHT,
            diet_type=DietType.STANDARD,
            meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
            medical_conditions=["diabetes"],
        )
    elif key == "p3":
        return UserProfile(
            name="Minh",
            age=55,
            gender=Gender.MALE,
            weight_kg=75.0,
            height_cm=168.0,
            activity_level=ActivityLevel.SEDENTARY,
            goal=Goal.MAINTAIN,
            diet_type=DietType.STANDARD,
            meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
            medical_conditions=["hypertension"],
        )
    else:  # p1 default
        return UserProfile(
            name="Duy",
            age=22,
            gender=Gender.MALE,
            weight_kg=65.0,
            height_cm=170.0,
            activity_level=ActivityLevel.MODERATE,
            goal=Goal.MAINTAIN,
            diet_type=DietType.STANDARD,
            meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
            medical_conditions=["healthy"],
        )


def get_profile_targets(profile: UserProfile) -> dict[str, float]:
    """Return nutrient targets tailored to condition constraints."""
    targets = daily_all_targets(profile)
    if "diabetes" in profile.medical_conditions:
        targets["sugar_g"] = 25.0
    if "hypertension" in profile.medical_conditions:
        targets["sodium_mg"] = 1500.0
    return targets


def plan_7days(
    profile: UserProfile,
    food_map: dict,
    targets: dict,
    base_seed: int,
    outer_iter: int = 15,
    inner_iter: int = 15,
    outer_agents: int = 8,
    inner_agents: int = 8,
    days: int = 7,
) -> Dict[str, object]:
    """Generate a cohesive 7-day meal plan with diversity enforcement.

    Args:
        profile: Target user profile.
        food_map: Food database dictionary.
        targets: Target nutrients.
        base_seed: Base seed for random generation.
        outer_iter: Outer loop iterations.
        inner_iter: Inner loop iterations.
        outer_agents: Outer loop agents.
        inner_agents: Inner loop agents.
        days: Number of days to plan (default: 7).

    Returns:
        Dict containing daily menus, metrics, fitness, and overall statistics.
    """
    daily_results = []
    history_food_ids: list[list[str]] = []
    total_fitness = 0.0
    total_cals = 0.0

    for day_idx in range(1, days + 1):
        day_seed = base_seed + day_idx * 17

        config = TwoTierConfig(
            outer_algo="idbo",
            outer_n_agents=outer_agents,
            outer_max_iter=outer_iter,
            inner_algo="idbo",
            inner_n_agents=inner_agents,
            inner_max_iter=inner_iter,
            seed=day_seed,
        )

        res = two_tier_optimize(profile, food_map, targets, config)
        menu = decode_result(res.best_food_ids, res.best_portions_g, food_map, profile.meal_counts)
        viols = validate_menu(menu, profile, targets)
        cals = menu.total("calories")

        div_pen = diversity_penalty(res.best_food_ids, history_food_ids, penalty_weight=10.0, lookback_days=2)
        effective_fitness = float(res.best_fitness) - div_pen

        history_food_ids.append(res.best_food_ids)
        total_fitness += effective_fitness
        total_cals += cals

        daily_results.append({
            "day": day_idx,
            "fitness": effective_fitness,
            "calories": cals,
            "violations": len(viols),
            "food_ids": res.best_food_ids,
            "portions_g": res.best_portions_g,
            "menu": menu,
        })

    target_cal = float(targets["calories"])
    mean_cal = total_cals / days
    cal_dev = mean_cal - target_cal
    diversity_pct = calculate_unique_main_dish_pct(history_food_ids)

    return {
        "mean_fitness": round(total_fitness / days, 2),
        "mean_calories": round(mean_cal, 1),
        "calorie_deviation": round(cal_dev, 1),
        "diversity_pct": round(diversity_pct, 1),
        "daily": daily_results,
    }


def main() -> None:
    """Main CLI execution for Option A/B/C generator."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Week 9: Multi-Option 7-Day Meal Plan Generator")
    parser.add_argument("--profile", type=str, default="p1", choices=["p1", "p2", "p3"], help="Profile choice")
    parser.add_argument("--options", type=int, default=3, help="Number of options (default: 3: A, B, C)")
    parser.add_argument("--days", type=int, default=7, help="Number of days per plan (default: 7)")
    parser.add_argument("--smoke", action="store_true", help="Fast smoke sanity check")
    parser.add_argument("--output-dir", type=str, default="experiments/week9", help="Output directory")

    args = parser.parse_args()

    if args.smoke:
        outer_iter, inner_iter = 3, 3
        outer_agents, inner_agents = 4, 4
        days = 2
        n_options = 2
    else:
        outer_iter, inner_iter = 12, 12
        outer_agents, inner_agents = 8, 8
        days = args.days
        n_options = args.options

    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    profile = get_profile(args.profile)
    targets = get_profile_targets(profile)
    df_food = load_food_db()
    food_map = build_food_map(df_food)

    seeds = [9001, 9002, 9003][:n_options]
    opt_labels = ["A", "B", "C"][:n_options]

    print("=" * 85)
    print(f"BỘ SINH ĐA PHƯƠNG ÁN THỰC ĐƠN 7 NGÀY (OPTION A/B/C) - PROFILE {args.profile.upper()}")
    print(f"Người dùng: {profile.name} | Tuổi: {profile.age} | Bệnh lý: {profile.medical_conditions}")
    print(f"Mục tiêu Calo: {targets['calories']:.1f} kcal/ngày | Số ngày: {days}")
    print("=" * 85)

    options_data = []
    for opt_idx, (lbl, seed) in enumerate(zip(opt_labels, seeds)):
        print(f"\n[Đang tính toán] Phương án {lbl} (Seed={seed})...", end=" ", flush=True)
        t0 = time.perf_counter()
        opt_res = plan_7days(
            profile=profile,
            food_map=food_map,
            targets=targets,
            base_seed=seed,
            outer_iter=outer_iter,
            inner_iter=inner_iter,
            outer_agents=outer_agents,
            inner_agents=inner_agents,
            days=days,
        )
        t_elap = time.perf_counter() - t0
        options_data.append((lbl, seed, opt_res))
        print(f"Xong trong {t_elap:.1f}s | Fitness: {opt_res['mean_fitness']} | Lệch Calo: {opt_res['calorie_deviation']:+.1f} kcal | Đa dạng: {opt_res['diversity_pct']}%")

    print("\n" + "=" * 85)
    print("BẢNG SO SÁNH 3 PHƯƠNG ÁN LỰA CHỌN (UX MULTI-OPTION COMPARISON)")
    print("=" * 85)
    header = f"{'CHỈ TIÊU / PHƯƠNG ÁN':<28}" + "".join([f" | PHƯƠNG ÁN {lbl} (seed {s})".center(25) for lbl, s in zip(opt_labels, seeds)])
    print(header)
    print("-" * 85)

    fit_cells = "".join([f"{str(res['mean_fitness']).center(25)}" for _, _, res in options_data])
    fit_row = f"{'Mean Fitness 7 ngày':<28}" + fit_cells
    print(fit_row)

    cal_cells = "".join([f"{(str(res['calorie_deviation']) + ' kcal').center(25)}" for _, _, res in options_data])
    cal_row = f"{'Sai lệch Calo (kcal/ngày)':<28}" + cal_cells
    print(cal_row)

    div_cells = "".join([f"{(str(res['diversity_pct']) + ' %').center(25)}" for _, _, res in options_data])
    div_row = f"{'% Món chính độc nhất (>=80%)':<28}" + div_cells
    print(div_row)

    print("-" * 85)
    print("MẪU THỰC ĐƠN NGÀY 1:")
    for lbl, _, res in options_data:
        day1 = res["daily"][0]
        foods_sample = [food_map.get(fid, {}).get("food_name", fid)[:20] for fid in day1["food_ids"][:3]]
        sample_str = ", ".join(foods_sample) + "..."
        print(f"  * Phương án {lbl}: {sample_str}")

    print("=" * 85)

    out_file = out_dir / f"options_comparison_{args.profile}.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"BẢNG SO SÁNH PHƯƠNG ÁN THỰC ĐƠN - PROFILE {args.profile.upper()}\n\n")
        f.write(header + "\n")
        f.write("-" * 85 + "\n")
        f.write(fit_row + "\n")
        f.write(cal_row + "\n")
        f.write(div_row + "\n")
    print(f"\n[SAVED] Báo cáo so sánh lưu tại: {out_file}")


if __name__ == "__main__":
    main()
