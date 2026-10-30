# TASK WEEK 11 — Demo Hardening (Đăng + Cương)

> **Phạm vi:** Chuẩn bị web app demo được trước hội đồng. Không đụng thuật toán DBO/IDBO. Không sửa dataset. Không dịch tự động 15k món. Mục tiêu: user mở web, thấy thực đơn đọc được, không bị lỗi 500, đổi món được.
>
> **Phân công:**
> - **Đăng (UI/frontend):** `app/static/index.html`, `app/static/js/app.js`, `app/static/js/api.js`, `app/static/js/charts.js`
> - **Cương (backend/constraints/swap):** `app/api/schemas.py`, `app/api/services.py`, `app/api/swap.py`, `src/models/dish_category.py`
>
> **File CẤM đụng:** `src/algorithms/*` (DBO/IDBO), `src/utils/nutrition.py` (giữ raise age<18), `src/models/diversity_penalty.py` (giữ MAIN_SLOTS), `data/processed/*.csv`, `src/models/report.py` (KHÔNG import vào app — dịch sai, gắn vào còn tệ hơn để tiếng Anh).

---

## Bước 0 (Cương): Rebase PR #34 lên main, merge

PR #34 (`feat/week10-11-web-grill-and-harden`) đã ổn (swap chạy, 314 test pass). Merge trước khi làm tiếp:

1. `git checkout feat/week10-11-web-grill-and-harden && git rebase origin/main`
2. Conflict chỉ ở `app/main.py` — giữ bản trên main (đã có lifespan), bỏ bản của PR.
3. Chạy `pytest` — phải 314 pass.
4. Merge vào main.

---

## P0 — Phải xong trước demo

### Task 1 (Cương): Chặn hết lỗi 500

**Vấn đề:** Các input sau trả 500 Internal Server Error (user thấy trang lỗi trắng):
- `seed=-1`, `seed=-999999` → `np.random.default_rng` raise `ValueError` (dbo.py:83, swap.py:121)
- `allergies=["a"]`, `["e"]`, `dislikes=["a"]` → pool bị lọc quá hẹp → fallback → lọt `RAW_INGREDIENT` bounds `(0,0)` → `lb must be strictly smaller than ub`
- Swap với `food_ids` chứa id không tồn tại (`ZZZ_999`) → KeyError trong `Menu.decode`
- `old_portions_g` = số âm, 0, `1e9`, hoặc sai độ dài → trả 200 với delta = -19 tỷ kcal

**Cách làm SAI (cấm):**
- ❌ Bắt exception rộng rồi trả 500 (vẫn là 500)
- ❌ Sửa `np.random.default_rng` để nhận số âm (sửa solver — cấm)
- ❌ Bỏ token dị ứng ngắn mà không ghi log (user gõ "tôm" vẫn ok, nhưng "a" thì bỏ im lặng — phải báo)

**Cách làm ĐÚNG:**
1. `schemas.py`: `GenerateIn.seed` và `SwapIn.seed` → `Field(9001, ge=0, le=2**31-1)`. `SwapIn.old_portions_g` thêm `@field_validator`: mỗi phần tử `0 < x <= 1000`, độ dài phải bằng `len(food_ids)` nếu không phải None → sai trả 422.
2. `services.py` `build_profile`: sau khi normalize, loại bỏ token dị ứng/ghét có độ dài <2 sau khi bỏ dấu, và nếu sau khi lọc pool quá nhỏ (<20) → trả 400 "Bộ lọc dị ứng/không thích quá hẹp, không đủ món ứng viên".
3. `swap.py`: trước khi decode, kiểm tra mọi `food_id ∈ food_map`, sai → 400.
4. `services.py` `generate_menu`: bọc `two_tier_optimize` trong `try/except ValueError` → 400 với message rõ ràng (không phải 500).

**File đụng:** `schemas.py`, `services.py`, `swap.py`.
**Tiêu chí hoàn thành:** Chạy lại các case trên → không có mã 5xx nào. Thêm test `test_api_boundary.py` cho `seed=-1`, `allergies=["a"]`, swap id lạ. pytest ≥314 + mới, xanh.

---

### Task 2 (Cương): Whitelist pool — vòng qua dataset nghèo

