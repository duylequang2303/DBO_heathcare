"""swap.py — Logic thay món tại một slot (Tuần 10-11).

Hoàn thiện theo TASK_WEEK10.md §"Thay Món" và AGENTS.md:
  - slot không thuộc meal_order → 400 Bad Request
  - food_ids không khớp số lượng slot → 400 Bad Request
  - hết món khác trong pool → 409 Conflict
  - new_food_id trùng món đang có trong bữa → 400 Bad Request
  - new_food_id vi phạm dị ứng → 400 Bad Request
  - new_food_id không hợp lệ/không thuộc pool → 400 Bad Request
  - Tối ưu lại khẩu phần bằng IDBO inner solver (n_agents=15, max_iter=25)
  - Làm tròn 5g ở output, tính delta dinh dưỡng và danh sách vi phạm mới
"""

from __future__ import annotations

import numpy as np
from fastapi import HTTPException

from src.algorithms.idbo import IDBO
from src.algorithms.menu_objective import decode_result, make_menu_objective
from src.models.constraints import validate_menu
from src.models.food_selector import build_meal_pools, get_meal_order_slots
from src.utils.portion_utils import round_portions

from .schemas import SwapIn, SwapOut
from .services import (
    _build_menu_items_out,
    _get_targets_with_conditions,
    _totals_from_menu,
    build_profile,
    get_food_map,
)


def swap_menu_item(req: SwapIn) -> SwapOut:
    """Thay 1 món trong slot, tối ưu lại khẩu phần bằng IDBO inner, trả delta và menu mới."""
    profile = build_profile(req.profile)
    food_map = get_food_map()
    targets = _get_targets_with_conditions(profile)
    meal_order = get_meal_order_slots(profile.meal_counts)

    # 1. Kiểm tra slot hợp lệ
    if req.slot not in meal_order:
        raise HTTPException(
            status_code=400,
            detail=f"Slot '{req.slot}' không thuộc thực đơn (chấp nhận: {meal_order})",
        )

    # 2. Kiểm tra food_ids khớp số lượng slot
    if len(req.food_ids) != len(meal_order):
        raise HTTPException(
            status_code=400,
            detail=f"Số lượng food_ids ({len(req.food_ids)}) không khớp số lượng slot ({len(meal_order)})",
        )

    slot_idx = meal_order.index(req.slot)
    meal_name = req.slot.rsplit("_", 1)[0]

    # 3. Các món đang dùng trong cùng bữa (không tính slot hiện tại đang thay)
    used_in_meal = {
        req.food_ids[i]
        for i, s in enumerate(meal_order)
        if s.rsplit("_", 1)[0] == meal_name and i != slot_idx
    }

    # 4. Lấy pool món ăn ứng viên cho slot
    pools = build_meal_pools(food_map, profile.meal_counts, profile)
    pool = pools.get(req.slot, [])

    if not pool:
        raise HTTPException(
            status_code=409,
            detail=f"Không tìm thấy danh sách món ứng viên cho slot '{req.slot}'",
        )

    # 5. Xác định new_food_id
    if req.new_food_id is not None:
        target_food = food_map.get(req.new_food_id)
        if target_food is None:
            raise HTTPException(
                status_code=400,
                detail=f"Món '{req.new_food_id}' không tồn tại trong cơ sở dữ liệu",
            )

        # Kiểm tra trùng món trong cùng bữa
        if req.new_food_id in used_in_meal:
            raise HTTPException(
                status_code=400,
                detail=f"Món mới '{req.new_food_id}' bị trùng với món khác trong cùng bữa {meal_name}",
            )

        # Kiểm tra dị ứng
        food_name_lower = str(target_food.get("food_name", "")).lower()
        for allergy in profile.allergies:
            allergy_str = allergy.strip().lower()
            if allergy_str and allergy_str in food_name_lower:
                raise HTTPException(
                    status_code=400,
                    detail=f"Món mới '{target_food.get('food_name')}' vi phạm dị ứng '{allergy}'",
                )

        # Kiểm tra món có nằm trong pool hợp lệ cho slot không
        if req.new_food_id not in pool:
            raise HTTPException(
                status_code=400,
                detail=f"Món '{req.new_food_id}' không phù hợp với vai trò của slot '{req.slot}'",
            )

        new_food_id = req.new_food_id
    else:
        # Tự chọn món khác cùng pool (không trùng món cũ và không trùng bữa)
        candidates = [
            fid for fid in pool
            if fid != req.food_ids[slot_idx] and fid not in used_in_meal
        ]
        if not candidates:
            raise HTTPException(
                status_code=409,
                detail=f"Không còn món thay thế phù hợp trong pool cho slot '{req.slot}'",
            )
        rng = np.random.default_rng(req.seed)
        new_food_id = candidates[int(rng.integers(0, len(candidates)))]

    # 6. Tạo danh sách món mới
    new_food_ids = list(req.food_ids)
    new_food_ids[slot_idx] = new_food_id

    # 7. Tính totals_old trước khi đổi
    if req.old_portions_g and len(req.old_portions_g) == len(req.food_ids):
        old_rounded = round_portions(req.old_portions_g, step=5)
        old_menu = decode_result(req.food_ids, old_rounded, food_map, profile.meal_counts)
        totals_old = _totals_from_menu(old_menu)
    else:
        # Dùng khẩu phần cơ sở 100g mỗi món
        base_portions = [100.0] * len(req.food_ids)
        old_menu = decode_result(req.food_ids, base_portions, food_map, profile.meal_counts)
        totals_old = _totals_from_menu(old_menu)

    # 8. Tối ưu lại khẩu phần liên tục bằng IDBO inner
    inner_obj = make_menu_objective(profile, new_food_ids, food_map, targets)
    inner_solver = IDBO(n_agents=15, max_iter=25)
    inner_res = inner_solver.optimize(
        inner_obj,
        dim=len(new_food_ids),
        lb=25.0,
        ub=350.0,
        seed=req.seed,
    )

    # 9. Làm tròn 5g ở output và tái đánh giá
    new_rounded = round_portions(inner_res.best_x, step=5)
    menu_new = decode_result(new_food_ids, new_rounded, food_map, profile.meal_counts)
    violations = validate_menu(menu_new, profile, targets)
    items_out = _build_menu_items_out(menu_new, profile.meal_counts)
    totals_new = _totals_from_menu(menu_new)

    # 10. Tính delta
    delta = {
        k: round(totals_new[k] - totals_old.get(k, 0.0), 2)
        for k in totals_new
    }

    return SwapOut(
        items=items_out,
        totals=totals_new,
        targets={k: round(v, 2) for k, v in targets.items()},
        violations=violations,
        delta=delta,
    )
