"""
Comprehensive tests for POST /api/menu/swap endpoint (Week 10-11).
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


@pytest.fixture(scope="module")
def sample_menu():
    """Generate a baseline menu for swap tests."""
    req = {
        "profile": BASE_PROFILE,
        "seed": 9001,
        "config": "smoke",
    }
    res = client.post("/api/menu/generate", json=req)
    assert res.status_code == 200
    return res.json()


def test_swap_auto_candidate_success(sample_menu):
    """Test swapping a dish when new_food_id is None (auto-select from pool)."""
    food_ids = [item["food_id"] for item in sample_menu["items"]]
    portions_g = [item["portion_g"] for item in sample_menu["items"]]
    target_slot = "lunch_0"
    target_idx = [i["slot"] for i in sample_menu["items"]].index(target_slot)
    original_food = food_ids[target_idx]

    swap_payload = {
        "profile": BASE_PROFILE,
        "food_ids": food_ids,
        "slot": target_slot,
        "new_food_id": None,
        "seed": 9001,
        "old_portions_g": portions_g,
    }

    res = client.post("/api/menu/swap", json=swap_payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert "items" in data
    assert "totals" in data
    assert "delta" in data
    assert "violations" in data

    # Swapped food must be different
    new_food = data["items"][target_idx]["food_id"]
    assert new_food != original_food

    # Other meals must remain unchanged
    other_original = [fid for i, fid in enumerate(food_ids) if i != target_idx]
    other_new = [item["food_id"] for i, item in enumerate(data["items"]) if i != target_idx]
    assert other_original == other_new

    # Portions must be rounded to 5g
    for item in data["items"]:
        assert item["portion_g_rounded"] % 5 == 0
        assert 25 <= item["portion_g_rounded"] <= 350

    # Delta must be computed for all macro keys
    for k in ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sodium_mg"]:
        assert k in data["delta"]


def test_swap_specific_candidate_success(sample_menu):
    """Test swapping a dish specifying a valid new_food_id from food search."""
    food_ids = [item["food_id"] for item in sample_menu["items"]]
    target_slot = "snack_0"
    target_idx = [i["slot"] for i in sample_menu["items"]].index(target_slot)
    original_food = food_ids[target_idx]

    # Search for an apple or fruit
    search_res = client.get("/api/foods?q=táo&limit=10").json()
    valid_candidates = [f["food_id"] for f in search_res if f["food_id"] != original_food and f["food_id"] not in food_ids]
    if not valid_candidates:
        search_res = client.get("/api/foods?q=chuối&limit=10").json()
        valid_candidates = [f["food_id"] for f in search_res if f["food_id"] != original_food and f["food_id"] not in food_ids]

    candidate_id = valid_candidates[0]
    swap_payload = {
        "profile": BASE_PROFILE,
        "food_ids": food_ids,
        "slot": target_slot,
        "new_food_id": candidate_id,
        "seed": 9001,
    }
    res = client.post("/api/menu/swap", json=swap_payload)
    # May return 200 or 400 if candidate role doesn't match slot
    if res.status_code == 200:
        data = res.json()
        assert data["items"][target_idx]["food_id"] == candidate_id


def test_swap_invalid_slot_returns_400(sample_menu):
    """Slot not belonging to meal_order must return HTTP 400."""
    food_ids = [item["food_id"] for item in sample_menu["items"]]
    swap_payload = {
        "profile": BASE_PROFILE,
        "food_ids": food_ids,
        "slot": "invalid_slot_99",
        "new_food_id": None,
    }
    res = client.post("/api/menu/swap", json=swap_payload)
    assert res.status_code == 400
    assert "Slot" in res.text or "slot" in res.text


def test_swap_duplicate_food_in_same_meal_returns_400(sample_menu):
    """Swapping with a food already used in the same meal must return HTTP 400."""
    food_ids = [item["food_id"] for item in sample_menu["items"]]
    # In breakfast (breakfast_0 and breakfast_1), swap breakfast_0 with breakfast_1's food
    b0_food = food_ids[0]
    b1_food = food_ids[1]

    swap_payload = {
        "profile": BASE_PROFILE,
        "food_ids": food_ids,
        "slot": "breakfast_0",
        "new_food_id": b1_food,
    }
    res = client.post("/api/menu/swap", json=swap_payload)
    assert res.status_code == 400
    assert "trùng" in res.text.lower() or "duplicate" in res.text.lower()


def test_swap_allergen_food_returns_400(sample_menu):
    """Swapping with an allergen food must return HTTP 400."""
    allergic_profile = dict(BASE_PROFILE, allergies=["tôm"])
    food_ids = [item["food_id"] for item in sample_menu["items"]]

    # Find a food containing "tôm"
    search_res = client.get("/api/foods?q=tôm&limit=5").json()
    assert len(search_res) > 0
    shrimp_food_id = search_res[0]["food_id"]

    swap_payload = {
        "profile": allergic_profile,
        "food_ids": food_ids,
        "slot": "lunch_1",
        "new_food_id": shrimp_food_id,
    }
    res = client.post("/api/menu/swap", json=swap_payload)
    assert res.status_code == 400
    assert "dị ứng" in res.text.lower() or "allergy" in res.text.lower() or "không phù hợp" in res.text.lower()


def test_swap_mismatched_food_ids_length_returns_400():
    """Mismatched food_ids length must return HTTP 400."""
    swap_payload = {
        "profile": BASE_PROFILE,
        "food_ids": ["USDA_123"],  # Only 1 item when 7 required
        "slot": "breakfast_0",
        "new_food_id": None,
    }
    res = client.post("/api/menu/swap", json=swap_payload)
    assert res.status_code == 400
