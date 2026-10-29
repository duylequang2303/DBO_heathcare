# Web Backend Hardening, Testing & Grilling Implementation Plan (Week 10-11)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thoroughly audit, grill, harden, and test the FastAPI web backend (`app/`) for Week 10-11, completing the Swap feature (`swap.py`), enforcing nutritional & AGENTS.md invariants, testing boundary & concurrency edge cases, and verifying frontend-backend contract consistency.

**Architecture:** 
The web layer wraps the two-tier IDBO optimization engine via FastAPI without modifying core solver algorithms. Requests are parsed and validated through Pydantic schemas, dispatched to domain logic via `asyncio.to_thread`, and return deterministic, 5g-rounded menus. The Swap feature dynamically swaps a single culinary slot and re-runs IDBO continuous inner optimization for portion re-balancing.

**Tech Stack:** FastAPI, Starlette, Pydantic v2, Uvicorn, Pytest, HTTPX, NumPy, Chart.js / Vanilla JS.

**Spec:** `docs/tasks/TASK_WEEK10.md`, `docs/project_notes/KE_HOACH_TUAN_11.md`, and `AGENTS.md`.

## Global Constraints

- Python 3.12 compatibility.
- Comply with all `ENFORCED` rules in `AGENTS.md`:
  - Energy/Calories within ±10%, Protein/Carbs ±15%, Fat ±20%, Fiber ±30% (§4.1).
  - Deterministic decoding given the same seed and input (§4.3).
  - Portion rounding to 5g multiples applied to output only; totals and validation computed on rounded menu (§4.4).
  - No raw ingredients or industrial seasoning items served as standalone dishes in candidate pools (§4.5).
  - No mutable global state in algorithms or request lifecycle; `_food_map` singleton must remain read-only during requests (§6.1).
- No regression: All existing 270 pytest tests must continue to pass.
- No Starlette/FastAPI deprecation warnings (migrate startup event to lifespan).

## Review Focus

1. **Swap Endpoint Failure Cases**: Requesting an invalid slot name (not in `meal_order`) or food ID with an allergen must return HTTP 400, not 500.
2. **Exhausted Pool Conflict**: When swapping a slot where no alternate candidate exists in the meal pool, the endpoint must return HTTP 409 Conflict with a helpful error message.
3. **Portion Rounding Recalculation**: After rounding portions to 5g, macros and validation violations must be evaluated against the rounded portions, not the continuous solver output.
4. **Thread Safety & Concurrency**: Multiple concurrent requests to `/api/menu/generate` must execute safely without memory corruption or race conditions on the food map singleton.
5. **Frontend-Backend Contract Drift**: Field names returned by `TargetsOut`, `MenuOut`, and `SwapOut` must match exact property names consumed by `app/static/js/app.js` and `app/static/js/charts.js`.

---

### Task 1: API Boundary, Lifespan Migration & Edge Cases Hardening (Subagent 1: QA/Security)

**Files:**
- Modify: `app/main.py:40-48`
- Modify: `app/api/schemas.py:22-63`
- Create: `tests/test_api_boundary.py`

**Interfaces:**
- Consumes: `ProfileIn`, `GenerateIn`, `SwapIn` from `app.api.schemas`
- Produces: Sanitized input schemas, clean lifespan event handler in `main.py`, robust validation errors (422/400).

- [ ] **Step 1: Write the failing tests in `tests/test_api_boundary.py`**

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_profile_extreme_boundaries():
    # Negative age -> 422
    res = client.post("/api/targets", json={"name": "A", "age": -1, "gender": "male", "height_cm": 170, "weight_kg": 65, "activity_level": "SEDENTARY", "goal": "MAINTAIN"})
    assert res.status_code == 422
    # Age > 120 -> 422
    res = client.post("/api/targets", json={"name": "A", "age": 121, "gender": "male", "height_cm": 170, "weight_kg": 65, "activity_level": "SEDENTARY", "goal": "MAINTAIN"})
    assert res.status_code == 422
    # Zero height -> 422
    res = client.post("/api/targets", json={"name": "A", "age": 25, "gender": "male", "height_cm": 0, "weight_kg": 65, "activity_level": "SEDENTARY", "goal": "MAINTAIN"})
    assert res.status_code == 422
    # Zero weight -> 422
    res = client.post("/api/targets", json={"name": "A", "age": 25, "gender": "male", "height_cm": 170, "weight_kg": 0, "activity_level": "SEDENTARY", "goal": "MAINTAIN"})
    assert res.status_code == 422