**Vấn đề:** 15,929 món đa số là SKU Mỹ không đọc được. `Tép gạo` bị coi là STAPLE (tên có "gạo") → 63% menu P2 có Tép gạo làm cơm. ~95% menu có ít nhất 1 món Na=0 (fillna(0) trên NaN). Bánh quy có thể lọt bữa trưa.

**Cách làm SAI (cấm):**
- ❌ Dịch tự động 15k món (sai hệ thống, report.py đã chứng minh)
- ❌ Sửa CSV gốc (cấm)
- ❌ Import `report.py`/`USDA_TO_VI` vào app (dịch sai: bagel→Hành tây, bacon→Xông xô)
- ❌ Whitelist quá nhỏ (<100 món) → pool mỗi slot <20 → fallback → 500

**Cách làm ĐÚNG:**
1. Tạo file mới `data/vn_food_display.json` (overlay, không đụng CSV gốc). Cấu trúc:
   ```json
   {
     "VN_1004": {"name_vi": "Phở bò", "category_vi": "Món nước", "hide": false},
     "USDA_xxx": {"hide": true}
   }
   ```
2. Tuần 1: **whitelist 150-300 món** (lấy từ 526 món VN có sẵn + món USDA an toàn đã kiểm tra). Trong `services.py` `get_food_map()`, sau khi load, lọc chỉ giữ món có trong whitelist (hoặc `hide != true`). Món nào không có `name_vi` thì hiển thị `category_vi` + tên gốc nhỏ.
3. **Bắt buộc đo trước khi commit:** chạy 20 seed × 3 profile (P1/P2/P3), đảm bảo mỗi slot pool ≥20 (không chạm `min_pool_size=20`), fitness trung bình không tụt >5 điểm so với pool đầy đủ. Nếu pool <20 ở slot nào → mở rộng whitelist slot đó.
4. Loại khỏi whitelist: món có Na=0 (đối với P3), `Tép gạo`, `Dầu cám gạo`, `Dầu ngô`, `Bột khoai lang`, cookie/cake/candy.

**File đụng:** `services.py`, `data/vn_food_display.json` (mới). **Xin phép TV3** nếu cần đụng `src/models/food_selector.py` (ngoài allow-list).
**Tiêu chí hoàn thành:** 20 seed × 3 profile → 0 món tên chứa `BACN`/`USDA_` hiển thị, 0 món Na=0, 0 `Tép gạo` làm cơm, 0 bánh quy bữa trưa, pool không vỡ.

---

### Task 3 (Đăng): UI sạch — đọc được bằng tiếng Việt

**Vấn đề:**
- Badge bữa ăn tiếng Anh (`breakfast/lunch/dinner/snack`) dù form đã tiếng Việt.
- `food_id` (USDA_2403410) hiển thị dưới tên món.
- Không có nút "Thay món" (CSS `.btn-swap` + hàm `apiSwapMenu` có sẵn nhưng không render, `app.js` không import).
- `api.js` không gửi `old_portions_g` khi swap → delta calo phình +503 kcal (gửi đúng thì chỉ +1 kcal).
- Placeholder bệnh lý tiếng Anh (`diabetes, hypertension…`) — user Việt gõ "tăng huyết áp" bị bỏ.

**Cách làm SAI (cấm):**
- ❌ Gọi `get_vietnamese_food_name` từ `report.py` (dịch sai)
- ❌ Đổi tên field JSON trong `MenuItemOut` (làm vỡ `test_frontend_contract.py` — chỉ được THÊM field `name_vi`, không đổi field cũ)
- ❌ Freeze các slot khác khi swap (trái spec tuần 10 — inner IDBO re-opt cả 7 khẩu phần là đúng narrative)

**Cách làm ĐÚNG:**
1. `app.js`: map `breakfast→Sáng`, `lunch→Trưa`, `dinner→Tối`, `snack→Phụ`. Ẩn `food_id` khỏi UI (vẫn giữ trong JSON).
2. `index.html` + `app.js`: render nút "Thay món" cạnh mỗi món, gọi `apiSwapMenu`, gửi kèm `old_portions_g` = `menu.items[].portion_g` (không phải rounded). Hiển thị delta calo sau khi swap.
3. `index.html`: đổi input bệnh lý từ text tự do thành **dropdown chọn sẵn** (Tăng huyết áp / Tiểu đường / Khỏe mạnh) — giá trị gửi lên là `hypertension`/`diabetes`/`healthy`. Alias tiếng Việt đã có ở backend (Task của Cương).
4. Hiển thị `violations` bằng tiếng Việt rõ ràng (nếu có), không để toast "Không có vi phạm" khi thực ra có.

