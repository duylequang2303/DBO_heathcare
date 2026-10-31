"""
Frontend-Backend contract compatibility tests (Subagent 4).
Verifies that response schemas exactly match frontend expectation in static JS.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

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


def test_contract_targets_out():
    """Verify POST /api/targets matches frontend expectation."""
    res = client.post("/api/targets", json=BASE_PROFILE)
    assert res.status_code == 200
    data = res.json()
    assert "bmr" in data and isinstance(data["bmr"], (int, float))
    assert "tdee" in data and isinstance(data["tdee"], (int, float))
    assert "targets" in data and isinstance(data["targets"], dict)
    for k in ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sodium_mg"]:
        assert k in data["targets"]


def test_contract_menu_out():
    """Verify POST /api/menu/generate matches frontend rendering requirements."""
    res = client.post("/api/menu/generate", json={"profile": BASE_PROFILE, "seed": 9001, "config": "smoke"})
    assert res.status_code == 200
    data = res.json()

    # Top-level fields required by app.js
    required_top = ["items", "totals", "targets", "fitness", "violations", "diversity_pct", "runtime_s"]
    for field in required_top:
        assert field in data, f"Missing required top-level field '{field}'"

    # MenuItemOut fields required for table rendering
    required_item = ["food_id", "name", "slot", "meal_type", "portion_g", "portion_g_rounded", "macros"]
    for item in data["items"]:
        for field in required_item:
            assert field in item, f"Missing required item field '{field}'"

        # MacroDict required by nutrient breakdown and radar chart
        required_macro = ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sodium_mg"]
        for m in required_macro:
            assert m in item["macros"], f"Missing macro field '{m}'"


def test_contract_swap_out():
    """Verify POST /api/menu/swap matches frontend swap modal and delta display."""
    gen_res = client.post("/api/menu/generate", json={"profile": BASE_PROFILE, "seed": 9001, "config": "smoke"}).json()
    food_ids = [item["food_id"] for item in gen_res["items"]]

    swap_res = client.post("/api/menu/swap", json={
        "profile": BASE_PROFILE,
        "food_ids": food_ids,
        "slot": "breakfast_0",
        "new_food_id": None,
        "seed": 9001
    })
    assert swap_res.status_code == 200
    data = swap_res.json()

    required_swap = ["items", "totals", "targets", "violations", "delta"]
    for field in required_swap:
        assert field in data, f"Missing SwapOut field '{field}'"

    # Delta must contain changes for all key nutrients
    for k in ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sodium_mg"]:
        assert k in data["delta"], f"Missing delta for '{k}'"


def test_contract_food_search():
    """Verify GET /api/foods returns array of FoodItem with expected fields."""
    res = client.get("/api/foods?q=cơm&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        required_food = ["food_id", "food_name", "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sodium_mg", "meal_type"]
        for field in required_food:
            assert field in item, f"Missing FoodItem field '{field}'"


def test_index_html_has_medical_condition_dropdown_and_action_col():
    """Verify index.html contains select dropdown for medical condition and table action column."""
    from pathlib import Path
    html_file = Path(__file__).resolve().parents[1] / "app" / "static" / "index.html"
    assert html_file.exists()
    content = html_file.read_text(encoding="utf-8")
    assert '<select id="medicalCondition"' in content
    assert 'value="hypertension"' in content
    assert 'value="diabetes"' in content
    assert '<th>Thao tác</th>' in content


def test_app_js_has_vietnamese_meal_labels_and_no_food_id():
    """Verify app.js defines Vietnamese meal labels and does not display food_id."""
    from pathlib import Path
    js_file = Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "app.js"
    assert js_file.exists()
    content = js_file.read_text(encoding="utf-8")
    assert "MEAL_LABELS" in content
    assert "'Sáng'" in content
    assert "'Trưa'" in content
    assert "'Tối'" in content
    assert "'Phụ'" in content
    assert '<div class="food-id">' not in content
    assert 'btn-swap' in content


def test_hypertension_profile_targets_sodium():
    """Verify selecting hypertension yields sodium target <= 1500mg."""
    p = dict(BASE_PROFILE, medical_conditions=["hypertension"])
    res = client.post("/api/targets", json=p)
    assert res.status_code == 200
    data = res.json()
    assert data["targets"]["sodium_mg"] <= 1500.0


def test_api_swap_with_old_portions_delta_bounded():
    """Verify POST /api/menu/swap with old_portions_g calculates reasonable delta."""
    gen_res = client.post("/api/menu/generate", json={"profile": BASE_PROFILE, "seed": 9001, "config": "smoke"}).json()
    food_ids = [item["food_id"] for item in gen_res["items"]]
    old_portions = [item["portion_g"] for item in gen_res["items"]]

    swap_res = client.post("/api/menu/swap", json={
        "profile": BASE_PROFILE,
        "food_ids": food_ids,
        "slot": "breakfast_0",
        "new_food_id": None,
        "seed": 9001,
        "old_portions_g": old_portions
    })
    assert swap_res.status_code == 200
    data = swap_res.json()
    assert "delta" in data
    assert abs(data["delta"]["calories"]) < 1000.0


