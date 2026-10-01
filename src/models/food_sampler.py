import numpy as np

from src.models.user_profile import UserProfile


MEAL_ORDER = ("breakfast", "lunch", "dinner", "snack")


def _normalize_text(value) -> str:
    """Chuyển dữ liệu về chuỗi chữ thường để so sánh."""
    if value is None:
        return ""

    text = str(value).strip().lower()

    if text in ("", "nan", "none"):
        return ""

    return text


def _is_blocked_food(food_name: str, profile: UserProfile) -> bool:
    """
    Kiểm tra tên món có chứa từ khóa dị ứng hoặc món không thích hay không.
    """
    name = _normalize_text(food_name)

    blocked_tokens = [
        token
        for token in (profile.allergies + profile.dislikes)
        if _normalize_text(token)
    ]

    return any(
        _normalize_text(token) in name
        for token in blocked_tokens
    )


def candidates_for_meal(
    food_map: dict,
    meal_name: str,
    profile: UserProfile,
) -> list[str]:
    """
    Trả về các food_id hợp lệ cho một bữa ăn.

    Quy tắc:
    - breakfast: ưu tiên meal_type='breakfast'
    - lunch/dinner: meal_type='all'
    - snack: meal_type='snack'
    - loại món chứa allergy/dislike
    """
    if meal_name not in MEAL_ORDER:
        raise ValueError(f"Unknown meal: {meal_name}")

    if meal_name == "breakfast":
        allowed_types = {"breakfast"}
    elif meal_name in ("lunch", "dinner"):
        allowed_types = {"all"}
    else:
        allowed_types = {"snack"}

    candidates = []

    for food_id, row in food_map.items():
        food_name = row.get("food_name", "")
        meal_type = _normalize_text(row.get("meal_type"))

        if meal_type not in allowed_types:
            continue

        if _is_blocked_food(food_name, profile):
            continue

        candidates.append(food_id)

    return candidates


def sample_food_ids(
    food_map: dict,
    meal_counts: dict[str, int],
    profile: UserProfile,
    rng: np.random.Generator,
) -> list[str]:
    """
    Chọn food_id hợp lệ cho thực đơn trong ngày.

    Kết quả có thứ tự:
    breakfast -> lunch -> dinner -> snack.

    Không chọn trùng food_id trong cùng một ngày.
    Tất cả lựa chọn ngẫu nhiên đều sử dụng rng.

    Với breakfast, nếu số món có nhãn 'breakfast' không đủ,
    hàm fallback sang các món meal_type='all' hoặc rỗng,
    nhưng vẫn ưu tiên món có nhãn breakfast.
    """
    selected_ids: list[str] = []
    used_ids: set[str] = set()

    for meal_name in MEAL_ORDER:
        count = meal_counts.get(meal_name, 0)

        if isinstance(count, bool) or not isinstance(count, int):
            raise ValueError(
                f"meal_counts['{meal_name}'] must be an integer"
            )

        if count < 0:
            raise ValueError(
                f"meal_counts['{meal_name}'] must be non-negative"
            )

        if count == 0:
            continue

        candidates = candidates_for_meal(
            food_map,
            meal_name,
            profile,
        )

        candidates = [
            food_id
            for food_id in candidates
            if food_id not in used_ids
        ]

        # Breakfast được phép fallback nếu pool breakfast không đủ.
        if meal_name == "breakfast" and len(candidates) < count:
            fallback = []

            for food_id, row in food_map.items():
                if food_id in used_ids or food_id in candidates:
                    continue

                meal_type = _normalize_text(row.get("meal_type"))

                if meal_type not in ("", "all"):
                    continue

                if _is_blocked_food(
                    row.get("food_name", ""),
                    profile,
                ):
                    continue

                fallback.append(food_id)

            candidates.extend(fallback)

        if len(candidates) < count:
            raise ValueError(
                f"Not enough candidates for {meal_name}: "
                f"need {count}, found {len(candidates)}"
            )

        chosen = rng.choice(
            candidates,
            size=count,
            replace=False,
        ).tolist()

        selected_ids.extend(chosen)
        used_ids.update(chosen)

    expected_count = sum(
        meal_counts.get(meal_name, 0)
        for meal_name in MEAL_ORDER
    )

    if len(selected_ids) != expected_count:
        raise ValueError(
            "Number of selected food_ids does not match meal_counts"
        )

    return selected_ids