"""
API endpoint tests using TestClient
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app

client = TestClient(app)

def test_health_check():
    """Test GET /api/health"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data

def test_get_profiles():
    """Test GET /api/profiles"""
    response = client.get("/api/profiles")
    assert response.status_code == 200
    data = response.json()
    assert "profiles" in data
    assert len(data["profiles"]) == 3
    assert data["profiles"][0]["id"] == "p1"

def test_calculate_targets_p1():
    """Test POST /api/targets with P1 profile"""
    profile = {
        "name": "Duy",
        "age": 22,
        "gender": "male",
        "height_cm": 170.0,
        "weight_kg": 65.0,
        "activity_level": "MODERATE",
        "goal": "MAINTAIN",
        "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
        "medical_conditions": [],
        "allergies": [],
        "dislikes": []
    }
    
    response = client.post("/api/targets", json=profile)
    assert response.status_code == 200
    data = response.json()
    
    assert "bmr" in data
    assert "tdee" in data
    assert "targets" in data
    assert data["bmr"] > 0
    assert data["tdee"] > data["bmr"]
    assert data["targets"]["calories"] > 0
    assert data["targets"]["protein_g"] > 0

def test_calculate_targets_invalid_age():
    """Test POST /api/targets with invalid age"""
    profile = {
        "name": "Test",
        "age": 150,  # Invalid
        "gender": "male",
        "height_cm": 170.0,
        "weight_kg": 65.0,
        "activity_level": "MODERATE",
        "goal": "MAINTAIN"
    }
    
    response = client.post("/api/targets", json=profile)
    assert response.status_code == 422  # Validation error

def test_generate_menu_smoke():
    """Test POST /api/menu/generate with smoke config"""
    profile = {
        "name": "Duy",
        "age": 22,
        "gender": "male",
        "height_cm": 170.0,
        "weight_kg": 65.0,
        "activity_level": "MODERATE",
        "goal": "MAINTAIN",
        "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
        "medical_conditions": [],
        "allergies": [],
        "dislikes": []
    }
    
    request = {
        "profile": profile,
        "seed": 9001,
        "config": "smoke"
    }
    
    response = client.post("/api/menu/generate", json=request)
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "totals" in data
    assert "targets" in data
    assert "fitness" in data
    assert len(data["items"]) == 7  # 2+2+2+1
    assert data["fitness"] > -100
    
    # Check portion rounding
    for item in data["items"]:
        assert item["name"]
        assert item["name"] != "Unknown"
        assert item["portion_g_rounded"] % 5 == 0
        assert 25 <= item["portion_g_rounded"] <= 350

def test_search_foods():
    """Test GET /api/foods"""
    response = client.get("/api/foods?q=rice&limit=5")
    assert response.status_code == 200
    data = response.json()
    
    assert "foods" in data
    assert "count" in data
    assert data["count"] <= 5
    assert data["count"] > 0
    assert all(food["name"] != "Unknown" for food in data["foods"])

@pytest.mark.slow
def test_menu_swap():
    """Test POST /api/menu/swap"""
    # First generate a menu
    profile = {
        "name": "Duy",
        "age": 22,
        "gender": "male",
        "height_cm": 170.0,
        "weight_kg": 65.0,
        "activity_level": "MODERATE",
        "goal": "MAINTAIN",
        "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
        "medical_conditions": [],
        "allergies": [],
        "dislikes": []
    }
    
    gen_request = {
        "profile": profile,
        "seed": 9001,
        "config": "smoke"
    }
    
    gen_response = client.post("/api/menu/generate", json=gen_request)
    assert gen_response.status_code == 200
    menu = gen_response.json()
    
    # Now swap one item
    food_ids = [item["food_id"] for item in menu["items"]]
    portions_g = [item["portion_g"] for item in menu["items"]]
    
    swap_request = {
        "profile": profile,
        "food_ids": food_ids,
        "portions_g": portions_g,
        "slot": "breakfast_0",
        "new_food_id": None,
        "seed": 9001
    }
    
    swap_response = client.post("/api/menu/swap", json=swap_request)
    assert swap_response.status_code == 200
    new_menu = swap_response.json()
    
    assert "items" in new_menu
    assert len(new_menu["items"]) == 7
    # Verify the swapped item is different
    assert new_menu["items"][0]["food_id"] != food_ids[0]

def test_menu_swap_invalid_slot():
    """Test POST /api/menu/swap with invalid slot"""
    profile = {
        "name": "Duy",
        "age": 22,
        "gender": "male",
        "height_cm": 170.0,
        "weight_kg": 65.0,
        "activity_level": "MODERATE",
        "goal": "MAINTAIN",
        "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1}
    }
    
    swap_request = {
        "profile": profile,
        "food_ids": ["1", "2", "3", "4", "5", "6", "7"],
        "portions_g": [100, 100, 100, 100, 100, 100, 100],
        "slot": "invalid_slot",
        "seed": 9001
    }
    
    response = client.post("/api/menu/swap", json=swap_request)
    assert response.status_code == 400
