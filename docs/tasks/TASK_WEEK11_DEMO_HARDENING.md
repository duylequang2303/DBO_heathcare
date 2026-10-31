# TASK WEEK 11 — Demo Hardening (Cookbook cho Đăng + Cương)

> **ĐÃ LÀM SẴN (verify rồi, đừng đụng vào):**
> 1. `schemas.py:24` — `age: Field(ge=18, le=120)` (trước là ge=0 → 500)
> 2. `services.py` — `_MEDICAL_ALIASES` + `_normalize_medical_conditions` ("tăng huyết áp"→Na 1500)
> 3. `services.py` `generate_menu` — chặn snack-only trả 400 (trước là 500 `Missing main-dish slots`)
>
> Verify 3 cái trên: `pytest tests/ -q` phải 314 pass. Nếu đỏ → bạn làm hỏng gì đó, revert.
>
> **File CẤM đụng:** `src/algorithms/*`, `src/utils/nutrition.py`, `src/models/diversity_penalty.py`, `data/processed/*.csv`, `src/models/report.py` (KHÔNG import vào app — dịch sai).

---

## TASK 1 (Cương): Chặn 3 lỗ 500 còn sót — 2 giờ

### 1.1. `seed` âm → 500
**Vấn đề:** `seed=-1` → `np.random.default_rng(-1)` raise ValueError → 500.
**File:** `app/api/schemas.py`, dòng 52 (`GenerateIn.seed`) và dòng 61 (`SwapIn.seed`).
**Sửa đúng:**
```python
# TRƯỚC (SAI):  seed: int = 9001
# SAU (ĐÚNG):   seed: int = Field(9001, ge=0, le=2**31-1)
```
**Verify:** gửi generate với `"seed":-1` → phải trả **422**, không phải 500.

### 1.2. `old_portions_g` rác → delta âm 19 tỷ kcal
**File:** `app/api/schemas.py`, class `SwapIn`. Thêm validator:
```python
    @field_validator("old_portions_g")
    @classmethod
    def validate_old_portions(cls, v):
        if v is None: return v
        for x in v:
            if not (0 < x <= 1000):
                raise ValueError(f"old_portions_g phải trong (0, 1000], nhận được {x}")
        return v
```
**Verify:** swap với `old_portions_g=[-5]` → phải 422.

### 1.3. Swap với `food_ids` chứa id lạ → 500
**File:** `app/api/swap.py`, hàm `swap_menu_item` (dòng 35). Ngay sau `food_map = get_food_map()` thêm:
```python
    for fid in req.food_ids:
        if fid not in food_map:
            raise HTTPException(status_code=400, detail=f"food_id '{fid}' không tồn tại")
```
**Verify:** swap với `food_ids` chứa `"ZZZ_999"` → phải 400.

### 1.4. `allergies=["a"]` → 500 (pool quá hẹp)
**File:** `app/api/services.py`, trong `build_profile`. Trước khi tạo UserProfile, lọc token ngắn:
```python
    allergies = [a for a in pin.allergies if len(str(a).strip()) >= 2]
    dislikes = [d for d in pin.dislikes if len(str(d).strip()) >= 2]
```
Dùng `allergies=allergies, dislikes=dislikes` thay vì `pin.allergies`/`pin.dislikes`.
**Verify:** `allergies=["a"]` → trả **422** (bị chặn bởi validator token rác, không phải 500).

**Tiêu chí TASK 1:** pytest ≥314 pass, KHÔNG có mã 5xx nào với edge cases trên.

---

## TASK 2 (Cương): Whitelist pool — vòng qua dataset nghèo — 1-2 ngày
> Động tác quan trọng nhất. Không dịch 15k món. Chỉ giữ ~200 món đọc được.

### 2.1. Tạo `data/vn_food_display.json` (mới, không đụng CSV)
```json
{
  "VN_1004": {"name_vi": "Phở bò", "category_vi": "Món nước", "hide": false},
  "VN_1011": {"name_vi": "Cơm trắng", "category_vi": "Tinh bột", "hide": false}
}
```
Curate từ 526 món VN trong CSV (lọc `source=vietnamese`), chọn món ăn thật. Mục tiêu 150-300 món, mỗi vai trò ≥30 món.

