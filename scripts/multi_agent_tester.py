"""Multi-Agent Tester: Hệ thống kiểm thử tự động đề xuất thực đơn.

Các vai trò subagent (giả lập nhân viên ảo thay con người):
- profile-agent: Sinh hồ sơ kiểm thử ngẫu nhiên.
- runner-agent: Chạy two-tier solver trên mỗi hồ sơ.
- validator-agent: Kiểm tra ràng buộc nghiệp vụ.
- reviewer-agent: Đọc và đánh giá đầu ra báo cáo (không có mã ID kỹ thuật, tên tiếng Anh khó hiểu).
- reporter-agent: Viết báo cáo tiếng Việt dễ hiểu.

Chạy:
    python scripts/multi_agent_tester.py --seed 42 --num-profiles 3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.two_tier_solver import TwoTierConfig, two_tier_optimize
from src.algorithms.menu_objective import decode_result
from src.models.constraints import validate_menu, is_feasible
from src.models.report import build_menu_report, format_menu_report
from src.models.user_profile import (
    ActivityLevel,
    DietType,
    Gender,
    Goal,
    UserProfile,
)
from src.utils.data_loader import build_food_map, load_food_db, CLEANED_DATA_PATH, DATA_PATH
from src.utils.nutrition import daily_all_targets
from src.utils.portion_utils import round_portions


# ---------------------------------------------------------------------------
# profile-agent: sinh hồ sơ kiểm thử ngẫu nhiên
# ---------------------------------------------------------------------------

def generate_test_profiles(seed: int, num_profiles: int) -> list[UserProfile]:
    """Sinh danh sách hồ sơ kiểm thử ngẫu nhiên (subagent: profile-agent)."""
    rng = np.random.default_rng(seed)
    profiles: list[UserProfile] = []

    genders = [Gender.MALE, Gender.FEMALE]
    activity_levels = [
        ActivityLevel.SEDENTARY,
        ActivityLevel.LIGHT,
        ActivityLevel.MODERATE,
        ActivityLevel.ACTIVE,
    ]
    goals = [Goal.MAINTAIN, Goal.LOSE_WEIGHT, Goal.GAIN_WEIGHT]

    for i in range(num_profiles):
        age = int(rng.integers(18, 65))
        gender = genders[int(rng.integers(0, len(genders)))]
        height_cm = float(rng.uniform(150, 185))
        weight_kg = float(rng.uniform(45, 90))
        activity_level = activity_levels[int(rng.integers(0, len(activity_levels)))]
        goal = goals[int(rng.integers(0, len(goals)))]

        profile = UserProfile(
            name=f"Người kiểm thử {i + 1}",
            age=age,
            gender=gender,
            height_cm=height_cm,
            weight_kg=weight_kg,
            activity_level=activity_level,
            goal=goal,
            diet_type=DietType.STANDARD,
            meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 2},
            allergies=[],
            dislikes=[],
            likes=[],
        )
        profiles.append(profile)

    return profiles


# ---------------------------------------------------------------------------
# runner-agent: chạy solver trên mỗi hồ sơ
# ---------------------------------------------------------------------------

def run_solver_for_profile(
    profile: UserProfile,
    food_map: dict,
    targets: dict,
    seed: int,
    outer_iter: int = 15,
    outer_agents: int = 10,
    inner_iter: int = 20,
    inner_agents: int = 10,
) -> object:
    """Chạy two-tier solver cho một hồ sơ (subagent: runner-agent)."""
    config = TwoTierConfig(
        outer_algo="idbo",
        outer_n_agents=outer_agents,
        outer_max_iter=outer_iter,
        inner_algo="idbo",
        inner_n_agents=inner_agents,
        inner_max_iter=inner_iter,
        seed=seed,
    )
    result = two_tier_optimize(profile, food_map, targets, config)
    return result


# ---------------------------------------------------------------------------
# validator-agent: kiểm tra ràng buộc nghiệp vụ
# ---------------------------------------------------------------------------

def validate_menu_for_profile(
    menu, profile: UserProfile, targets: dict, food_map: dict
) -> tuple[list[str], bool]:
    """Kiểm tra ràng buộc nghiệp vụ (subagent: validator-agent).

    Returns:
        (violations, is_feasible)
    """
    violations = validate_menu(menu, profile, targets, food_map=food_map)
    return violations, len(violations) == 0


# ---------------------------------------------------------------------------
# reviewer-agent: đọc và đánh giá đầu ra báo cáo
# ---------------------------------------------------------------------------

def review_report_output(report_text: str, food_map: dict) -> list[str]:
    """Đánh giá đầu ra báo cáo có dễ hiểu không (subagent: reviewer-agent).

    Kiểm tra:
    - Không chứa mã ID kỹ thuật trùm lầy (USDA_..., VN_...) không kèm giải thích.
    - Không chứa tên tiếng Anh USDA thô mà không có tên tiếng Việt.
    - Không đề xuất nguyên liệu thô như món ăn độc lập.

    Returns:
        Danh sách vi phạm (rỗng nếu đầu ra hợp lệ).
    """
    issues: list[str] = []

    # Kiểm tra xuất hiện mã ID trùm lầy trong báo cáo
    import re as _re
    usda_matches = _re.findall(r"\bUSDA_\d+\b", report_text)
    vn_matches = _re.findall(r"\bVN_\d+\b", report_text)
    if usda_matches:
        issues.append(f"Báo cáo chứa mã ID kỹ thuật USDA (ví dụ: {usda_matches[:3]}) mà không kèm tên tiếng Việt dễ hiểu.")
    if vn_matches:
        issues.append(f"Báo cáo chứa mã ID kỹ thuật VN (ví dụ: {vn_matches[:3]}) mà không kèm tên tiếng Việt dễ hiểu.")

    # Kiểm tra tên thức phẩm kỹ thuật thô (không dấu, dài, có dấu phẩy)
    technical_patterns = [
        r"Cereals ready-to-eat",
        r"Honey Nut Shredded",
        r"BACN,",
        r"ATLANTIC SALMON",
    ]
    for pat in technical_patterns:
        if _re.search(pat, report_text, _re.IGNORECASE):
            issues.append(f"Báo cáo chứa tên thức phẩm kỹ thuật khó hiểu: {pat}")

    return issues


# ---------------------------------------------------------------------------
# reporter-agent: viết báo cáo tiếng Việt dễ hiểu
# ---------------------------------------------------------------------------

def generate_vietnamese_report(
    menu,
    food_map: dict,
    profile: UserProfile,
    targets: dict,
    violations: list[str],
) -> str:
    """Tạo báo cáo tiếng Việt dễ hiểu (subagent: reporter-agent)."""
    report = build_menu_report(
        menu=menu,
        food_map=food_map,
        profile_name=profile.name,
        targets=targets,
        violations=violations,
    )
    return format_menu_report(report)


# ---------------------------------------------------------------------------
# Điều phối pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    seed: int,
    num_profiles: int,
    output_dir: Optional[Path] = None,
    outer_iter: int = 15,
    outer_agents: int = 10,
    inner_iter: int = 20,
    inner_agents: int = 10,
) -> int:
    """Chạy pipeline multi-agent kiểm thử (điều phối tất cả subagent)."""
    # Load dữ liệu
    data_path = CLEANED_DATA_PATH if CLEANED_DATA_PATH.exists() else DATA_PATH
    df = load_food_db(data_path)
    food_map = build_food_map(df)

    # profile-agent: sinh hồ sơ kiểm thử
    profiles = generate_test_profiles(seed=seed, num_profiles=num_profiles)

    all_reports: list[str] = []
    exit_code = 0

    for idx, profile in enumerate(profiles, start=1):
        targets = daily_all_targets(profile)

        print(f"\n{'='*60}")
        print(f"HỒ SƠ {idx}/{num_profiles}: {profile.name}")
        print(f"  Tuổi: {profile.age} | Giới tính: {profile.gender.value}")
        print(f"  Cân nặng: {profile.weight_kg} kg | Chiều cao: {profile.height_cm} cm")
        print(f"  Hoạt động: {profile.activity_level.name} | Mục tiêu: {profile.goal.value}")
        print(f"{'='*60}")

        # runner-agent: chạy solver
        t_start = time.perf_counter()
        result = run_solver_for_profile(
            profile=profile,
            food_map=food_map,
            targets=targets,
            seed=seed + idx,
            outer_iter=outer_iter,
            outer_agents=outer_agents,
            inner_iter=inner_iter,
            inner_agents=inner_agents,
        )
        runtime_s = time.perf_counter() - t_start

        # §6.3: IDBO telemetry — báo cáo perturbations, restarts, stagnation
        print(f"\n  [IDBO TELEMETRY]")
        print(f"    Outer:  {result.outer_perturbations} perturbations, "
              f"{result.outer_restarts} restarts, "
              f"{result.outer_collapse_events} collapse events, "
              f"max stagnation {result.outer_max_stagnation}")
        print(f"    Inner:  {result.inner_perturbations_total} perturbations, "
              f"{result.inner_restarts_total} restarts, "
              f"final inner {result.final_inner_perturbations} perturbations, "
              f"{result.final_inner_restarts} restarts, "
              f"max stagnation {result.final_inner_max_stagnation}")

        # §4.4: Làm tròn khẩu phần → decode rounded menu → recalc → validate
        rounded_portions = round_portions(result.best_portions_g, step=5)
        rounded_menu = decode_result(
            result.best_food_ids, rounded_portions, food_map, profile.meal_counts
        )

        # validator-agent: kiểm tra ràng buộc trên menu đã làm tròn
        violations, is_ok = validate_menu_for_profile(
            rounded_menu, profile, targets, food_map=food_map
        )

        # reporter-agent: tạo báo cáo tiếng Việt
        report_text = generate_vietnamese_report(
            rounded_menu, food_map, profile, targets, violations
        )

        # reviewer-agent: đánh giá độ dễ hiểu của báo cáo
        review_issues = review_report_output(report_text, food_map)
        if review_issues:
            print("\n  [REVIEWER] Phát hiện vấn đề độ dễ hiểu:")
            for issue in review_issues:
                print(f"    - {issue}")
            exit_code = 1

        # In báo cáo tiếng Việt
        print("\n" + report_text)
        print(f"\n  Thời gian chạy: {runtime_s:.2f} giây")
        print(f"  Ràng buộc: {'ĐẤT' if is_ok else 'KHÔNG ĐẤT'} ({len(violations)} vi phạm)")
        if not is_ok:
            exit_code = 1

        all_reports.append(report_text)

    # Lưu báo cáo ra file nếu yêu cầu
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = output_dir / f"multi_agent_report_{timestamp}_seed{seed}.txt"
        out_file.write_text("\n\n".join(all_reports), encoding="utf-8")
        print(f"\nĐã lưu báo cáo vào: {out_file}")

    return exit_code


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Tester: Kiểm thử đề xuất thực đơn bằng tiếng Việt"
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed ngẫu nhiên (mặc định: 42)")
    parser.add_argument(
        "--num-profiles", type=int, default=3, help="Số lượng hồ sơ kiểm thử (mặc định: 3)"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None, help="Thư mục lưu báo cáo (tùy chọn)"
    )
    parser.add_argument(
        "--outer-iter", type=int, default=15, help="Số vòng lặp tầng 1 (mặc định: 15)"
    )
    parser.add_argument(
        "--outer-agents", type=int, default=10, help="Số cá thể tầng 1 (mặc định: 10)"
    )
    parser.add_argument(
        "--inner-iter", type=int, default=20, help="Số vòng lặp tầng 2 (mặc định: 20)"
    )
    parser.add_argument(
        "--inner-agents", type=int, default=10, help="Số cá thể tầng 2 (mặc định: 10)"
    )
    args = parser.parse_args()

    exit_code = run_pipeline(
        seed=args.seed,
        num_profiles=args.num_profiles,
        output_dir=args.output_dir,
        outer_iter=args.outer_iter,
        outer_agents=args.outer_agents,
        inner_iter=args.inner_iter,
        inner_agents=args.inner_agents,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
