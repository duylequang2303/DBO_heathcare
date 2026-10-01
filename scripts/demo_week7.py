"""Week 7 Demonstration Script.

Runs a single menu optimization using DBO or IDBO on Profile P1, and prints
a detailed Vietnamese summary report:
  1. Profile P1 + BMR / TDEE / Target Calories
  2. Food list with meal assignments and optimized gram portions
  3. Best original fitness, evaluation count, runtime
  4. Total nutrients (calories, protein, carbs, fat, fiber) vs target
  5. Menu validation and constraint violations (if any)
  6. 5 history checkpoints across iterations
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

from src.algorithms.dbo import DBO
from src.algorithms.idbo import IDBO
from src.algorithms.menu_objective import decode_result, make_menu_objective
from src.models.constraints import validate_menu
from src.models.food_sampler import sample_food_ids
from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import calc_bmr, calc_calorie_target, calc_tdee, daily_all_targets


def main():
    """Run a single demo menu optimization on Profile P1 using DBO or IDBO."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Demo Tuần 7: IDBO/DBO Tối ưu thực đơn")
    parser.add_argument("--algo", type=str, default="idbo", choices=["dbo", "idbo"], help="Thuật toán (dbo/idbo)")
    parser.add_argument("--max-iter", type=int, default=50, help="Số vòng lặp tối đa")
    parser.add_argument("--n-agents", type=int, default=30, help="Số lượng cá thể")
    parser.add_argument("--seed", type=int, default=42, help="Seed thuật toán")
    parser.add_argument("--seed-sampler", type=int, default=7000, help="Seed chọn món")
    args = parser.parse_args()

    # 1. Profile P1
    profile = UserProfile(
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
    bmr = calc_bmr(profile)
    tdee = calc_tdee(profile)
    target_cals = calc_calorie_target(profile)
    targets = daily_all_targets(profile)

    print("================================================================================")
    print("DEMO TUẦN 7: TỐI ƯU HÓA KHẨU PHẦN THỰC ĐƠN BẰNG " + args.algo.upper())
    print("================================================================================")
    print("1. HỒ SƠ NGƯỜI DÙNG (PROFILE P1)")
    print(f"   Họ tên: {profile.name} | Tuổi: {profile.age} | Giới tính: {profile.gender.value}")
    print(f"   Chiều cao: {profile.height_cm} cm | Cân nặng: {profile.weight_kg} kg")
    print(f"   Mức vận động: {profile.activity_level.name} | Mục tiêu: {profile.goal.name}")
    print(f"   BMR (Mifflin-St Jeor): {bmr:.1f} kcal")
    print(f"   TDEE:                  {tdee:.1f} kcal")
    print(f"   Calo mục tiêu:         {target_cals:.1f} kcal/ngày")

    # 2. Food sampling
    df = load_food_db()
    food_map = build_food_map(df)
    rng_sampler = np.random.default_rng(args.seed_sampler)
    food_ids = sample_food_ids(food_map, profile.meal_counts, profile, rng_sampler)

    # 3. Optimize
    obj = make_menu_objective(profile, food_ids, food_map, targets)
    t0 = time.perf_counter()
    if args.algo == "dbo":
        optimizer = DBO(n_agents=args.n_agents, max_iter=args.max_iter)
    else:
        optimizer = IDBO(n_agents=args.n_agents, max_iter=args.max_iter)

    res = optimizer.optimize(obj, dim=len(food_ids), lb=25.0, ub=350.0, seed=args.seed)
    runtime_s = time.perf_counter() - t0
    best_fitness = -float(res.best_fitness)

    menu = decode_result(food_ids, res.best_x, food_map, profile.meal_counts)

    print("\n2. DANH SÁCH MÓN ĂN & KHẨU PHẦN TỐI ƯU")
    meal_names = {"breakfast": "Bữa sáng", "lunch": "Bữa trưa", "dinner": "Bữa tối", "snack": "Bữa phụ"}
    idx = 0
    for meal_type_enum, meal in menu.meals.items():
        m_name = meal_names.get(meal_type_enum.value, meal_type_enum.value)
        for item in meal.items:
            portion = res.best_x[idx]
            print(f"   - [{m_name}] {item.food_name[:45]:<45} : {portion:>6.1f} g  (ID: {item.food_id})")
            idx += 1

    print("\n3. HIỆU NĂNG TỐI ƯU")
    print(f"   Best Fitness gốc:   {best_fitness:.4f} (thang [-100, 100])")
    print(f"   Số lần đánh giá:    {res.n_evaluations}")
    print(f"   Thời gian thực thi: {runtime_s:.3f} giây")

    print("\n4. THÀNH PHẦN DINH DƯỠNG SO VỚI MỤC TIÊU")
    print(f"   Năng lượng:   {menu.total('calories'):>7.1f} kcal / {targets['calories']:>7.1f} kcal (Lệch: {abs(menu.total('calories')-targets['calories']):.1f} kcal)")
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

    print("\n6. 5 MỐC LỊCH SỬ HỘI TỤ (FITNESS GỐC)")
    max_it = args.max_iter
    checkpoints = sorted(list({0, max_it // 4, max_it // 2, (3 * max_it) // 4, max_it}))
    for cp in checkpoints:
        if cp < len(res.history):
            fit_cp = -float(res.history[cp])
            print(f"   - Iteration {cp:3d}: Fitness = {fit_cp:.4f}")
    print("================================================================================")


if __name__ == "__main__":
    main()
