"""swap.py — Logic thay món tại một slot (Cương - Tuần 10).

Stub hiện tại: trả HTTPException 501.
Cương sẽ implement đầy đủ theo TASK_WEEK10.md §"Thay Món".

Edge cases bắt buộc xử lý:
  - slot không thuộc meal_order → 400 Bad Request
  - hết món khác trong pool → 409 Conflict + gợi ý
  - new_food_id trùng món đang có trong bữa → 400
  - new_food_id vi phạm dị ứng → 400
  - Đổi xong → trả delta calo/macro + vi phạm mới
"""

from __future__ import annotations

from fastapi import HTTPException

from .schemas import SwapIn, SwapOut


def swap_menu_item(req: SwapIn) -> SwapOut:
    """Thay 1 món trong slot, tối ưu lại gram bằng IDBO inner, trả delta.

    TODO (Cương):
      1. build_profile(req.profile)
      2. get_meal_order_slots(profile.meal_counts)
      3. build_meal_pools(food_map, meal_counts, profile)
      4. Kiểm tra req.slot hợp lệ (400 nếu không)
      5. Chọn new_food_id hoặc validate new_food_id cung cấp
      6. Tạo new_ids bằng cách thay phần tử tại index slot
      7. IDBO inner optimize: make_menu_objective + IDBO(n_agents=15, max_iter=25)
      8. decode_result, validate_menu, tính delta
      9. Trả SwapOut
    """
    raise HTTPException(status_code=501, detail="swap_menu_item chưa được triển khai (Cương)")
