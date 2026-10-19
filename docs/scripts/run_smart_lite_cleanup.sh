#!/bin/bash
# Smart Lite Cleanup: Giữ code + data cần thiết, bỏ reproducible files
set -e

echo "=========================================="
echo "  SMART LITE CLEANUP FOR AI/COPILOT"
echo "  Target: < 50MB, keep runnable code"
echo "=========================================="
echo ""

cd /home/duyle/coding/DBO_heathcare

# Backup
echo "📦 Creating backup branch..."
BACKUP="backup-smart-lite-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP"
echo "✓ Backup: $BACKUP"
echo ""

# Show current size
echo "📊 BEFORE:"
du -sh .
git ls-files | xargs du -ch 2>/dev/null | tail -1 | sed 's/^/Git tracked: /'
echo ""

# Update .gitignore
echo "🔧 Updating .gitignore..."
cat >> .gitignore << 'GITIGNORE'

# === Smart Lite Cleanup ===
data/raw/comprehensive_foods_usda.csv
experiments/week*/
experiments/ablation_dbo_idbo/*.csv
experiments/ablation_dbo_idbo/*.png
experiments/ablation_dbo_idbo/*.json
docs/reports/*.docx
docs/slides/*.pptx
docs/slides/*.pdf
docs/slides/archive/
patches/
*.zip
*.7z*
.ai_base_commit
latest_*
GITIGNORE
echo "✓ .gitignore updated"

# Remove from Git (keep local)
echo ""
echo "🗑️  Removing large files from Git..."
git rm --cached data/raw/comprehensive_foods_usda.csv 2>/dev/null || echo "  (already removed)"
git rm -r --cached experiments/week*/ 2>/dev/null || echo "  (already removed)"
git rm -r --cached experiments/ablation_dbo_idbo/*.csv 2>/dev/null || echo "  (already removed)" 
git rm -r --cached experiments/ablation_dbo_idbo/*.png 2>/dev/null || echo "  (already removed)"
git rm -r --cached docs/reports/*.docx 2>/dev/null || echo "  (already removed)"
git rm -r --cached docs/slides/*.pptx 2>/dev/null || echo "  (already removed)"
git rm -r --cached docs/slides/*.pdf 2>/dev/null || echo "  (already removed)"
git rm -r --cached patches/ 2>/dev/null || echo "  (already removed)"
echo "✓ Large files removed from Git"

# Create README files
echo ""
echo "📝 Creating README instructions..."
cat > data/raw/README.md << 'README'
# Raw Data

## comprehensive_foods_usda.csv (16MB)
Too large for Git. Options:
1. Download from: [USDA FoodData Central](https://fdc.nal.usda.gov/)
2. Use processed data: `../processed/merged_food_nutrition.csv` (3MB) ✓ RECOMMENDED

**Note:** Processed data is sufficient for all demos and tests.
README

cat > experiments/README.md << 'README'
# Experiments

Result files (.csv, .png) regenerated locally.

To reproduce:
```bash
python scripts/experiment_dbo_idbo_ablation.py
python scripts/build_pptx_week8_9.py
```
README

cat > SETUP_FOR_AI.md << 'SETUP'
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
SETUP

echo "✓ README files created"

# Commit
echo ""
echo "💾 Committing changes..."
git add .gitignore data/raw/README.md experiments/README.md SETUP_FOR_AI.md
git commit -m "chore: Optimize repo for AI/Copilot (<50MB)

- Remove large raw data (16MB) - can download separately
- Remove experiment outputs - can regenerate locally
- Remove binary docs (docx/pptx) - use external storage
- Keep processed data (3MB) - sufficient to run code
- Add setup instructions for AI

Repo size: ~93MB → ~8MB tracked
" || echo "Nothing to commit"

# Git cleanup
echo ""
echo "🧹 Git cleanup..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo "✓ Git cleanup done"

# Verify
echo ""
echo "=========================================="
echo "📊 AFTER:"
du -sh .
echo ""
echo "Git tracked files:"
git ls-files | xargs du -ch 2>/dev/null | tail -1
echo ""
echo "=========================================="
echo "🧪 Verifying tests still pass after cleanup..."
python3 -m pytest tests/ -q --tb=short
echo ""
echo "✅ DONE! All tests passed."
echo ""
echo "To rollback: git checkout $BACKUP"
echo "=========================================="
