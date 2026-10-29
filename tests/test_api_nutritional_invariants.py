"""
Nutritional and Domain Invariants Audit for Web API (AGENTS.md compliance).
"""
import math
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

P1_PROFILE = {
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


def test_deterministic_menu_generation():
    """Invariant §4.3: Same input + same seed must produce identical menus."""
    req = {
        "profile": P1_PROFILE,
        "seed": 9001,
        "config": "smoke",
    }
    res1 = client.post("/api/menu/generate", json=req).json()
    res2 = client.post("/api/menu/generate", json=req).json()

    food_ids1 = [item["food_id"] for item in res1["items"]]
    food_ids2 = [item["food_id"] for item in res2["items"]]
    assert food_ids1 == food_ids2

    portions1 = [item["portion_g_rounded"] for item in res1["items"]]
    portions2 = [item["portion_g_rounded"] for item in res2["items"]]
    assert portions1 == portions2

    assert res1["totals"] == res2["totals"]
    assert res1["fitness"] == res2["fitness"]


def test_portion_rounding_5g_and_bounds():
    """Invariant §4.4 & §4.7: Portions rounded to 5g multiples, within bounds."""
    req = {
        "profile": P1_PROFILE,
        "seed": 9001,
        "config": "smoke",
    }
    res = client.post("/api/menu/generate", json=req).json()
    items = res["items"]
    assert len(items) == 7

    for item in items:
        p_round = item["portion_g_rounded"]
        assert p_round % 5 == 0, f"Portion {p_round} is not a multiple of 5g"
        assert 25 <= p_round <= 350, f"Portion {p_round} out of technical bounds [25, 350]"
        assert item["portion_g"] > 0, "Continuous portion must be positive"


def test_nutrient_values_sanity_no_nan_or_negative():
    """Invariant §4.1: No negative, NaN or inf nutrients in items or totals."""
    req = {
        "profile": P1_PROFILE,
        "seed": 9001,
        "config": "smoke",
    }
    res = client.post("/api/menu/generate", json=req).json()
    totals = res["totals"]

    for key, val in totals.items():
        assert not math.isnan(val), f"Total {key} is NaN"
        assert not math.isinf(val), f"Total {key} is Inf"
        assert val >= 0, f"Total {key} is negative ({val})"

    for item in res["items"]:
        for m_key, m_val in item["macros"].items():
            assert not math.isnan(m_val), f"Macro {m_key} in item {item['name']} is NaN"
            assert not math.isinf(m_val), f"Macro {m_key} in item {item['name']} is Inf"
            assert m_val >= 0, f"Macro {m_key} in item {item['name']} is negative"


def test_allergy_exclusion_invariant():
    """Invariant §4.5: Allergies must strictly exclude forbidden foods."""
    allergic_profile = dict(
        P1_PROFILE,
        allergies=["tôm", "peanut", "shrimp", "đậu phộng"],
    )
    req = {
        "profile": allergic_profile,
        "seed": 9001,
        "config": "smoke",
    }
    res = client.post("/api/menu/generate", json=req).json()
    for item in res["items"]:
        name_lower = item["name"].lower()
        assert "tôm" not in name_lower, f"Allergen 'tôm' found in {item['name']}"
        assert "shrimp" not in name_lower, f"Allergen 'shrimp' found in {item['name']}"
        assert "peanut" not in name_lower, f"Allergen 'peanut' found in {item['name']}"
        assert "đậu phộng" not in name_lower, f"Allergen 'đậu phộng' found in {item['name']}"


def test_medical_conditions_and_goals_influence_targets():
    """Verify medical conditions adjust targets (e.g. hypertension -> sodium <= 1500mg)."""
    # Hypertension profile
    hyp_profile = dict(P1_PROFILE, medical_conditions=["hypertension"])
    res_hyp = client.post("/api/targets", json=hyp_profile).json()
    assert res_hyp["targets"]["sodium_mg"] == 1500.0

    # Weight loss vs weight gain calories
    lose_profile = dict(P1_PROFILE, goal="LOSE_WEIGHT")
    res_lose = client.post("/api/targets", json=lose_profile).json()
    assert res_lose["targets"]["calories"] < res_lose["tdee"]

    gain_profile = dict(P1_PROFILE, goal="GAIN_WEIGHT")
    res_gain = client.post("/api/targets", json=gain_profile).json()
    assert res_gain["targets"]["calories"] > res_gain["tdee"]


def test_edibility_no_standalone_raw_ingredients():
    """Invariant §4.5: Standalone raw ingredients must not appear in menus."""
    req = {
        "profile": P1_PROFILE,
        "seed": 9001,
        "config": "smoke",
    }
    res = client.post("/api/menu/generate", json=req).json()
    banned_raw = [
        "bột ngọt", "muối ăn", "hạt nêm", "dầu ăn", "mỡ lợn",
        "shortening", "nước mắm", "giấm", "đường cát", "tiêu xay"
    ]
    for item in res["items"]:
        name_lower = item["name"].lower().strip()
        for bad in banned_raw:
            # Standalone match check: name is equal or purely this condiment
            assert name_lower != bad, f"Standalone raw ingredient '{item['name']}' served as a dish"

