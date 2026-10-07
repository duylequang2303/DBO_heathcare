"""Week 8 Demonstration Script: Mixed-Integer Two-Tier Optimization.

Runs end-to-end two-tier optimization on Profile P1:
  - Tầng 1 (Outer): IDBO/DBO chọn tổ hợp món tự do từ kho 15.929 món
  - Tầng 2 (Inner): IDBO/DBO tối ưu định lượng gram cho các món đã chọn
  - Làm tròn khẩu phần về bội số 5g thực tế

Usage:
  python scripts/demo_week8.py
  python scripts/demo_week8.py --outer-iter 10 --inner-iter 10 --seed 42
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.two_tier_solver import TwoTierConfig, two_tier_optimize
from src.algorithms.menu_objective import decode_result
from src.models.constraints import validate_menu
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import calc_bmr, calc_calorie_target, calc_tdee, daily_all_targets
from src.utils.portion_utils import round_portions


def get_profile_p1() -> UserProfile:
    """Evaluation Profile P1 (Duy)."""
    return UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        weight_kg=65.0,
        height_cm=170.0,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        diet_type=DietType.STANDARD,
        meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 2},
        allergies=[],
        dislikes=[],
        likes=[],
    )


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Demo Tuần 8: Tối ưu 2 tầng chọn món & định lượng")
    parser.add_argument("--outer-algo", type=str, default="idbo", choices=["dbo", "idbo"], help="Thuật toán tầng 1 (chọn món)")
    parser.add_argument("--inner-algo", type=str, default="idbo", choices=["dbo", "idbo"], help="Thuật toán tầng 2 (định lượng)")
    parser.add_argument("--outer-iter", type=int, default=20, help="Số vòng lặp tầng 1 (mặc định: 20)")
    parser.add_argument("--outer-agents", type=int, default=10, help="Số cá thể tầng 1 (mặc định: 10)")
    parser.add_argument("--inner-iter", type=int, default=25, help="Số vòng lặp tầng 2 (mặc định: 25)")
    parser.add_argument("--inner-agents", type=int, default=10, help="Số cá thể tầng 2 (mặc định: 10)")
    parser.add_argument("--seed", type=int, default=None, help="Ngẫu nhiên seed (mặc định: theo thời gian hiện tại)")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else int(time.time() * 1000) % 2147483647

    profile = get_profile_p1()
    bmr = calc_bmr(profile)
    tdee = calc_tdee(profile)
    target_cals = calc_calorie_target(profile)
    targets = daily_all_targets(profile)

    print("=" * 80)
    print("DEMO TUẦN 8: MIXED-INTEGER OPTIMIZATION (TỰ CHỌN MÓN 2 TẦNG)")
    print(f"Thuật toán: Outer={args.outer_algo.upper()} | Inner={args.inner_algo.upper()} | Seed={seed}")
    print("=" * 80)
    print("1. HỒ SƠ NGƯỜI DÙNG (PROFILE P1)")
    print(f"   Họ tên: {profile.name} | Tuổi: {profile.age} | Giới tính: {profile.gender.value}")
    print(f"   Chiều cao: {profile.height_cm} cm | Cân nặng: {profile.weight_kg} kg")
    print(f"   Mức vận động: {profile.activity_level.name} | Mục tiêu: {profile.goal.name}")
    print(f"   BMR (Mifflin-St Jeor): {bmr:.1f} kcal")
    print(f"   TDEE:                  {tdee:.1f} kcal")
    print(f"   Calo mục tiêu:         {target_cals:.1f} kcal/ngày")

    # Load database
    df = load_food_db()
    food_map = build_food_map(df)

    config = TwoTierConfig(
        outer_algo=args.outer_algo,
        outer_n_agents=args.outer_agents,
        outer_max_iter=args.outer_iter,
        inner_algo=args.inner_algo,
        inner_n_agents=args.inner_agents,
        inner_max_iter=args.inner_iter,
        seed=seed,
    )

    print(f"\n[Đang chạy] Tối ưu hóa 2 tầng (Outer {args.outer_iter} iters, Inner {args.inner_iter} iters)...")
    res = two_tier_optimize(profile, food_map, targets, config)

    # Decode menu & compute portions
    menu = decode_result(res.best_food_ids, res.best_portions_g, food_map, profile.meal_counts)
    rounded_portions = round_portions(res.best_portions_g, step=5)

    print("\n2. THỰC ĐƠN TỰ CHỌN TỪ KHO 15.929 MÓN & KHẨU PHẦN TỐI ƯU")
    meal_names = {"breakfast": "Bữa sáng", "lunch": "Bữa trưa", "dinner": "Bữa tối", "snack": "Bữa phụ"}
    idx = 0
    for meal_type_enum, meal in menu.meals.items():
        m_name = meal_names.get(meal_type_enum.value, meal_type_enum.value)
        for item in meal.items:
            portion_orig = res.best_portions_g[idx]
            portion_round = rounded_portions[idx]
            print(f"   - [{m_name}] {item.food_name[:42]:<42} : {portion_orig:>6.1f} g (thực tế: {portion_round:>3d} g, ID: {item.food_id})")
            idx += 1

    print(f"\n   * Mảng gram tối ưu (gốc): {np.round(res.best_portions_g, 1).tolist()}")
    print(f"   * Mảng gram thực tế (5g): {rounded_portions.tolist()}")

    print("\n3. HIỆU NĂNG TỐI ƯU 2 TẦNG")
    print(f"   Best Fitness:       {res.best_fitness:.4f} (thang [-100, 100])")
    print(f"   Đánh giá Outer:     {res.outer_evals} lần")
    print(f"   Tổng đánh giá Inner:{res.inner_evals_total} lần")
    print(f"   Thời gian thực thi: {res.runtime_s:.2f} giây")

    print("\n4. THÀNH PHẦN DINH DƯỠNG SO VỚI MỤC TIÊU")
    cals = menu.total("calories")
    print(f"   Năng lượng:   {cals:>7.1f} kcal / {targets['calories']:>7.1f} kcal (Lệch: {abs(cals - targets['calories']):.1f} kcal, {abs(cals - targets['calories'])/targets['calories']*100:.2f}%)")
    print(f"   Protein:      {menu.total('protein_g'):>7.1f} g    / {targets['protein_g']:>7.1f} g")
    print(f"   Carbohydrate: {menu.total('carbs_g'):>7.1f} g    / {targets['carbs_g']:>7.1f} g")
    print(f"   Chất béo:     {menu.total('fat_g'):>7.1f} g    / {targets['fat_g']:>7.1f} g")
    print(f"   Chất xơ:      {menu.total('fiber_g'):>7.1f} g    / {targets['fiber_g']:>7.1f} g")

    print("\n5. KIỂM TRA RÀNG BUỘC (VALIDATE_MENU)")
    violations = validate_menu(menu, profile, targets)
    print(f"   Số vi phạm: {len(violations)}")
    if violations:
        for v in violations:
            print(f"     * {v}")
    else:
        print("   -> Thực đơn hoàn toàn hợp lệ (0 vi phạm)!")

    print("================================================================================")


if __name__ == "__main__":
    main()
