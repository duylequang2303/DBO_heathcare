# Hướng Dẫn Giảm Dung Lượng Project < 50MB

## Hiện trạng
- **Tổng dung lượng**: 833MB (với venv)
- **Git tracked files**: 37MB
- **Source code**: ~2MB
- **Vấn đề**: data (19MB), docs (18MB), experiments (51MB), venv (330MB), .git (82MB)

## Giải pháp

### 🎯 Tùy chọn 1: "Lite" Repository (Recommended) - ~15-20MB

Giữ code + sample data, loại bỏ files lớn không cần thiết.

**Bước 1: Cập nhật .gitignore**
```bash
# Thêm vào .gitignore
data/raw/comprehensive_foods_usda.csv
docs/reports/*.docx
docs/slides/*.pptx
docs/slides/*.pdf
patches/*.patch
patches/*.bundle
experiments/*/
!experiments/*/*.md
!experiments/*/*.txt
venv/
.git/
*.zip
*.7z*
```

**Bước 2: Xóa files khỏi Git history (CẨNTHẬN!)**
```bash
# Backup trước
git branch backup-before-cleanup

# Xóa files lớn khỏi Git history
git filter-branch --tree-filter 'rm -f data/raw/comprehensive_foods_usda.csv' HEAD
git filter-branch --tree-filter 'rm -rf docs/reports/*.docx' HEAD
git filter-branch --tree-filter 'rm -rf docs/slides/*.pptx' HEAD

# Cleanup Git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

**Bước 3: Dùng Git LFS cho files lớn**
```bash
git lfs install
git lfs track "*.csv"
git lfs track "*.docx"
git lfs track "*.pptx"
git add .gitattributes
```

**Kết quả**: ~15-20MB (code + small data samples)

---

### 🎯 Tùy chọn 2: "Micro" Repository - ~2-5MB

Chỉ giữ source code, loại bỏ tất cả data/docs/experiments.

**Thực hiện**:
```bash
# 1. Tạo .gitignore mới
cat > .gitignore << 'GITIGNORE'
__pycache__/
*.pyc
.env
venv/
.vscode/
.DS_Store

# Loại bỏ hoàn toàn
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
*.png
*.jpg
GITIGNORE

# 2. Xóa từ Git
git rm -r --cached data/ docs/ experiments/ patches/
git commit -m "chore: Remove large files to reduce repo size"

# 3. Cleanup Git history nếu muốn giảm .git size
git gc --aggressive --prune=now
```

**Kết quả**: ~2-5MB (pure code)

---

### 🎯 Tùy chọn 3: Giữ nguyên, dùng .gitignore tốt hơn (Safest)

Không xóa gì, chỉ đảm bảo files không cần thiết không vào Git.

**Cập nhật .gitignore**:
```bash
# Đã có
venv/
__pycache__/
*.pyc

# Thêm
*.zip
*.7z*
*.patch
*.bundle
.ai_base_commit
latest_*

# Optional: Không commit experiment outputs
experiments/*/paired_runs.csv
experiments/*/summary.csv
experiments/*/*.png
experiments/*/*.json
```

**Clone "shallow" khi cần**:
```bash
# Chỉ lấy commit mới nhất
git clone --depth 1 <repo-url>

# Kết quả: Giảm ~50% .git size
```

---

## So sánh các tùy chọn

| Tùy chọn | Dung lượng | Code | Data | Docs | Experiments | Rủi ro |
|----------|-----------|------|------|------|-------------|--------|
| Lite     | ~15-20MB  | ✓    | Sample | README | Summary | Thấp |
| Micro    | ~2-5MB    | ✓    | ✗    | ✗    | ✗       | Trung bình |
| Shallow  | ~40MB     | ✓    | ✓    | ✓    | ✓       | Không có |

## Khuyến nghị

**Cho submission/deployment**:
→ Dùng **Tùy chọn 1 (Lite)** hoặc **Tùy chọn 2 (Micro)**

**Cho development**:
→ Dùng **Tùy chọn 3 (Shallow clone)** + .gitignore tốt

## Lệnh nhanh - Xóa files không cần commit

```bash
cd /home/duyle/coding/DBO_heathcare

# Xóa files binary không nên trong Git (safe)
rm -f *.zip *.7z* 
rm -f latest_changes.patch* latest_changes.files.txt
rm -f .ai_base_commit

# Kiểm tra files đang staged
git status

# Nếu có files không mong muốn
git reset HEAD <file>
git restore <file>

# Dung lượng sau cleanup
du -sh .
```

## Lưu ý quan trọng

1. **Backup** trước khi xóa files khỏi Git history
2. **Data** lớn nên dùng Git LFS hoặc external storage
3. **Docs** binary (.docx, .pptx) nên lưu ở Google Drive/SharePoint
4. **venv/** không bao giờ commit (dùng requirements.txt)
5. **.git/** size lớn → dùng `git gc --aggressive`

