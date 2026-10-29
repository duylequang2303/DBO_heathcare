# Core Algorithm & Source Code Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix critical source-code issues found by the parallel-agent grill: IDBO perturbation/restart mechanisms not activating, universal `[25,350]` portion bounds violating AGENTS.md §4.7, demo script bypassing the §4.4 rounding pipeline, and missing data provenance for `data/processed/`.

**Architecture:** Four independent task groups. Task 1 calibrates IDBO diversity threshold so perturbation/restart fire. Task 2 makes `_check_portion` role-aware using `get_role_portion_bounds`. Task 3 fixes `demo_week8.py` to round → decode → recalc → validate. Task 4 adds provenance metadata for `data/processed/`. No shared mutable state between tasks.

**Tech Stack:** Python 3.12, NumPy, Pytest, pandas, AGENTS.md business rules.

**Spec:** `AGENTS.md` (§4.4, §4.7, §6.3, §8, §12); existing plan `docs/superpowers/plans/2026-10-29-web-backend-grill-and-test.md` (web/API scope — do not duplicate).

## Global Constraints

- Python 3.12 compatibility.
- Comply with all `ENFORCED` rules in `AGENTS.md`:
  - §4.4: Rounding pipeline is continuous → round to 5g → decode → recalc nutrients → validate rounded → report final metrics.
  - §4.7: Do not use `[25,350]` as final bounds for every role; role-aware bounds (STAPLE 100-250, MAIN_PROTEIN 60-180, VEGETABLE 80-220, SOUP 100-350, FRUIT_SNACK 50-200).
  - §6.3: IDBO telemetry (n_perturbations, n_restarts) must be reported and mechanisms must actually fire under diagnostic configuration.
  - §8: `data/processed/` must not be hand-edited without a regeneration script and provenance metadata.
- No regression: All existing 293 pytest tests must continue to pass.
- No silent fallback from IDBO to DBO (§6.2).

## Review Focus

1. **IDBO threshold too high**: default `outer_diversity_threshold=0.28` never triggers with natural swarm diversity ~0.246 → IDBO behaves identically to DBO. Need calibrated threshold so mechanisms activate.
2. **Universal portion bounds**: `PORTION_RANGE = {min: 25, max: 350}` applied to all roles violates §4.7 role-aware bounds in constraint validation.
3. **Demo validates wrong menu**: `demo_week8.py` validates continuous solution then prints rounded values — violates §4.4 pipeline order.
4. **Data provenance**: `data/processed/` CSVs committed without `config.json`/README per §8.

---

### Task 1: Calibrate IDBO activation threshold in two-tier solver

**Files:**
- Modify: `src/algorithms/two_tier_solver.py:43-44`
- Modify: `tests/test_two_tier_solver.py`

**Interfaces:**
- Consumes: `TwoTierConfig.outer_diversity_threshold` default value
- Produces: `outer_diversity_threshold` lowered so natural swarm diversity (~0.246) falls below it, triggering collapse → perturbation/restart.

- [ ] **Step 1: Write failing test**

```python
def test_idbo_mechanism_fires_in_two_tier_diagnostic(food_map_fixture, profile_p1):
    targets = daily_all_targets(profile_p1)
    config = TwoTierConfig(
        outer_algo="idbo",
        outer_n_agents=8,
        outer_max_iter=10,
        inner_algo="idbo",
        inner_n_agents=8,
        inner_max_iter=10,
        diversity_threshold=0.5,
        stagnation_window=2,
        perturbation_rate=1.0,
        restart_rate=1.0,
        seed=8006,
    )
    result = two_tier_optimize(profile_p1, food_map_fixture, targets, config)
    assert result.outer_perturbations > 0 or result.outer_restarts > 0
    assert result.outer_collapse_events > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/test_two_tier_solver.py::test_idbo_mechanism_fires_in_two_tier_diagnostic -v`
Expected: FAIL with `outer_perturbations == 0` and `outer_collapse_events == 0`.

- [ ] **Step 3: Implement threshold calibration in `two_tier_solver.py`**

