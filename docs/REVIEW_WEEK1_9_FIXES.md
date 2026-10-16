# REVIEW & FIX REPORT - TUAN 1 DEN TUAN 9

## Baseline

- Source snapshot: branch `main`, commit reported by uploaded archive: `9ca8e4e0b8c616d785d6964eecce8d7c6183f334`.
- Initial suite: 193 tests passed.
- Final suite: 195 tests passed.
- Regression demos executed: week 3, week 4, week 5-6, week 7 (DBO and IDBO), week 8, week 9 (P1 and P3).

## Fixes implemented

### 1. Evidence-backed medical constraints

- Added sodium validation for profiles containing `hypertension`.
- The sodium rule uses the real `sodium_mg` field from the merged dataset.
- Added regression tests proving that hypertension enforces the configured sodium limit and that a healthy profile is not incorrectly subjected to the hypertension-specific rule.

### 2. Diabetes/sugar limitation made explicit

- The merged dataset has no total-sugar nutrient field.
- The previous implementation used `carbs * 0.15` but presented it as actual sugar. This value is now explicitly named and documented as an estimate/proxy.
- The proxy is not used to claim medical safety.
- Slide claims such as "safe for diabetes" were removed.

### 3. Rounded portions are the reported portions

- Week 9 demo, experiment, and multi-option generator now decode, calculate nutrients, and validate using the 5 g rounded portions.
- This prevents reporting values from the continuous solution while showing a different rounded menu.

### 4. IDBO activation telemetry

- `TwoTierResult` now exposes perturbation and restart counts for the outer solver and final inner solver.
- Week 8 and week 9 experiment outputs include these counters.
- This makes it possible to explain identical DBO/IDBO results instead of claiming an improvement when IDBO mechanisms did not activate.

### 5. Demo/report correctness

- Fixed the contradictory message that printed "100% valid" even when violations existed.
- Labels now respect the requested number of days instead of always saying seven days.
- The first/last-day wording is dynamic.
- README no longer hard-codes an obsolete test count.

### 6. Week 8-9 slides

- Rebuilt week 9 figures from the tracked CSV files.
- Corrected the profile values to P1 90.68, P2 79.27, and P3 88.09.
- Corrected calorie deviation wording: P2 is 5.59%, so not all profiles are below 4%.
- Removed unsupported claims of universal adaptability, diabetes safety, and AHA compliance.
- Added honest interpretation of sodium and fiber limitations.
- Updated automated-test count to 195/195.

## Important remaining limitations

1. The dataset needs a trustworthy total-sugar field before the system can enforce a diabetes-specific sugar constraint.
2. Serving bounds remain global (25-350 g) and should later be replaced by food-group or serving-specific ranges.
3. Existing full week 8-9 benchmark CSV files were retained as historical results. Because the medical validation and rounded reporting rules changed, a new full benchmark should be run before using the numbers as final clinical evidence.
4. DBO and IDBO may remain identical when perturbation/restart mechanisms do not activate. This is a result to report, not hide.
5. The system is a technical decision-support prototype, not a substitute for assessment by a qualified health professional.

## Commands used for regression

```bash
python -m pytest -q
python scripts/demo_week3.py
python scripts/demo_week4.py --function sphere --dim 5 --n-agents 6 --max-iter 5 --seed 42 --log-every 1
python scripts/demo_week5_6.py --function sphere --dim 5 --n-agents 6 --max-iter 5 --seed 42 --log-every 1
python scripts/demo_week7.py --algo dbo --max-iter 5 --n-agents 6 --seed 42 --seed-sampler 7000
python scripts/demo_week7.py --algo idbo --max-iter 5 --n-agents 6 --seed 42 --seed-sampler 7000
python scripts/demo_week8.py --outer-iter 2 --outer-agents 4 --inner-iter 2 --inner-agents 4 --seed 8003
python scripts/demo_week9.py --profile p1 --algo idbo --days 2 --outer-iter 2 --outer-agents 4 --inner-iter 2 --inner-agents 4 --seed 9001
python scripts/demo_week9.py --profile p3 --algo idbo --days 2 --outer-iter 2 --outer-agents 4 --inner-iter 2 --inner-agents 4 --seed 9001
```

## Recommended next work

- Add a verified total-sugar source and re-run P2.
- Add serving bounds by food category.
- Run an IDBO ablation study with activation counters.
- Run the complete week 8-9 benchmarks again and regenerate all CSV/figures/slides from one pipeline.
