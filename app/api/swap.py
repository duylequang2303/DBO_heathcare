
"""swap.py — Logic thay món tại một slot (Tuần 10-11).

Hoàn thiện theo TASK_WEEK10.md và AGENTS.md:
  - Slot không hợp lệ → HTTP 400
  - Số lượng food_ids không khớp → HTTP 400
  - Hết món thay thế trong pool → HTTP 409
  - Món mới vi phạm dị ứng → HTTP 400
  - Món mới trùng trong cùng bữa → HTTP 400
  - Món mới không tồn tại hoặc không thuộc pool → HTTP 400
  - Tối ưu lại khẩu phần bằng IDBO inner solver
  - Làm tròn khẩu phần 5g, tính delta và violations
"""

from __future__ import annotations

import numpy as np
from fastapi import HTTPException

from src.algorithms.idbo import IDBO
from src.algorithms.menu_objective import (
    decode_result,
    make_menu_objective,
)
from src.models.constraints import validate_menu
from src.models.food_selector import (
    build_meal_pools,
    get_meal_order_slots,
)
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
    """Thay món tại một slot và tối ưu lại khẩu phần bằng IDBO."""

    profile = build_profile(req.profile)
    food_map = get_food_map()
    targets = _get_targets_with_conditions(profile)
    meal_order = get_meal_order_slots(profile.meal_counts)

    # 1. Kiểm tra slot hợp lệ
    if req.slot not in meal_order:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Slot '{req.slot}' không thuộc thực đơn "
                f"(chấp nhận: {meal_order})"
            ),
        )

    # 2. Kiểm tra số lượng food_ids
    if len(req.food_ids) != len(meal_order):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Số lượng food_ids ({len(req.food_ids)}) "
                f"không khớp số lượng slot ({len(meal_order)})"
            ),
        )

    # Chặn food_ids không tồn tại trong whitelist
    unknown = [
        fid for fid in req.food_ids
        if fid not in food_map
    ]

    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"food_ids không hợp lệ: {unknown[:3]}",
        )

    slot_idx = meal_order.index(req.slot)
    meal_name = req.slot.rsplit("_", 1)[0]

    # 3. Các món đã dùng trong cùng bữa, trừ slot đang thay
    used_in_meal = {
        req.food_ids[i]
        for i, slot in enumerate(meal_order)
        if (
            slot.rsplit("_", 1)[0] == meal_name
            and i != slot_idx
        )
    }

    # 4. Xây dựng pool ứng viên
    pools = build_meal_pools(
        food_map,
        profile.meal_counts,
        profile,
    )

    pool = pools.get(req.slot, [])

    if not pool:
        raise HTTPException(
            status_code=409,
            detail=(
                "Không tìm thấy danh sách món ứng viên "
                f"cho slot '{req.slot}'"
            ),
        )

    # 5. Xác định món thay thế
    if req.new_food_id is not None:

        target_food = food_map.get(req.new_food_id)

        # 5.1. Kiểm tra món có tồn tại
        if target_food is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Món '{req.new_food_id}' "
                    "không tồn tại trong cơ sở dữ liệu"
                ),
            )

        # 5.2. ƯU TIÊN kiểm tra dị ứng trước kiểm tra trùng
        food_name_lower = str(
            target_food.get("food_name", "")
        ).lower()

        for allergy in profile.allergies:
            allergy_str = str(allergy).strip().lower()

            if (
                allergy_str
                and allergy_str in food_name_lower
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Món mới '{target_food.get('food_name')}' "
                        f"vi phạm dị ứng '{allergy}'"
                    ),
                )

        # 5.3. Kiểm tra trùng món trong cùng bữa
        if req.new_food_id in used_in_meal:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Món mới '{req.new_food_id}' "
                    f"bị trùng với món khác "
                    f"trong cùng bữa {meal_name}"
                ),
            )

        # 5.4. Kiểm tra món thuộc pool hợp lệ
        if req.new_food_id not in pool:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Món '{req.new_food_id}' "
                    f"không phù hợp với vai trò "
                    f"của slot '{req.slot}'"
                ),
            )

        new_food_id = req.new_food_id

    else:
        # Tự chọn món khác cùng pool
        candidates = [
            fid
            for fid in pool
            if (
                fid != req.food_ids[slot_idx]
                and fid not in used_in_meal
            )
        ]

        if not candidates:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Không còn món thay thế phù hợp "
                    f"trong pool cho slot '{req.slot}'"
                ),
            )

        rng = np.random.default_rng(req.seed)

        new_food_id = candidates[
            int(rng.integers(0, len(candidates)))
        ]

    # 6. Tạo danh sách món mới
    new_food_ids = list(req.food_ids)
    new_food_ids[slot_idx] = new_food_id

    # 7. Tính tổng dinh dưỡng trước khi đổi món
    if req.old_portions_g is not None:
        old_rounded = round_portions(
            req.old_portions_g,
            step=5,
        )

        old_menu = decode_result(
            req.food_ids,
            old_rounded,
            food_map,
            profile.meal_counts,
        )

        totals_old = _totals_from_menu(old_menu)

    else:
        # Dùng khẩu phần cơ sở 100g khi không có old_portions_g
        base_portions = [100.0] * len(req.food_ids)

        old_menu = decode_result(
            req.food_ids,
            base_portions,
            food_map,
            profile.meal_counts,
        )

        totals_old = _totals_from_menu(old_menu)

    # 8. Tối ưu lại khẩu phần bằng IDBO inner
    inner_obj = make_menu_objective(
        profile,
        new_food_ids,
        food_map,
        targets,
    )

    inner_solver = IDBO(
        n_agents=15,
        max_iter=25,
    )

    inner_res = inner_solver.optimize(
        inner_obj,
        dim=len(new_food_ids),
        lb=25.0,
        ub=350.0,
        seed=req.seed,
    )

    # 9. Làm tròn 5g và kiểm tra ràng buộc
    new_rounded = round_portions(
        inner_res.best_x,
        step=5,
    )

    menu_new = decode_result(
        new_food_ids,
        new_rounded,
        food_map,
        profile.meal_counts,
    )

    violations = validate_menu(
        menu_new,
        profile,
        targets,
    )

    items_out = _build_menu_items_out(
        menu_new,
        profile.meal_counts,
    )

    totals_new = _totals_from_menu(menu_new)

    # 10. Tính delta dinh dưỡng
    delta = {
        k: round(
            totals_new[k] - totals_old.get(k, 0.0),
            2,
        )
        for k in totals_new
    }

    return SwapOut(
        items=items_out,
        totals=totals_new,
        targets={
            k: round(v, 2)
            for k, v in targets.items()
        },
        violations=violations,
        delta=delta,
    )
