"""Unit tests for TASK C4: Dish role classification & slot policy hardening.

Verifies culinary roles for prepared dishes, avoids misclassifying cooked/dairy/legume
items, and guarantees role pool sufficiency for meal slots.
"""

import pytest

from app.api.schemas import ProfileIn
from app.api.services import PRESET_PROFILES, build_profile, get_food_map
from src.models.dish_category import DishRole, classify_dish_role
from src.models.food_selector import MIN_ROLE_POOL_SIZE, _roles_for_slot, build_meal_pools


@pytest.mark.parametrize(
    ("food_name", "category", "source", "expected_role"),
    [
        # Nhóm Tinh bột / Staples (nấu chín hoặc ngũ cốc ăn được)
        ("Cơm gạo lứt", "", "vietnamese", DishRole.STAPLE),
        ("Cơm kê", "", "vietnamese", DishRole.STAPLE),
        ("Cơm tẻ trắng", "", "vietnamese", DishRole.STAPLE),
        ("Đậu đậu nành/đậu tương hấp", "", "vietnamese", DishRole.STAPLE),
        ("Đậu xanh luộc", "", "vietnamese", DishRole.STAPLE),
        ("Khoai tây luộc", "", "vietnamese", DishRole.STAPLE),
        ("Khoai lang luộc", "", "vietnamese", DishRole.STAPLE),
        # Nhóm Rau / Vegetables
        ("Đậu hà lan luộc", "", "vietnamese", DishRole.VEGETABLE),
        ("Rau muống luộc", "", "vietnamese", DishRole.VEGETABLE),
        ("Măng tre luộc", "", "vietnamese", DishRole.VEGETABLE),
        # Nhóm Đạm chính / Main Protein
        ("Trứng vịt lộn luộc", "", "vietnamese", DishRole.MAIN_PROTEIN),
        ("Tép gạo", "thủy sản", "vietnamese", DishRole.MAIN_PROTEIN),
        # Nhóm Snack / Trái cây / Sữa
        ("Sữa bò tươi", "", "vietnamese", DishRole.FRUIT_SNACK),
        ("Sữa đậu nành", "", "vietnamese", DishRole.FRUIT_SNACK),
        ("Mãng cầu xiêm", "", "vietnamese", DishRole.FRUIT_SNACK),
        ("Cookies, oatmeal", "snacks", "", DishRole.FRUIT_SNACK),
    ],
)
def test_c4_dish_role_classification(food_name, category, source, expected_role):
    """TASK C4 Bước 1: Phân loại đúng vai trò ẩm thực cho các món ăn cụ thể."""
    role = classify_dish_role(food_name, category=category, source=source)
    assert role == expected_role, f"'{food_name}' được phân loại là {role}, mong đợi {expected_role}"


def test_pea_not_misclassified_as_fruit_snack():
    """Đậu hà lan có chữ 'hạt' trong category/tên không được bị xếp là FRUIT_SNACK."""
    role = classify_dish_role("Đậu hà lan (hạt)", category="hạt", source="vietnamese")
    assert role != DishRole.FRUIT_SNACK, "Đậu hà lan không được là FRUIT_SNACK"
    assert role == DishRole.VEGETABLE


def test_cooked_dishes_never_classified_as_raw_ingredient():
    """Tên có từ chỉ trạng thái chế biến không bao giờ bị rơi vào RAW_INGREDIENT."""
    cooked_names = [
        "Rau muống luộc",
        "Măng tre xào",
        "Đậu cô ve luộc",
        "Thịt lợn nướng",
        "Cá basa kho",
        "Bí đao nấu",
        "Khoai tây hấp",
    ]
    for name in cooked_names:
        role = classify_dish_role(name, source="vietnamese")
        assert role != DishRole.RAW_INGREDIENT, f"Món chín '{name}' không được là RAW_INGREDIENT"


def test_breakfast_1_slot_policy_excludes_fruit_snack():
    """TASK C4 Bước 2: breakfast_1 là bữa chính nên không nhận FRUIT_SNACK hoặc BEVERAGE."""
    roles = _roles_for_slot("breakfast", slot_idx=1, count=2)
    assert DishRole.FRUIT_SNACK not in roles
    assert DishRole.BEVERAGE not in roles
    assert DishRole.MAIN_PROTEIN in roles


def test_main_meals_slot0_is_always_staple():
    """Slot 0 của các bữa chính luôn là STAPLE."""
    for meal in ["breakfast", "lunch", "dinner"]:
        roles = _roles_for_slot(meal, slot_idx=0, count=2)
        assert roles == {DishRole.STAPLE}


def test_whitelist_role_pools_satisfy_min_threshold_all_presets():
    """Mọi slot trong menu 2-2-2-1 với P1, P2, P3 trên whitelist đều đạt MIN_ROLE_POOL_SIZE >= 3."""
    food_map = get_food_map()
    for key in ["p1", "p2", "p3"]:
        profile = build_profile(ProfileIn(**PRESET_PROFILES[key]))
        pools = build_meal_pools(food_map, profile.meal_counts, profile)

        # Đảm bảo đủ các slot yêu cầu
        assert "breakfast_0" in pools
        assert "breakfast_1" in pools
        assert "lunch_0" in pools
        assert "lunch_1" in pools
        assert "dinner_0" in pools
        assert "dinner_1" in pools
        assert "snack_0" in pools

        for slot_name, food_ids in pools.items():
            assert len(food_ids) >= MIN_ROLE_POOL_SIZE, (
                f"Preset {key}, slot '{slot_name}' chỉ có {len(food_ids)} món "
                f"(ngưỡng tối thiểu {MIN_ROLE_POOL_SIZE})"
            )


@pytest.mark.parametrize('name', ['Dầu rang', 'Dầu đậu nành rang', 'Bột mì rang', 'Mỡ chiên'])
def test_cooking_word_does_not_make_industrial_product_a_dish(name):
    assert classify_dish_role(name) == DishRole.RAW_INGREDIENT

@pytest.mark.parametrize(('name', 'role'), [
    ('Thịt gà rang dầu', DishRole.MAIN_PROTEIN),
    ('Rau xào dầu', DishRole.VEGETABLE),
    ('Cá chiên bột mì', DishRole.MAIN_PROTEIN),
])
def test_prepared_dish_can_mention_industrial_ingredient(name, role):
    assert classify_dish_role(name) == role


def test_industrial_products_with_cooked_words_stay_raw_ingredient():
    """CodeRabbit review: Sản phẩm công nghiệp (dầu, mỡ, bột) dù có từ 'rang', 'rán', 'chiên' vẫn phải là RAW_INGREDIENT."""
    industrial_names = [
        "Dầu rang",
        "Mỡ rán",
        "Bột chiên xù",
        "Dầu cám gạo",
        "Bột nướng",
    ]
    for name in industrial_names:
        role = classify_dish_role(name, source="vietnamese")
        assert role == DishRole.RAW_INGREDIENT, (
            f"Sản phẩm công nghiệp '{name}' không được gán role {role}, phải là RAW_INGREDIENT"
        )
