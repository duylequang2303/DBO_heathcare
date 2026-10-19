# Kế Hoạch Tối Ưu: Repo < 50MB Cho AI/Copilot

## Mục tiêu
- GitHub repo < 50MB
- AI có thể clone và CHẠY ĐƯỢC
- Giữ code + data cần thiết + khả năng reproduce

## Chiến lược: "Smart Lite"

### ✅ GIỮ LẠI (Essential - ~8MB)
```
src/              364K    ✓ Core algorithms (DBO, IDBO, menu, constraints)
app/              140K    ✓ Web API (tuần 10)
scripts/          716K    ✓ Demo scripts
tests/            592K    ✓ Test suite (205 + 9 tests)
data/processed/   3.0MB   ✓ merged_food_nutrition.csv (CẦN để chạy!)
data/raw/vn*.csv  236K    ✓ Vietnamese food data (nhỏ)
requirements.txt  ~1KB    ✓ Dependencies
README.md         ~50KB   ✓ Documentation
AGENTS.md         ~30KB   ✓ AI guidelines
pytest.ini        ~1KB    ✓ Test config
.gitignore        ~1KB    ✓ Git config
```

### ❌ XÓA KHỎI GIT (Reproducible - ~60MB)
```
data/raw/comprehensive_foods_usda.csv  16MB   ✗ TOO BIG, có thể download lại
experiments/ablation_dbo_idbo/*.csv    ~2MB   ✗ Có thể chạy lại
experiments/ablation_dbo_idbo/*.png    ~200KB ✗ Có thể vẽ lại
experiments/week*/                     ~48MB  ✗ Old results
docs/reports/*.docx                    ~15MB  ✗ Binary files → Google Drive
docs/slides/*.pptx                     ~5MB   ✗ Binary files → Google Drive
docs/slides/*.pdf                      ~2MB   ✗ Binary files
patches/*.patch                        ~3MB   ✗ Old patches
```

### 📝 GIẢI PHÁP CHO DATA LỚN

**comprehensive_foods_usda.csv (16MB):**
```bash
# Option 1: Tạo script download tự động
cat > scripts/download_usda_data.sh << 'SCRIPT'
#!/bin/bash
# Download USDA data nếu chưa có
if [ ! -f data/raw/comprehensive_foods_usda.csv ]; then
    echo "Downloading USDA food data..."
    # wget hoặc curl từ source
    # Hoặc dùng data đã processed (3MB) là đủ!
fi
SCRIPT

# Option 2: Chỉ cần processed data (3MB) là đủ để chạy!
# Raw data chỉ cần khi preprocess lại
```

**Kết luận:** AI chỉ cần `data/processed/merged_food_nutrition.csv` (3MB) là đủ chạy!

## Kết quả Dự kiến

| Thành phần | Trước | Sau | Ghi chú |
|------------|-------|-----|---------|
| Source code | 2MB | 2MB | Giữ nguyên |
| Data | 19MB | 3MB | Chỉ processed |
| Docs | 18MB | 0.5MB | Chỉ .md files |
| Experiments | 51MB | 0.5MB | Chỉ README |
| Patches | 3MB | 0MB | Xóa |
| **TỔNG** | **93MB** | **~6-8MB** | ✓ < 50MB |

## Implementation Steps

```bash
# 1. Backup
git branch backup-smart-lite

# 2. Cập nhật .gitignore
cat >> .gitignore << 'GITIGNORE'

# === Smart Lite: Bỏ files lớn không cần thiết ===
# Raw data (có thể tái tạo từ processed)
data/raw/comprehensive_foods_usda.csv

# Experiment outputs (có thể chạy lại)
experiments/week*/
experiments/ablation_dbo_idbo/*.csv
experiments/ablation_dbo_idbo/*.png
experiments/ablation_dbo_idbo/*.json

# Binary docs (lưu Google Drive)
docs/reports/*.docx
docs/slides/*.pptx
docs/slides/*.pdf
docs/slides/archive/

# Patches (không cần)
patches/

# Temporary
*.zip
*.7z*
.ai_base_commit
latest_*
GITIGNORE

# 3. Xóa từ Git (nhưng GIỮ local)
git rm --cached data/raw/comprehensive_foods_usda.csv
git rm -r --cached experiments/week*/ 
git rm -r --cached experiments/ablation_dbo_idbo/*.csv
git rm -r --cached experiments/ablation_dbo_idbo/*.png
git rm -r --cached docs/reports/*.docx
git rm -r --cached docs/slides/*.pptx
git rm -r --cached docs/slides/*.pdf
git rm -r --cached patches/

# 4. Tạo README cho data download
cat > data/raw/README.md << 'README'
# Raw Data

## comprehensive_foods_usda.csv (16MB)
This file is too large for Git. Download from:
- Original source: [USDA FoodData Central](https://fdc.nal.usda.gov/)
- Or use processed data: `../processed/merged_food_nutrition.csv` (3MB)

**Note:** The processed data is sufficient to run all demos and tests.
Raw data is only needed to re-run preprocessing.
README

# 5. Tạo README cho experiments
cat > experiments/README.md << 'README'
# Experiments

Result files (.csv, .png) are not tracked in Git.
To reproduce:
```bash
python scripts/experiment_dbo_idbo_ablation.py
python scripts/build_pptx_week8_9.py
```
README

# 6. Commit
git add .gitignore data/raw/README.md experiments/README.md
git commit -m "chore: Optimize repo size for AI/Copilot (<50MB)

- Remove large raw data (can download separately)
- Remove experiment outputs (can regenerate)  
- Remove binary docs (use Google Drive)
- Keep processed data (3MB) - sufficient to run all code
- Add download instructions in README files

Repo size: 93MB → ~8MB"

# 7. Git cleanup
git gc --prune=now --aggressive

# 8. Verify
echo "Git tracked size:"
git ls-files | xargs du -ch | tail -1
```

## Verification Commands

```bash
# Test vẫn chạy được
python -m pytest tests/ -v

# Demo vẫn chạy được
python scripts/demo_week7.py

# API vẫn chạy được
python -m uvicorn app.main:app
```

## Hướng Dẫn Cho AI Clone

Tạo file `SETUP_FOR_AI.md`:

```markdown
# Setup Instructions for AI/Copilot

## Quick Start (3 steps)

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd DBO_heathcare
   ```

2. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run tests**
   ```bash
   python -m pytest tests/ -v
   # Expected: 214 tests passed
   ```

## Data

- **Processed data** (3MB) is included: `data/processed/merged_food_nutrition.csv`
- This is sufficient to run all code
- Raw data (16MB) can be downloaded separately if needed

## Run Examples

```bash
# Run demo
python scripts/demo_week7.py

# Run web API
python -m uvicorn app.main:app --reload

# Run experiments
python scripts/experiment_dbo_idbo_ablation.py
```

## Project Structure

```
src/          # Core algorithms (DBO, IDBO, menu optimization)
app/          # Web API (FastAPI)
scripts/      # Demo and experiment scripts
tests/        # Test suite (214 tests)
data/         # Food nutrition database (processed 3MB)
```

See `README.md` and `AGENTS.md` for details.
```

## Kết Luận

✅ Repo < 50MB  
✅ AI có thể clone  
✅ Code chạy được  
✅ Tests pass  
✅ Có hướng dẫn rõ ràng  
✅ Có thể reproduce experiments  

❌ Không mất data quan trọng (có hướng dẫn download)  
❌ Không mất code  
❌ Không làm hỏng Git history  
