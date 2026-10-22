# Setup for AI/Copilot

## Quick Start
```bash
# 1. Clone
git clone <repo-url>
cd DBO_heathcare

# 2. Install
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Test
python -m pytest tests/ -v
# Expected: all tests passed (check count: pytest --co -q)
```

## Data
- Processed data (3MB) included: `data/processed/merged_food_nutrition.csv`
- Sufficient to run all code
- Raw data (16MB) can be downloaded separately if needed

## Examples
```bash
python scripts/demo_week7.py
python -m uvicorn app.main:app
```

See `README.md` for full documentation.
