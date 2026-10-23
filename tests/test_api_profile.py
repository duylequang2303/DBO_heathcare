"""Meal counts are validated at the API boundary before reaching the solver."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api import routes
from app.api.schemas import GenerateIn, ProfileIn
from app.api.services import PRESET_PROFILES


@pytest.mark.parametrize(
    "counts",
    [
        {},
        {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0},
        {"breakfast": 5, "lunch": 5, "dinner": 5, "snack": 3},
        {"lunch": 1, "snack": 0},
    ],
)
def test_meal_counts_accept_zero_and_inclusive_limits(counts: dict[str, int]) -> None:
    profile = ProfileIn(**{**PRESET_PROFILES["p1"], "meal_counts": counts})
    assert profile.meal_counts == counts
    assert GenerateIn(profile=profile).profile.meal_counts == counts


@pytest.mark.parametrize(
    "counts",
    [
        {"brunch": 1},
        {"brunch": 0},
        {"breakfast": -1},
        {"breakfast": 6},
        {"lunch": -1},
        {"lunch": 6},
        {"dinner": -1},
        {"dinner": 6},
        {"snack": -1},
        {"snack": 4},
    ],
)
def test_invalid_meal_counts_rejected_before_generation(
    counts: dict[str, int], monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = {**PRESET_PROFILES["p1"], "meal_counts": counts}
    with pytest.raises(ValidationError):
        ProfileIn(**profile)

    def unexpected_generate(req: GenerateIn) -> None:
        pytest.fail("Invalid meal counts reached menu generation")

    monkeypatch.setattr(routes, "generate_menu", unexpected_generate)
    app = FastAPI()
    app.include_router(routes.router)
    with TestClient(app) as client:
        response = client.post("/api/menu/generate", json={"profile": profile})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "profile", "meal_counts"]