Change default `outer_diversity_threshold` from `0.28` to `0.50` so natural swarm diversity (~0.246) falls below it, triggering collapse → perturbation/restart. Keep `inner_diversity_threshold` logic intact.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_two_tier_solver.py::test_idbo_mechanism_fires_in_two_tier_diagnostic -v`
Expected: PASS with `outer_perturbations > 0` or `outer_restarts > 0`.

- [ ] **Step 5: Run full solver test suite**

Run: `venv/bin/pytest tests/test_two_tier_solver.py -v`
Expected: All pass.

- [ ] **Step 6: Commit**

```bash
git add src/algorithms/two_tier_solver.py tests/test_two_tier_solver.py
git commit -m "fix(algo): calibrate IDBO outer diversity threshold so mechanisms activate"
```

---

### Task 2: Role-aware portion bounds in constraint validation

**Files:**
- Modify: `src/models/constraints.py:4-5`
- Modify: `src/models/constraints.py:23-34`
- Modify: `src/models/constraints.py:107-113`
- Create: `tests/test_portion_bounds.py`

**Interfaces:**
- Consumes: `get_role_portion_bounds(role)` from `src.models.dish_category`, `classify_dish_role` from `src.models.dish_category`
- Produces: `_check_portion` validates each item against its dish role's bounds instead of universal `[25,350]`, with food_map passed through `validate_menu`.

- [ ] **Step 1: Write failing tests**

```python
def test_check_portion_uses_role_bounds_not_universal():
    from src.models.menu import Menu, Meal, MealType, MenuItem
    from src.models.dish_category import DishRole, classify_dish_role
    from src.models.constraints import _check_portion

    # Staple with 40g: inside universal [25,350] but below STAPLE role bound 100g
    item = MenuItem(food_id="F1", food_name="Com", portion_g=40.0, calories=100.0)
    item.dish_role = DishRole.STAPLE  # set directly for test
    menu = Menu()
    menu.meals[MealType.LUNCH] = Meal(MealType.LUNCH, [item])

    violations = _check_portion(menu)
    assert any("Com" in v and "40" in v for v in violations)

    # Staple with 150g: inside STAPLE role bounds [100,250] — should pass
    item2 = MenuItem(food_id="F2", food_name="Pho", portion_g=150.0, calories=200.0)
    item2.dish_role = DishRole.STAPLE
    menu2 = Menu()
    menu2.meals[MealType.LUNCH] = Meal(MealType.LUNCH, [item2])
    violations2 = _check_portion(menu2)
    assert len(violations2) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/test_portion_bounds.py::test_check_portion_uses_role_bounds_not_universal -v`
Expected: FAIL — `_check_portion` doesn't read `dish_role`, uses universal [25,350], so 40g staple passes.

- [ ] **Step 3: Implement role-aware bounds in `constraints.py`**

Add `dish_role: Optional[DishRole] = None` field to `MenuItem` (in `menu.py` if needed) OR pass `food_map` to `_check_portion`/`validate_menu` and classify role per item. Use `get_role_portion_bounds(role)` when role known, fall back to `PORTION_RANGE` when unknown.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_portion_bounds.py -v`
Expected: All pass.

- [ ] **Step 5: Run constraint tests**

Run: `venv/bin/pytest tests/test_constraints.py tests/test_menu.py -v`
Expected: All pass (no regression).

- [ ] **Step 6: Commit**

```bash
git add src/models/constraints.py src/models/menu.py tests/test_portion_bounds.py
git commit -m "fix(constraints): role-aware portion bounds per AGENTS.md §4.7"
```

---

### Task 3: Fix demo script rounding pipeline (AGENTS.md §4.4)

**Files:**
- Modify: `scripts/demo_week8.py:108-110`

**Interfaces:**
- Consumes: `round_portions`, `decode_result`, `validate_menu` from existing modules
- Produces: Demo decodes rounded menu and validates rounded menu, not continuous.

- [ ] **Step 1: Write failing test / verification script**