### 2.2. Lọc trong `services.py` `get_food_map()` (dòng 61-67)
Sau `_food_map = build_food_map(_food_df)` thêm:
```python
        overlay_path = ROOT / "data" / "vn_food_display.json"
        if overlay_path.exists():
            import json
            with open(overlay_path) as f: overlay = json.load(f)
            _food_map = {fid: row for fid, row in _food_map.items()
                         if overlay.get(fid, {}).get("hide", False) is False}
            for fid, row in _food_map.items():
                if fid in overlay:
                    row["name_vi"] = overlay[fid].get("name_vi", row["food_name"])
```

### 2.3. Bắt buộc đo trước khi commit
```python
from app.api.services import get_food_map
print("Pool size:", len(get_food_map()))  # phải ≥300, nếu <300 → mở rộng whitelist
```
Chạy 20 seed × 3 profile: pool mỗi slot ≥20, fitness ≥85, 0 món Na=0, 0 SKU hiển thị.

---

## TASK 3 (Đăng): UI sạch — nửa ngày

### 3.1. Badge tiếng Việt + ẩn food_id
**File:** `app/static/js/app.js` dòng 336-367 (`renderMenu`).
- Thêm `const MEAL_LABELS = { breakfast: 'Sáng', lunch: 'Trưa', dinner: 'Tối', snack: 'Phụ' };`
- Dòng 362: `${mealName}` → `${MEAL_LABELS[mealName] || mealName}`
- Dòng 367: **XÓA HẲN** `<div class="food-id">${item.food_id}</div>`

### 3.2. Nút "Thay món" + gửi `old_portions_g`
- Trong `renderMenu`, mỗi hàng thêm `<button class="btn-swap" data-slot="${item.slot}">Thay món</button>`
- Event listener gọi `apiSwapMenu(profile, foodIds, slot, null, seed, oldPortionsG)` với `oldPortionsG = menuData.items.map(i => i.portion_g)`
- `api.js` `apiSwapMenu`: thêm field `old_portions_g` vào body (hiện chưa gửi → delta +503 kcal)
**Verify:** swap 1 món → delta calo <100 kcal.

### 3.3. Bệnh lý = dropdown (không phải text tự do)
**File:** `index.html`. Thay input text bằng:
```html
<select id="medicalCondition">
  <option value="">Khỏe mạnh</option>
  <option value="hypertension">Tăng huyết áp (giảm muối)</option>
  <option value="diabetes">Tiểu đường (chỉ ghi chú — không có cột đường)</option>
</select>
```
**Verify:** chọn "Tăng huyết áp" → target sodium = 1500.

---

## TASK 4 (Cương): Sửa role classification — 4 giờ
**Vấn đề:** `Tép gạo`→STAPLE (tên có "gạo"), `Cookies, oatmeal`→STAPLE, `Dầu cám gạo`→STAPLE.
**File:** `src/models/dish_category.py`. TRƯỚC dòng 116 (`if STAPLE_PATTERNS.search...`) thêm:
```python
    EXCLUDE_STAPLE = re.compile(r"\b(cookie|cake|candy|pie|waffle|muffin|biscuit|donut)\b", re.I)
    RAW_EXCLUDE = re.compile(r"\b(dầu|bột|tương|nước mắm|hạt nêm|muối|giấm)\b")
    if EXCLUDE_STAPLE.search(name_clean): return DishRole.FRUIT_SNACK
    if RAW_EXCLUDE.search(name_clean): return DishRole.RAW_INGREDIENT
    if source == "vietnamese" and any(k in cat_clean for k in ["thủy sản", "cá", "tôm", "thịt"]):
        return DishRole.MAIN_PROTEIN
```
**Verify:** `classify_dish_role('Tép gạo', 'thủy sản', 'vietnamese')` → `main_protein`. `classify_dish_role('Cookies, oatmeal', 'snacks')` → `fruit_snack`. Pool mỗi slot vẫn ≥20.

---

## Verification cuối (phải PASS hết)
```bash
pytest tests/ -q   # ≥314 pass, 0 fail
# Edge cases: seed=-1→422, allergies=["a"]→200, swap id lạ→400, old_portions_g=[-5]→422
# Web: badge tiếng Việt, không có food_id, nút swap hoạt động, tăng huyết áp→Na=1500
# 20 seed×3 profile: 0 SKU, 0 Na=0, pool≥20, fitness≥85
```

## Cấm claim trên slide
- ❌ "IDBO thắng DBO" (inner_restarts=0 mọi lần)
- ❌ "Na an toàn" (dữ liệu Na đang thủng)
- ❌ "P2 an toàn tiểu đường" (không có cột đường)
- ✅ Được nói: "P1 là case chính. P2/P3 có giới hạn dữ liệu, chỉ trình bày khi bị hỏi."
