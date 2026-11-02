"""Tests for KE_HOACH_FIX_NGAY_MAI items 3, 4, 5.

3. SwapOut returns recomputed fitness
4. MenuOut/SwapOut return medical warnings + data limitations
5. 422 messages in Vietnamese; UI hides solver knobs; fitness label in Vietnamese
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ROOT = Path(__file__).resolve().parents[1]

BASE_PROFILE = {
    "name": "Duy",
    "age": 22,
    "gender": "male",
    "height_cm": 170.0,
    "weight_kg": 65.0,
    "activity_level": "MODERATE",
    "goal": "MAINTAIN",
    "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
    "medical_conditions": ["healthy"],
    "allergies": [],
    "dislikes": [],
}


@pytest.fixture(scope="module")
def sample_menu():
    res = client.post(
        "/api/menu/generate",
        json={"profile": BASE_PROFILE, "seed": 9001, "config": "smoke"},
    )
    assert res.status_code == 200
    return res.json()


def test_swap_response_includes_recomputed_fitness(sample_menu):
    food_ids = [item["food_id"] for item in sample_menu["items"]]
    portions_g = [item["portion_g"] for item in sample_menu["items"]]
    res = client.post(
        "/api/menu/swap",
        json={
            "profile": BASE_PROFILE,
            "food_ids": food_ids,
            "slot": "lunch_0",
            "new_food_id": None,
            "seed": 9001,
            "old_portions_g": portions_g,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "fitness" in data
    assert isinstance(data["fitness"], (int, float))
    assert -100.0 <= data["fitness"] <= 100.0


def test_generate_includes_prototype_disclaimer(sample_menu):
    assert "data_limitations" in sample_menu
    joined = " ".join(sample_menu["data_limitations"])
    assert "prototype" in joined.lower()
    assert "không phải thiết bị y tế" in joined.lower()


def test_generate_diabetes_includes_sugar_warning():
    profile = dict(BASE_PROFILE, medical_conditions=["diabetes"])
    res = client.post(
        "/api/menu/generate",
        json={"profile": profile, "seed": 9001, "config": "smoke"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "warnings" in data
    joined = " ".join(data["warnings"])
    assert "đường" in joined.lower() or "sugar" in joined.lower()
    assert "không bảo đảm an toàn lâm sàng" in joined.lower()


def test_generate_healthy_has_no_diabetes_clinical_warning(sample_menu):
    warnings = sample_menu.get("warnings") or []
    joined = " ".join(warnings).lower()
    assert "an toàn lâm sàng" not in joined


def test_swap_includes_warnings_and_limitations(sample_menu):
    food_ids = [item["food_id"] for item in sample_menu["items"]]
    res = client.post(
        "/api/menu/swap",
        json={
            "profile": BASE_PROFILE,
            "food_ids": food_ids,
            "slot": "snack_0",
            "new_food_id": None,
            "seed": 9001,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "warnings" in data
    assert "data_limitations" in data
    assert any("prototype" in x.lower() for x in data["data_limitations"])


def test_422_age_message_is_vietnamese():
    profile = dict(BASE_PROFILE, age=17)
    res = client.post("/api/targets", json=profile)
    assert res.status_code == 422
    text = res.text.lower()
    assert "field required" not in text
    assert "input should be" not in text
    assert "tuổi" in text


def test_422_missing_name_is_vietnamese():
    profile = dict(BASE_PROFILE)
    del profile["name"]
    res = client.post("/api/targets", json=profile)
    assert res.status_code == 422
    text = res.text.lower()
    assert "field required" not in text
    assert "họ tên" in text or "ho ten" in text or "tên" in text


def test_index_hides_seed_and_solver_behind_advanced():
    html = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")
    assert "Tùy chọn nâng cao" in html
    seed_pos = html.find('id="inpSeed"')
    cfg_pos = html.find('id="cfgSmoke"')
    adv_pos = html.find("Tùy chọn nâng cao")
    assert seed_pos > 0 and cfg_pos > 0 and adv_pos > 0
    assert adv_pos < seed_pos
    assert adv_pos < cfg_pos


def test_app_js_uses_vietnamese_fitness_label():
    js = (ROOT / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "Độ phù hợp mục tiêu" in js
    assert "Fitness:" not in js


def test_422_age_message_includes_threshold_value():
    """1.3: lỗi 422 phải nêu ngưỡng cụ thể, không nói chung chung."""
    profile = dict(BASE_PROFILE, age=17)
    res = client.post("/api/targets", json=profile)
    assert res.status_code == 422
    msg = " ".join(d["msg"] for d in res.json()["detail"])
    assert "Tuổi" in msg
    assert "18" in msg
    assert "tối thiểu" not in msg


def test_422_height_message_includes_lower_threshold():
    profile = dict(BASE_PROFILE, height_cm=0)
    res = client.post("/api/targets", json=profile)
    assert res.status_code == 422
    msg = " ".join(d["msg"] for d in res.json()["detail"])
    assert "Chiều cao" in msg
    assert "0" in msg
    assert "tối thiểu" not in msg


def test_422_weight_message_includes_upper_threshold():
    profile = dict(BASE_PROFILE, weight_kg=500)
    res = client.post("/api/targets", json=profile)
    assert res.status_code == 422
    msg = " ".join(d["msg"] for d in res.json()["detail"])
    assert "Cân nặng" in msg
    assert "400" in msg


def test_api_js_does_not_double_prefix_english_field_key():
    """1.1: toast không được ghép 'name: ' trước câu đã Việt hóa."""
    js = (ROOT / "app" / "static" / "js" / "api.js").read_text(encoding="utf-8")
    assert "formatFieldError" in js
    # Mẫu cũ luôn ghép khóa tiếng Anh vào mọi message.
    assert "`${d.loc?.slice(-1)[0] || 'trường'}: ${d.msg}`" not in js


def test_menu_notices_normalizes_vietnamese_diabetes_alias():
    """1.2: menu_notices không được bỏ lọt alias 'tiểu đường'."""
    from app.api.services import menu_notices
    from src.models.user_profile import ActivityLevel, Gender, Goal, UserProfile

    profile = UserProfile(
        name="Lan",
        age=45,
        gender=Gender.FEMALE,
        height_cm=158.0,
        weight_kg=62.0,
        activity_level=ActivityLevel.LIGHT,
        goal=Goal.LOSE_WEIGHT,
        medical_conditions=["tiểu đường"],
        allergies=[],
        dislikes=[],
        likes=[],
        meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
    )
    warnings, limitations = menu_notices(profile)
    assert any("đường" in w.lower() for w in warnings)
    assert not any("an toàn lâm sàng" in w.lower() for w in limitations)
    assert any("prototype" in item.lower() for item in limitations)