```python
# Inline verification in demo: after rounding, decode rounded portions and validate
rounded_portions = round_portions(res.best_portions_g, step=5)
menu = decode_result(res.best_food_ids, rounded_portions, food_map, profile.meal_counts)
violations = validate_menu(menu, profile, targets)
# Print violations from rounded menu, not continuous
```

- [ ] **Step 2: Run demo to verify current behavior**

Run: `./venv/bin/python scripts/demo_week8.py --outer-iter 5 --outer-agents 6 --inner-iter 5 --inner-agents 6 --seed 42`
Expected: Currently prints continuous portions and validates continuous menu (wrong per §4.4).

- [ ] **Step 3: Fix demo to round → decode → validate**

Change lines 108-110: use `rounded_portions` for `decode_result`, then `validate_menu` on the rounded menu. Print violations and fitness from rounded menu.

- [ ] **Step 4: Run demo to verify fix**

Run: `./venv/bin/python scripts/demo_week8.py --outer-iter 5 --outer-agents 6 --inner-iter 5 --inner-agents 6 --seed 42`
Expected: Prints rounded portions, validates rounded menu, no nutrient NaN/negative.

- [ ] **Step 5: Commit**

```bash
git add scripts/demo_week8.py
git commit -m "fix(demo): round-then-decode-then-validate pipeline per AGENTS.md §4.4"
```

---

### Task 4: Add data provenance metadata for data/processed/

**Files:**
- Create: `data/processed/config.json`
- Create: `data/processed/PROVENANCE.md`
- Modify: `scripts/preprocess_data.py` (if regeneration script exists — verify first)

**Interfaces:**
- Consumes: None
- Produces: Provenance metadata documenting how `merged_food_nutrition.csv` and `cleaned_food_nutrition.csv` were generated, per AGENTS.md §8.

- [ ] **Step 1: Verify regeneration script exists**

Run: `ls scripts/preprocess_data.py`
Expected: File exists.

- [ ] **Step 2: Create `data/processed/config.json`**

```json
{
  "regeneration_script": "scripts/preprocess_data.py",
  "source": "data/raw/vietnamese_food_composition.csv + USDA",
  "generated_at": "2026-10-29",
  "row_count_merged": <count>,
  "row_count_cleaned": <count>,
  "columns": ["food_id","food_name","category","meal_type","serving_size_g","calories","protein_g","carbs_g","fat_g","fiber_g","sodium_mg","calcium_mg","iron_mg","vitamin_c_mg","source","name_en"],
  "notes": "USDA kJ values converted to kcal (/4.184). No total_sugar column present."
}
```

- [ ] **Step 3: Create `data/processed/PROVENANCE.md`**

Document per AGENTS.md §8: no hand-edits without regeneration script, source data, transformation steps, known limitations (missing total sugar).

- [ ] **Step 4: Verify tests still pass**

Run: `venv/bin/pytest tests/test_menu.py tests/test_data_integrity.py -v`
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add data/processed/config.json data/processed/PROVENANCE.md scripts/preprocess_data.py
git commit -m "docs(data): add provenance metadata for data/processed/ per AGENTS.md §8"
```

---

### Task 5: Whole-branch regression & final verification

**Files:**
- None (verification only)

- [ ] **Step 1: Run complete test suite**

Run: `venv/bin/pytest -q`
Expected: 293 tests pass, 0 failures.

- [ ] **Step 2: Run solver-specific tests**

Run: `venv/bin/pytest tests/test_two_tier_solver.py tests/test_idbo.py tests/test_dbo.py -v`
Expected: All pass.

- [ ] **Step 3: Run demo smoke test**

Run: `./venv/bin/python scripts/demo_week8.py --outer-iter 5 --outer-agents 6 --inner-iter 5 --inner-agents 6 --seed 42`
Expected: No negative/NaN nutrients, rounded menu validates, deterministic with seed 42.

- [ ] **Step 4: Commit final verification**

```bash
git add -A
git commit -m "test(regression): full suite passes after source hardening"
```

---

**Plan complete.** This plan covers core algorithm & source code issues outside the existing web backend plan. Please review: does it capture what you want?