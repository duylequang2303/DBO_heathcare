# Force Push để Clean GitHub Remote

## ⚠️ CẢNH BÁO QUAN TRỌNG

**Force push sẽ GHI ĐÈ lịch sử trên GitHub remote!**
- Tất cả files lớn đã xóa ở local sẽ biến mất trên GitHub
- Nếu có người khác đang work trên repo này, họ sẽ gặp conflict
- Không thể undo (trừ khi có backup)

## Chuẩn Bị

1. **Backup branch trên GitHub** (quan trọng!):
   - Vào https://github.com/duylequang2303/DBO_heathcare
   - Tạo branch backup từ branch hiện tại
   - Hoặc chạy: `git push origin experiment/dbo-idbo-ablation:backup-before-cleanup`

2. **Kiểm tra local đã clean**:
   ```bash
   git log --oneline -3
   # Phải thấy: "chore: Optimize repo for AI/Copilot (<50MB)"
   
   git ls-files | xargs du -ch | tail -1
   # Phải thấy: ~14M total
   ```

## Cách 1: Force Push Branch Hiện Tại (Recommended)

```bash
cd /home/duyle/coding/DBO_heathcare

# Đảm bảo đang ở branch đúng
git checkout experiment/dbo-idbo-ablation

# Tạo backup trên remote TRƯỚC KHI force push
git push origin experiment/dbo-idbo-ablation:backup-before-force-push

# Force push branch này
git push --force-with-lease origin experiment/dbo-idbo-ablation

# --force-with-lease: an toàn hơn --force
# Nó sẽ FAIL nếu có ai đó đã push commits mới lên remote
```

## Cách 2: Force Push Main Branch

```bash
# Merge vào main trước
git checkout main
git merge experiment/dbo-idbo-ablation

# Backup main trên remote
git push origin main:backup-main-before-force

# Force push main
git push --force-with-lease origin main
```

## Cách 3: Force Push Tất Cả Branches

```bash
# Backup toàn bộ
git push origin --all --tags

# Force push all branches
git push --force-with-lease origin --all
```

## Verify Sau Khi Push

1. **Vào GitHub kiểm tra**:
   ```
   https://github.com/duylequang2303/DBO_heathcare
   ```

2. **Kiểm tra dung lượng repo**:
   - Vào: Settings → (scroll xuống) → Repository size
   - Phải thấy: < 50MB

3. **Kiểm tra files đã mất**:
   - data/raw/comprehensive_foods_usda.csv → PHẢI MẤT ✓
   - experiments/ablation_dbo_idbo/*.csv → PHẢI MẤT ✓
   - docs/reports/*.docx → PHẢI MẤT ✓
   - docs/slides/*.pptx → PHẢI MẤT ✓

4. **Clone về test**:
   ```bash
   cd /tmp
   git clone https://github.com/duylequang2303/DBO_heathcare.git test-clone
   cd test-clone
   du -sh .
   # Phải < 50MB
   ```

## Lệnh Đầy Đủ (Copy & Paste)

```bash
#!/bin/bash
cd /home/duyle/coding/DBO_heathcare

# 1. Verify local clean
echo "📊 Local repo size:"
git ls-files | xargs du -ch | tail -1

# 2. Backup trên remote
echo ""
echo "📦 Creating backup on GitHub..."
git push origin experiment/dbo-idbo-ablation:backup-before-force-push-$(date +%Y%m%d)

# 3. Force push
echo ""
echo "🚀 Force pushing clean repo..."
git push --force-with-lease origin experiment/dbo-idbo-ablation

echo ""
echo "✅ DONE! Check GitHub:"
echo "   https://github.com/duylequang2303/DBO_heathcare"
```

## Nếu Gặp Lỗi

### Lỗi: "failed to push some refs"
**Nguyên nhân**: Remote có commits mới

**Giải pháp**: Dùng `--force` thay vì `--force-with-lease`
```bash
git push --force origin experiment/dbo-idbo-ablation
```

### Lỗi: "Updates were rejected"
**Nguyên nhân**: Branch protected

**Giải pháp**: 
1. Vào GitHub: Settings → Branches
2. Tắt "Branch protection" tạm thời
3. Push lại
4. Bật lại protection

## Sau Khi Force Push Thành Công

### Cho người khác update
Nếu có người khác đang work trên repo:

```bash
# Họ cần:
git fetch origin
git reset --hard origin/experiment/dbo-idbo-ablation

# HOẶC
git pull --rebase --force
```

### Giảm dung lượng .git trên remote
GitHub tự động chạy `git gc` sau vài phút.
Nếu muốn xóa ngay, vào:
- Settings → (scroll xuống) → Danger Zone
- Click "Manage" bên cạnh "Repository size"

## Kết Quả Mong Đợi

✅ GitHub repo < 50MB  
✅ Files lớn đã biến mất trên remote  
✅ AI/Copilot có thể clone dễ dàng  
✅ Code vẫn chạy được  
✅ Có backup branch để restore nếu cần  