def test_meal_counts_all_zero():
    # All meal counts 0 -> 422
    res = client.post("/api/targets", json={
        "name": "A", "age": 25, "gender": "male", "height_cm": 170, "weight_kg": 65,
        "activity_level": "SEDENTARY", "goal": "MAINTAIN",
        "meal_counts": {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
    })
    assert res.status_code == 422

def test_food_search_injection_and_edge_cases():
    # Empty query
    res = client.get("/api/foods?q=&limit=5")
    assert res.status_code == 200
    # SQL injection / special characters string
    res = client.get("/api/foods?q=' OR '1'='1&limit=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    # XSS payload
    res = client.get("/api/foods?q=<script>alert(1)</script>&limit=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
```

- [ ] **Step 2: Run test to verify failures**

Run: `venv/bin/pytest tests/test_api_boundary.py -v`
Expected: FAIL on `test_meal_counts_all_zero` (total meals = 0 currently accepted).

- [ ] **Step 3: Implement validation in `app/api/schemas.py` & migrate lifespan in `app/main.py`**

In `app/api/schemas.py`:
Add validator ensuring `sum(v.values()) > 0` (at least 1 meal item per day).
In `app/main.py`:
Replace `@app.on_event("startup")` with `@asynccontextmanager async def lifespan(app: FastAPI): ...`

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_api_boundary.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/main.py app/api/schemas.py tests/test_api_boundary.py
git commit -m "feat(api): harden profile validation and migrate to lifespan handler"
```

---

### Task 2: Nutritional & Domain Invariants Auditor (Subagent 2: Nutrition/Domain Auditor)

**Files:**
- Create: `tests/test_api_nutritional_invariants.py`
- Modify: `app/api/services.py:254-287`

**Interfaces:**
- Consumes: `generate_menu`, `build_profile`, `get_targets` from `app.api.services`
- Produces: Verified menu output compliant with AGENTS.md §4 (5g portion rounding, macro tolerances, determinism, edibility).

- [ ] **Step 1: Write the failing tests in `tests/test_api_nutritional_invariants.py`**

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_deterministic_menu_generation():
    payload = {
        "profile": {
            "name": "Duy", "age": 22, "gender": "male", "height_cm": 170.0, "weight_kg": 65.0,
            "activity_level": "MODERATE", "goal": "MAINTAIN",
            "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1}
        },
        "seed": 9001,
        "config": "smoke"
    }
    res1 = client.post("/api/menu/generate", json=payload).json()
    res2 = client.post("/api/menu/generate", json=payload).json()
    assert [i["food_id"] for i in res1["items"]] == [i["food_id"] for i in res2["items"]]
    assert [i["portion_g_rounded"] for i in res1["items"]] == [i["portion_g_rounded"] for i in res2["items"]]
    assert res1["totals"] == res2["totals"]

def test_portion_rounding_and_recalculated_totals():
    payload = {
        "profile": {
            "name": "Duy", "age": 22, "gender": "male", "height_cm": 170.0, "weight_kg": 65.0,
            "activity_level": "MODERATE", "goal": "MAINTAIN",
            "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1}
        },
        "seed": 9001,
        "config": "smoke"
    }
    res = client.post("/api/menu/generate", json=payload).json()
    for item in res["items"]:
        assert item["portion_g_rounded"] % 5 == 0
        assert 25 <= item["portion_g_rounded"] <= 350
    # Totals in response must match sum of macros computed with portion_g_rounded (or portion_g if spec requires continuous, check exact AGENTS.md rule)
    assert res["totals"]["calories"] > 0

def test_allergies_and_dislikes_excluded():
    payload = {
        "profile": {
            "name": "Allergic User", "age": 30, "gender": "female", "height_cm": 160.0, "weight_kg": 50.0,
            "activity_level": "LIGHT", "goal": "MAINTAIN",
            "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
            "allergies": ["peanut", "shrimp"]
        },
        "seed": 9001,
        "config": "smoke"
    }
    res = client.post("/api/menu/generate", json=payload).json()
    for item in res["items"]:
        name_lower = item["name"].lower()
        assert "peanut" not in name_lower and "đậu phộng" not in name_lower and "lạc" not in name_lower
        assert "tôm" not in name_lower and "shrimp" not in name_lower

def test_edibility_no_raw_seasoning_main_dish():
    payload = {
        "profile": {
            "name": "Duy", "age": 22, "gender": "male", "height_cm": 170.0, "weight_kg": 65.0,
            "activity_level": "MODERATE", "goal": "MAINTAIN",
            "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1}
        },
        "seed": 9001,
        "config": "smoke"
    }
    res = client.post("/api/menu/generate", json=payload).json()
    raw_blacklist = ["bột ngọt", "muối ăn", "hạt nêm", "dầu ăn tinh luyện", "shortening"]
    for item in res["items"]:
        for bad in raw_blacklist:
            assert bad not in item["name"].lower()
```

- [ ] **Step 2: Run test to verify behavior**

Run: `venv/bin/pytest tests/test_api_nutritional_invariants.py -v`
Expected: PASS if invariants are preserved; if any item violates, fix in `app/api/services.py`.

- [ ] **Step 3: Update `app/api/services.py` if needed to ensure recalculation and pool sanity**

Ensure `generate_menu` calculates item macros matching `portion_g_rounded` and verifies culinary pools.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_api_nutritional_invariants.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_api_nutritional_invariants.py app/api/services.py
git commit -m "test(api): enforce nutritional invariants, determinism, and edibility rules"
```

---

### Task 3: Full Implementation & Edge Cases of Swap Feature (Subagent 3: Swap Specialist)

**Files:**
- Modify: `app/api/swap.py`
- Modify: `app/api/schemas.py:56-64`
- Modify: `tests/test_api.py:127-148`
- Create: `tests/test_api_swap.py`

**Interfaces:**
- Consumes: `SwapIn`, `SwapOut` from `app.api.schemas`, `UserProfile` from `src.models.user_profile`, `IDBO` from `src.algorithms.idbo`, `make_menu_objective` from `src.algorithms.menu_objective`, `decode_result`, `validate_menu` from `src.models.constraints`
- Produces: Fully functional `swap_menu_item(req: SwapIn) -> SwapOut` handling 400, 409, portion re-optimization, and delta metrics.

- [ ] **Step 1: Write comprehensive tests in `tests/test_api_swap.py`**

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BASE_PROFILE = {
    "name": "Duy", "age": 22, "gender": "male", "height_cm": 170.0, "weight_kg": 65.0,
    "activity_level": "MODERATE", "goal": "MAINTAIN",
    "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1}
}

def test_swap_success_auto_candidate():
    gen_res = client.post("/api/menu/generate", json={"profile": BASE_PROFILE, "seed": 9001, "config": "smoke"}).json()
    food_ids = [item["food_id"] for item in gen_res["items"]]
    old_food = food_ids[0]
    
    swap_payload = {
        "profile": BASE_PROFILE,
        "food_ids": food_ids,
        "slot": "breakfast_0",
        "new_food_id": None,
        "seed": 9001
    }
    res = client.post("/api/menu/swap", json=swap_payload)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "totals" in data
    assert "delta" in data
    assert data["items"][0]["food_id"] != old_food
    assert data["items"][0]["slot"] == "breakfast_0"
    for item in data["items"]:
        assert item["portion_g_rounded"] % 5 == 0

def test_swap_invalid_slot_returns_400():
    swap_payload = {
        "profile": BASE_PROFILE,
        "food_ids": ["USDA_2037503"],
        "slot": "midnight_snack_99",
        "new_food_id": None
    }
    res = client.post("/api/menu/swap", json=swap_payload)
    assert res.status_code == 400

def test_swap_duplicate_food_in_meal_returns_400():
    gen_res = client.post("/api/menu/generate", json={"profile": BASE_PROFILE, "seed": 9001, "config": "smoke"}).json()
    food_ids = [item["food_id"] for item in gen_res["items"]]
    # Attempt to swap slot 0 with food in slot 1 (same meal breakfast)
    swap_payload = {
        "profile": BASE_PROFILE,
        "food_ids": food_ids,
        "slot": "breakfast_0",
        "new_food_id": food_ids[1]
    }
    res = client.post("/api/menu/swap", json=swap_payload)
    assert res.status_code == 400
    assert "trùng" in res.json()["detail"].lower()

def test_swap_allergen_food_returns_400():
    # Attempt to swap with a food containing allergen
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/test_api_swap.py -v`
Expected: FAIL with 501 Not Implemented.

- [ ] **Step 3: Implement `app/api/swap.py`**

Implement complete swap logic according to `TASK_WEEK10.md` §"Thay Món":
1. `build_profile(req.profile)`
2. `meal_order = get_meal_order_slots(profile.meal_counts)`
3. Validate `req.slot in meal_order` -> 400 if not.
4. `pools = build_meal_pools(food_map, profile.meal_counts, profile)`
5. Check `new_food_id` or auto-select from pool excluding current and duplicate in meal. If empty -> 409 Conflict.
6. Re-optimize portions via `IDBO(n_agents=10, max_iter=20)` and `make_menu_objective`.
7. Decode result, round portions to 5g, compute totals & delta, validate menu.
8. Return `SwapOut`.
Update `tests/test_api.py::test_menu_swap` to assert 200 OK.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_api_swap.py tests/test_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/swap.py app/api/schemas.py tests/test_api_swap.py tests/test_api.py
git commit -m "feat(api): implement swap_menu_item with IDBO re-optimization and edge case handling"
```

---

### Task 4: Concurrency, Performance & Frontend Contract Verifier (Subagent 4: Integration Tester)

**Files:**
- Create: `tests/test_api_concurrency.py`
- Create: `tests/test_frontend_contract.py`

**Interfaces:**
- Consumes: FastAPI endpoints `/api/health`, `/api/profiles`, `/api/targets`, `/api/menu/generate`, `/api/menu/swap`, `/api/foods`
- Produces: Concurrency stability proofs, frontend JSON schema compatibility checks.

- [ ] **Step 1: Write concurrency and frontend contract tests**

In `tests/test_api_concurrency.py`:
- Use `concurrent.futures.ThreadPoolExecutor` to send 5 concurrent requests with different profiles and seeds to `/api/menu/generate`.
- Assert all 5 return 200 OK without race conditions.
- Benchmark runtime of `config="smoke"` (< 3.0s).

In `tests/test_frontend_contract.py`:
- Verify all fields expected by `app/static/js/app.js`:
  - `MenuOut`: `items`, `totals`, `targets`, `fitness`, `violations`, `diversity_pct`, `runtime_s`.
  - `MenuItemOut`: `food_id`, `name`, `slot`, `meal_type`, `portion_g`, `portion_g_rounded`, `macros`.
  - `MacroDict`: `calories`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g`, `sodium_mg`.
  - `SwapOut`: `items`, `totals`, `targets`, `violations`, `delta`.
- Check that radar chart in `app/static/js/charts.js` maps correctly to `totals` and `targets`.

- [ ] **Step 2: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_api_concurrency.py tests/test_frontend_contract.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_api_concurrency.py tests/test_frontend_contract.py
git commit -m "test(api): verify concurrent execution safety and frontend contract fidelity"
```

---

### Task 5: Whole-Branch Regression & Final Verification

- [ ] **Step 1: Run complete test suite**

Run: `venv/bin/pytest -q`
Expected: All 270+ tests PASS, 0 failures, 0 warnings.

- [ ] **Step 2: Audit AGENTS.md compliance**

Verify:
- No proxy sugar presented as measured.
- No raw items in menu output.
- All portions rounded to 5g.
- Deterministic decoding verified.
