#!/bin/bash
# Script giảm dung lượng project xuống < 50MB
# Sử dụng: bash cleanup_to_50mb.sh [lite|micro]

set -e

PROJECT_DIR="/home/duyle/coding/DBO_heathcare"
cd "$PROJECT_DIR"

MODE="${1:-lite}"

echo "=========================================="
echo "  GIẢM DUNG LƯỢNG PROJECT < 50MB"
echo "  Mode: $MODE"
echo "=========================================="
echo ""

# Backup trước
echo "📦 Tạo backup..."
BACKUP_BRANCH="backup-before-cleanup-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP_BRANCH" 2>/dev/null || echo "Branch backup đã tồn tại"
echo "✓ Backup branch: $BACKUP_BRANCH"
echo ""

# Hiển thị dung lượng trước
echo "📊 Dung lượng TRƯỚC:"
du -sh .
echo ""

if [ "$MODE" = "micro" ]; then
    echo "🔧 MODE: MICRO (code-only, ~5-10MB)"
    echo ""
    
    # Xóa khỏi Git (nhưng giữ local)
    echo "1. Xóa data/docs/experiments khỏi Git..."
    git rm -r --cached data/ docs/ experiments/ patches/ 2>/dev/null || true
    
    # Cập nhật .gitignore
    echo "2. Cập nhật .gitignore..."
    cat >> .gitignore << 'GITIGNORE'

# === Cleanup for micro mode ===
data/
docs/
experiments/
patches/
*.zip
*.7z*
*.csv
*.docx
*.pptx
*.pdf
GITIGNORE
    
    echo "3. Commit changes..."
    git add .gitignore
    git commit -m "chore: Reduce repo size to <50MB (micro mode - code only)" || true
    
else
    echo "🔧 MODE: LITE (~20-30MB, giữ sample data)"
    echo ""
    
    # Xóa files lớn
    echo "1. Xóa files lớn không cần thiết..."
    git rm --cached data/raw/comprehensive_foods_usda.csv 2>/dev/null || true
    git rm --cached docs/reports/*.docx 2>/dev/null || true
    git rm --cached docs/slides/*.pptx 2>/dev/null || true
    git rm --cached docs/slides/*.pdf 2>/dev/null || true
    git rm --cached patches/*.patch* 2>/dev/null || true
    
    # Cập nhật .gitignore
    echo "2. Cập nhật .gitignore..."
    cat >> .gitignore << 'GITIGNORE'

# === Cleanup for lite mode ===
data/raw/comprehensive_foods_usda.csv
docs/reports/*.docx
docs/slides/*.pptx
docs/slides/*.pdf
patches/*.patch
patches/*.bundle
experiments/*/paired_runs.csv
experiments/*/summary.csv
experiments/*/*.png
*.zip
*.7z*
GITIGNORE
    
    echo "3. Commit changes..."
    git add .gitignore
    git commit -m "chore: Reduce repo size to <50MB (lite mode)" || true
fi

# Git cleanup
echo ""
echo "4. Git cleanup (gc --aggressive)..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo "✓ Git cleanup done"

# Hiển thị kết quả
echo ""
echo "=========================================="
echo "📊 Dung lượng SAU:"
du -sh .
echo ""
echo "Git tracked files:"
git ls-files | xargs du -ch 2>/dev/null | tail -1 || echo "N/A"
echo ""
echo "=========================================="
echo "✓ HOÀN TẤT"
echo ""
echo "Để hoàn tác: git checkout $BACKUP_BRANCH"
echo "=========================================="