**File đụng:** `index.html`, `app.js`, `api.js`.
**Tiêu chí hoàn thành:** Mở web, tạo thực đơn → không thấy chữ tiếng Anh ở cột bữa, không thấy `USDA_`/`VN_` ID, nút Thay món hoạt động, delta calo hợp lý (<100 kcal khi đổi 1 món), chọn "Tăng huyết áp" → target sodium = 1500.

---

### Task 4 (Cương): Sửa role classification — Tép gạo & bánh quy

**Vấn đề:** `dish_category.py` regex STAPLE khớp "gạo" → `Tép gạo` (tôm nhỏ) thành STAPLE. `\boatmeal\b` khớp "Cookies, oatmeal" → bánh quy thành STAPLE → lọt bữa trưa. `Dầu cám gạo`, `Dầu ngô`, `Bột khoai lang` cũng thành STAPLE.

**Cách làm SAI (cấm):**
- ❌ Xóa các món này khỏi CSV (cấm)
- ❌ Đổi `ROLE_PORTION_BOUNDS` thành [25,350] cho mọi role (mâu thuẫn AGENTS.md §4.7)

**Cách làm ĐÚNG:**
1. Thêm loại trừ TRƯỚC khi kiểm STAPLE: `cookie|cake|candy|pie|waffle|muffin|biscuit` → FRUIT_SNACK (không phải staple).
2. Thêm loại trừ: `dầu|bột|tương|nước mắm|hạt nêm|muối` → RAW_INGREDIENT (không phải món ăn độc lập).
3. Với món VN: dùng `category` trước khi regex tên. `Tép gạo` có category thủy sản → MAIN_PROTEIN (không phải staple).
4. Đảm bảo pool mỗi slot vẫn ≥20 sau khi sửa (chạy đo như Task 2).

**File đụng:** `dish_category.py`.
**Tiêu chí hoàn thành:** Pool lunch_0/dinner_0 có 0 món ngọt/bánh, 0 `Dầu cám gạo`, `Tép gạo` role = main_protein. Thêm test regex. Pool không dưới 20.

---

## P1 — Tuần 2 (nếu còn thời gian)

- **Search sạch:** bỏ dấu + lowercase, khớp word-boundary trên `name_vi`+`aliases`+`name_en`. `q` rỗng trả danh sách curated, không phải `df.head`. (`services.py`)
- **Allergen đa ngôn ngữ:** overlay `allergen_synonyms` (`tôm→shrimp,prawn`, `đậu phộng→peanut,lạc`, `sữa→milk`, `trứng→egg`). Mở rộng `allergies` trong `build_profile` trước khi vào solver. (`services.py` + overlay)
- **Swap bounds theo vai trò:** trong `swap.py`, thay `lb=25, ub=350` cứng bằng `get_role_portion_bounds` theo từng món. (`swap.py`)

---

## Verification checklist (trước khi gọi là xong)

Chạy hết các lệnh sau, phải PASS hết:

```bash
# 1. Test
python -m pytest tests/ -q   # ≥314 pass, 0 fail

# 2. Không còn 500 (chạy script grill trong scripts/ nếu có)
#    age=17 → 422, seed=-1 → 422, allergies=["a"] → 400, swap id lạ → 400

# 3. 20 seed × 3 profile không có món SKU hiển thị, pool không vỡ

# 4. Web: tạo menu → badge tiếng Việt, không có food_id, nút swap hoạt động

# 5. Chọn "Tăng huyết áp" → sodium target = 1500
```

## Cấm claim trên slide

- ❌ "IDBO thắng DBO" (inner_restarts=0 ở mọi lần chạy)
- ❌ "Na an toàn / không ngày nào vượt 2300" (dữ liệu Na đang thủng, ~95% menu có món Na=0)
- ❌ "P2 an toàn tiểu đường" (không có cột sugar)
- ❌ "P3 ăn kiêng muối" (Na thấp là ảo vì fillna(0))
- ✅ Được nói: "P1 là case chính. P2/P3 có giới hạn mapping dữ liệu, chỉ trình bày khi bị hỏi."
