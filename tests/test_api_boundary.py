"""
Tests for API boundaries, validation, injection/XSS edge cases, and error responses.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BASE_VALID_PROFILE = {
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


def test_profile_extreme_boundaries():
    """Verify age, height, weight boundary rejections."""
    # Negative age -> 422
    p = dict(BASE_VALID_PROFILE, age=-1)
    res = client.post("/api/targets", json=p)
    assert res.status_code == 422

    # Age > 120 -> 422
    p = dict(BASE_VALID_PROFILE, age=121)
    res = client.post("/api/targets", json=p)
    assert res.status_code == 422

    # Zero height -> 422
    p = dict(BASE_VALID_PROFILE, height_cm=0)
    res = client.post("/api/targets", json=p)
    assert res.status_code == 422

    # Height > 250 -> 422
    p = dict(BASE_VALID_PROFILE, height_cm=251)
    res = client.post("/api/targets", json=p)
    assert res.status_code == 422

    # Zero weight -> 422
    p = dict(BASE_VALID_PROFILE, weight_kg=0)
    res = client.post("/api/targets", json=p)
    assert res.status_code == 422

    # Weight > 400 -> 422
    p = dict(BASE_VALID_PROFILE, weight_kg=401)
    res = client.post("/api/targets", json=p)
    assert res.status_code == 422


def test_meal_counts_all_zero_rejected():
    """A profile with 0 total meals cannot form a valid menu -> reject 400 on generate."""
    p = dict(BASE_VALID_PROFILE, meal_counts={"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0})
    res = client.post("/api/menu/generate", json={"profile": p, "config": "smoke"})
    assert res.status_code == 400
    assert "ít nhất 1 món" in res.text


def test_meal_counts_invalid_keys_and_ranges():
    """Test invalid meal keys and negative or excess counts."""
    # Unknown meal name -> 422
    p = dict(BASE_VALID_PROFILE, meal_counts={"supper": 1})
    res = client.post("/api/targets", json=p)
    assert res.status_code == 422

    # Negative count -> 422
    p = dict(BASE_VALID_PROFILE, meal_counts={"breakfast": -1, "lunch": 2, "dinner": 2, "snack": 1})
    res = client.post("/api/targets", json=p)
    assert res.status_code == 422

    # Excess count (>5 for main meal) -> 422
    p = dict(BASE_VALID_PROFILE, meal_counts={"breakfast": 6, "lunch": 2, "dinner": 2, "snack": 1})
    res = client.post("/api/targets", json=p)
    assert res.status_code == 422

    # Excess count (>3 for snack) -> 422
    p = dict(BASE_VALID_PROFILE, meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 4})
    res = client.post("/api/targets", json=p)
    assert res.status_code == 422


def test_food_search_injection_and_edge_cases():
    """Verify /api/foods safely handles empty, injection, and special characters."""
    # Empty query returns top results
    res = client.get("/api/foods?q=&limit=5")
    assert res.status_code == 200
    assert len(res.json()) <= 5

    # SQL injection / quote test
    res = client.get("/api/foods?q=' OR '1'='1&limit=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # XSS payload
    res = client.get("/api/foods?q=<script>alert('xss')</script>&limit=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Unicode & Vietnamese diacritics
    res = client.get("/api/foods?q=cơm tấm&limit=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_empty_and_malformed_requests():
    """Empty payload for POST endpoints must return 422."""
    assert client.post("/api/targets", json={}).status_code == 422
    assert client.post("/api/menu/generate", json={}).status_code == 422
    assert client.post("/api/menu/swap", json={}).status_code == 422
