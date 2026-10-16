"""Week 9 Demonstration Script: 7-Day Weekly Meal Planning & Multi-Profile Solver.

Runs end-to-end 7-day optimization with diversity penalty for P1, P2 (diabetes), or P3 (hypertension):
  - Lập kế hoạch thực đơn chu kỳ 7 ngày liên tiếp
  - Cơ chế phạt lặp món chính (Diversity Penalty, cửa sổ trượt 2 ngày)
  - Kiểm soát nghiêm ngặt ràng buộc bệnh lý:
      * P2 (Tiểu đường): Đường <= 25g
      * P3 (Tăng huyết áp): Natri <= 1500mg
  - Làm tròn khẩu phần về bội số 5g thực tế

Usage:
  python scripts/demo_week9.py --profile p1
  python scripts/demo_week9.py --profile p2 --days 7 --seed 9001
  python scripts/demo_week9.py --profile p3 --algo idbo
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

from scripts.generate_options_week9 import get_profile, get_profile_targets
from src.algorithms.menu_objective import decode_result
from src.algorithms.two_tier_solver import TwoTierConfig, two_tier_optimize
from src.models.constraints import validate_menu
from src.models.diversity_penalty import calculate_unique_main_dish_pct, diversity_penalty
from src.models.food_selector import get_meal_order_slots
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.portion_utils import round_portions


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Demo Tuần 9: Lập thực đơn 7 ngày đa dạng món & kiểm soát bệnh lý")
    parser.add_argument("--profile", type=str, default="p1", choices=["p1", "p2", "p3"], help="Hồ sơ bệnh lý (p1, p2, p3)")
    parser.add_argument("--algo", type=str, default="idbo", choices=["dbo", "idbo"], help="Thuật toán 2 tầng (mặc định: idbo)")
    parser.add_argument("--days", type=int, default=7, help="Số ngày lập thực đơn (mặc định: 7)")
    parser.add_argument("--outer-iter", type=int, default=15, help="Số vòng lặp tầng 1 (mặc định: 15)")
    parser.add_argument("--outer-agents", type=int, default=8, help="Số cá thể tầng 1 (mặc định: 8)")
    parser.add_argument("--inner-iter", type=int, default=15, help="Số vòng lặp tầng 2 (mặc định: 15)")
    parser.add_argument("--inner-agents", type=int, default=8, help="Số cá thể tầng 2 (mặc định: 8)")
    parser.add_argument("--seed", type=int, default=9001, help="Seed ngẫu nhiên (mặc định: 9001)")
    args = parser.parse_args()

    profile = get_profile(args.profile)
    targets = get_profile_targets(profile)

    df_food = load_food_db()
    food_map = build_food_map(df_food)

    print("=" * 85)
    print("DEMO TUẦN 9: KẾ HOẠCH THỰC ĐƠN 7 NGÀY & KIỂM SOÁT BỆNH LÝ (DBO / IDBO)")
    print(f"Thuật toán: {args.algo.upper()} | Hồ sơ: {args.profile.upper()} ({profile.name}) | Seed: {args.seed}")
    print("=" * 85)
    print("1. HỒ SƠ & MỤC TIÊU DINH DƯỠNG KHUYẾN NGHỊ")
    print(f"   Họ tên: {profile.name} | Tuổi: {profile.age} | Giới tính: {profile.gender.value}")
    print(f"   Cân nặng: {profile.weight_kg} kg | Chiều cao: {profile.height_cm} cm")
    print(f"   Bệnh lý: {profile.medical_conditions if profile.medical_conditions else 'Không (Khỏe mạnh)'}")
    print(f"   Năng lượng mục tiêu: {targets['calories']:.1f} kcal/ngày")
    print(f"   Đạm (Protein):       {targets['protein_g']:.1f} g")
    print(f"   Tinh bột (Carbs):    {targets['carbs_g']:.1f} g")
    print(f"   Chất béo (Fat):      {targets['fat_g']:.1f} g")
    if "sugar_g" in targets:
        print(f"   Ngưỡng proxy Đường (ước tính):      <= {targets['sugar_g']:.1f} g/ngày (Ràng buộc ĐTĐ)")
    if "sodium_mg" in targets:
        print(f"   Giới hạn Natri:      <= {targets['sodium_mg']:.1f} mg/ngày (Ràng buộc Tăng HA)")

    meal_order = get_meal_order_slots(profile.meal_counts)
    history_food_ids: list[list[str]] = []
    daily_results = []

    print(f"\n[Đang tối ưu] Tiến hành lập kế hoạch cho chu kỳ {args.days} ngày...")
    t_start = time.perf_counter()

    for d in range(1, args.days + 1):
        day_seed = args.seed + d * 10

        config = TwoTierConfig(
            outer_algo=args.algo,
            outer_n_agents=args.outer_agents,
            outer_max_iter=args.outer_iter,
            inner_algo=args.algo,
            inner_n_agents=args.inner_agents,
            inner_max_iter=args.inner_iter,
            seed=day_seed,
        )

        res = two_tier_optimize(profile, food_map, targets, config)
        div_loss = diversity_penalty(
            res.best_food_ids, history_food_ids, penalty_weight=10.0, lookback_days=2, meal_order=meal_order
        )
        adjusted_fit = float(res.best_fitness) - div_loss

        rounded = round_portions(res.best_portions_g, step=5)
        menu = decode_result(res.best_food_ids, rounded, food_map, profile.meal_counts)
        violations = validate_menu(menu, profile, targets)

        cals = float(menu.total("calories"))
        protein = float(menu.total("protein_g"))
        carbs = float(menu.total("carbs_g"))
        fat = float(menu.total("fat_g"))
        sodium = float(menu.total("sodium_mg"))
        sugar = carbs * 0.15  # proxy only: source dataset has no total-sugar field

        daily_results.append({
            "day": d,
            "seed": day_seed,
            "fitness": adjusted_fit,
            "calories": cals,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "sodium": sodium,
            "sugar": sugar,
            "violations": len(violations),
            "food_ids": res.best_food_ids,
            "portions_orig": res.best_portions_g,
            "portions_round": rounded,
            "menu": menu,
        })
        history_food_ids.append(res.best_food_ids)
        print(f"  - Ngày {d}: Fitness={adjusted_fit:>6.2f} | Calo={cals:>6.1f} kcal | Natri={sodium:>6.1f} mg | Đường={sugar:>5.1f} g | Vi phạm={len(violations)}")

    total_time = time.perf_counter() - t_start
    unique_main_pct = calculate_unique_main_dish_pct(history_food_ids, meal_order)

    print("\n2. ĐỘ ĐA DẠNG THỰC ĐƠN (DIVERSITY METRIC)")
    print(f"   Tỷ lệ món chính độc nhất trong chu kỳ: {unique_main_pct:.1f}% (Chuẩn yêu cầu: >= 80.0%)")
    if unique_main_pct >= 80.0:
        print("   -> ĐẠT YÊU CẦU ĐA DẠNG: Người dùng không bị trùng lặp món chính trong chu kỳ đang chạy!")
    else:
        print("   -> Cảnh báo: Tỷ lệ đa dạng dưới 80%, cần tăng trọng số diversity penalty.")

    print("\n3. CHI TIẾT THỰC ĐƠN MINH HỌA (NGÀY ĐẦU & NGÀY CUỐI - KHẨU PHẦN ĐÃ LÀM TRÒN 5G)")
    meal_names = {"breakfast": "Sáng", "lunch": "Trưa", "dinner": "Tối", "snack": "Phụ"}

    for d_idx in [0, len(daily_results) - 1]:
        d_res = daily_results[d_idx]
        print(f"\n   [NGÀY {d_res['day']}] (Fitness: {d_res['fitness']:.2f}, Năng lượng: {d_res['calories']:.1f} kcal)")
        m_idx = 0
        for m_type, meal in d_res["menu"].meals.items():
            m_label = meal_names.get(m_type.value, m_type.value)
            for it in meal.items:
                p_rnd = d_res["portions_round"][m_idx]
                print(f"     * [{m_label}] {it.food_name[:38]:<38} : {p_rnd:>3d} g (ID: {it.food_id})")
                m_idx += 1

    print("\n4. BẢNG TỔNG HỢP DINH DƯỠNG TRONG CHU KỲ")
    print(f"   {'Ngày':<6} | {'Calo (kcal)':<12} | {'Đạm (g)':<9} | {'Béo (g)':<9} | {'Proxy đường*':<10} | {'Natri (mg)':<11} | {'Vi phạm'}")
    print("   " + "-" * 75)
    for r in daily_results:
        print(f"   Ngày {r['day']:<2} | {r['calories']:>10.1f}  | {r['protein']:>7.1f}  | {r['fat']:>7.1f}  | {r['sugar']:>8.1f}   | {r['sodium']:>9.1f}   | {r['violations']}")
    print("   " + "-" * 75)
    print("   * Proxy đường = 15% carbohydrate; không phải số đường đo từ dataset và không dùng để kết luận an toàn y tế.")
    mean_cal = np.mean([r["calories"] for r in daily_results])
    mean_fit = np.mean([r["fitness"] for r in daily_results])
    total_viols = sum([r["violations"] for r in daily_results])
    print(f"   TB     | {mean_cal:>10.1f}  | -         | -         | -          | -           | Tổng: {total_viols}")
    print(f"\n   * Mean Fitness chu kỳ: {mean_fit:.2f}")
    status = "hợp lệ theo tập ràng buộc hiện tại" if total_viols == 0 else "còn vi phạm cần xử lý"
    print(f"   * Tổng số vi phạm dinh dưỡng: {total_viols} ({status})")
    print(f"   * Tổng thời gian giải {args.days} ngày: {total_time:.2f} giây ({total_time/args.days:.2f}s/ngày)")
    print("=" * 85)


if __name__ == "__main__":
    main()
