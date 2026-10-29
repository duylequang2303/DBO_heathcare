"""
Concurrency and thread-safety tests for FastAPI backend (Subagent 4).
"""
import concurrent.futures
import time
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


def _run_single_generate(seed: int):
    payload = {
        "profile": BASE_PROFILE,
        "seed": seed,
        "config": "smoke",
    }
    start = time.perf_counter()
    res = client.post("/api/menu/generate", json=payload)
    duration = time.perf_counter() - start
    return res.status_code, res.json(), duration


def test_concurrent_menu_generations():
    """Verify that multiple concurrent generate requests run safely without race conditions."""
    seeds = [9001, 9002, 9003, 9004]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_run_single_generate, seed) for seed in seeds]
        results = [f.result() for f in futures]

    for status_code, data, duration in results:
        assert status_code == 200
        assert "items" in data
        assert len(data["items"]) == 7
        assert "totals" in data
        assert data["fitness"] > -100
        assert duration < 5.0, f"Request took too long: {duration}s"


def test_runtime_field_populated_and_accurate():
    """Verify runtime_s in MenuOut is non-zero and reasonable."""
    payload = {
        "profile": BASE_PROFILE,
        "seed": 9001,
        "config": "smoke",
    }
    res = client.post("/api/menu/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "runtime_s" in data
    assert 0 < data["runtime_s"] < 5.0

