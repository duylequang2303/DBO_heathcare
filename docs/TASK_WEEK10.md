# Kế Hoạch Tuần 10 — Tích Hợp IDBO Vào Web: Tạo Thực Đơn, Hiển Thị Dinh Dưỡng, Thay Món

Nhóm: Lê Quang Duy (trưởng nhóm) · Đặng Nguyễn Minh Đăng · Hồ Trung Cương

> **Trích đề cương Tuần 10:** *"Tích hợp IDBO; tạo thực đơn, hiển thị dinh dưỡng, thay món."*
> Tuần 8–9 đã xong solver 2 tầng (mixed-integer), 7-day planner, đa profile bệnh lý và diversity.
> Tuần 10 **không viết lại thuật toán** — chỉ đưa solver ra khỏi CLI thành **API + giao diện web**.

---

## Tổng Quan Lộ Trình (3 tuần cuối)

| Tuần | Nội dung đề cương | Đầu ra chính |
| :--- | :--- | :--- |
| **10** | Tích hợp IDBO; tạo thực đơn, hiển thị dinh dưỡng, thay món | FastAPI + UI web, API generate/swap |
| 11 | Kiểm thử hệ thống, tổng hợp thực nghiệm, chỉnh báo cáo | Test E2E, bảng tổng hợp, sửa Word |
| 12 | Hoàn thiện báo cáo, hướng dẫn, demo, chuẩn bị bảo vệ | Báo cáo cuối, slide, video demo |

---

## Mục Tiêu Khoa Học Tuần 10

1. Bọc IDBO (qua `two_tier_optimize`) thành **service API** tái sử dụng, không sửa lõi thuật toán.
2. **Tạo thực đơn** từ hồ sơ người dùng: nhập thông tin → tính mục tiêu → chạy solver → trả menu.
3. **Hiển thị dinh dưỡng** trực quan: bảng từng món, tổng ngày, % đạt target, radar, cảnh báo vi phạm.
4. **Thay món** tại một vị trí bữa ăn, tối ưu lại khẩu phần, cập nhật dinh dưỡng tức thời.
5. Bảo toàn **tính tái lập** (seed), **làm tròn gram 5g chỉ ở output**, và **mọi con số lấy từ solver**.

---

## Kiến Trúc Hệ Thống (một tiến trình, một cổng)

```
┌───────────────────────────────────────────────────────────┐
│  Trình duyệt (HTML + CSS + JS + Chart.js)                  │
└───────────────────────────┬───────────────────────────────┘
                            │ fetch /api/...
┌───────────────────────────▼───────────────────────────────┐
│  FastAPI (app/main.py)                                      │
│   - StaticFiles("/")  → app/static                          │
│   - /api/targets, /api/menu/generate, /api/menu/swap ...    │
└───────────────────────────┬───────────────────────────────┘
                            │ (asyncio.to_thread)
┌───────────────────────────▼───────────────────────────────┐
│  services.py  — cầu nối tới lõi đã có (không viết lại)      │
│   two_tier_optimize → decode_result → validate_menu         │
│   daily_all_targets, build_meal_pools, round_portions       │
└───────────────────────────────────────────────────────────┘
```

**Vì sao 1 tiến trình FastAPI phục vụ cả API lẫn static:**
- Môi trường preview chỉ expose **một cổng** → tránh CORS và cấu hình proxy.
- Một lệnh `uvicorn` là chạy được, dễ demo.

> Nếu tách frontend dev server riêng (Vite/…) thì **bắt buộc** cấu hình proxy
> `'/api' → http://localhost:<backend>` và thêm `allowedHosts: ['.monkeycode-ai.live']`.
> Mặc định tuần này chọn cách một cổng.

---

## Cấu Trúc Thư Mục Mới

```
app/
  __init__.py
  main.py               # tạo FastAPI app, mount static, gắn router
  api/
    __init__.py
    schemas.py          # Pydantic request/response
    services.py         # bridge tới lõi (Duy)
    routes.py           # định nghĩa endpoint (Duy)
    swap.py             # logic thay món (Cương)
  static/
    index.html
    css/styles.css
    js/api.js           # gọi API
    js/app.js           # form + render menu + swap
    js/charts.js        # radar / progress (Đăng)
tests/
  test_api.py           # TestClient (không cần mạng)
docs/
  TASK_WEEK10.md
  BaoCao_Tuan10.docx
```

**Phụ thuộc mới (`requirements.txt`):**

```
fastapi
uvicorn[standard]
pydantic
httpx
```

---

## Hợp Đồng API (chốt trước khi code)

| Method | Endpoint | Ý nghĩa |
| :--- | :--- | :--- |
| GET | `/api/health` | kiểm tra service sống |
| GET | `/api/profiles` | 3 preset P1/P2/P3 (tái dùng `get_profile` từ `generate_options_week9.py`) |
| POST | `/api/targets` | nhận hồ sơ → trả BMR/TDEE/calo/macro (`daily_all_targets`) |
| POST | `/api/menu/generate` | chạy `two_tier_optimize` → trả menu + dinh dưỡng + vi phạm |
| POST | `/api/menu/swap` | thay món 1 slot → tối ưu lại gram → trả menu mới + delta |
| GET | `/api/foods?q=&limit=` | tìm món trong DB (cho thay món thủ công) |

**Schema chính (`app/api/schemas.py`):**

```python
class ProfileIn(BaseModel):
    name: str
    age: int = Field(ge=0, le=120)
    gender: Literal["male", "female"]
    height_cm: float = Field(gt=0, le=250)
    weight_kg: float = Field(gt=0, le=400)
    activity_level: Literal["SEDENTARY", "LIGHT", "MODERATE", "ACTIVE", "VERY_ACTIVE"]
    goal: Literal["LOSE_WEIGHT", "MAINTAIN", "GAIN_WEIGHT"]
    meal_counts: dict[str, int] = {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1}
    medical_conditions: list[str] = []
    allergies: list[str] = []
    dislikes: list[str] = []

class GenerateIn(BaseModel):
    profile: ProfileIn
    seed: int = 9001
    config: Literal["smoke", "web", "full"] = "web"

class SwapIn(BaseModel):
    profile: ProfileIn
    food_ids: list[str]
    slot: str                 # vd "lunch_0"
    new_food_id: str | None = None   # None → tự chọn món khác cùng pool
    seed: int = 9001
```

**Menu JSON trả về (rút gọn khỏi `TwoTierResult` + `Menu`):**

```json
{
  "items": [
    {"food_id": "1234", "name": "Cơm gạo lứt", "slot": "lunch_0",
     "portion_g": 180.0, "portion_g_rounded": 180,
     "macros": {"calories": 245.0, "protein_g": 5.1, "carbs_g": 51.0,
                "fat_g": 1.8, "fiber_g": 3.2, "sodium_mg": 5.0}}
  ],
  "totals": {"calories": 2480.0, "protein_g": 128.0, "carbs_g": 305.0,
             "fat_g": 72.0, "fiber_g": 30.0, "sodium_mg": 1900.0},
  "targets": {"calories": 2450.0, "protein_g": 130.0, "...": "..."},
  "fitness": 88.4,
  "violations": [],
  "diversity_pct": 92.9
}
```

---

## Luồng Nghiệp Vụ Chính

```
(1) Nhập hồ sơ  ──POST /api/targets──────►  hiển thị BMR/TDEE/calo/macro
(2) Tạo thực đơn ─POST /api/menu/generate─►  bảng món + tổng dinh dưỡng + radar
(3) Thay món    ──POST /api/menu/swap────►  cập nhật 1 dòng + delta + radar
(4) (tuỳ chọn)  ──3 phương án A/B/C──────►  so sánh & chọn
```

---

## Thay Món — Cương (trọng tâm tuần 10)

**Mục tiêu:** đổi 1 món trong 1 slot, giữ nguyên `meal_type`, không trùng trong cùng bữa,
không dính dị ứng/dislike; tối ưu lại khẩu phần và trả delta.

```python
def swap_menu_item(profile, food_ids, food_map, targets, slot, new_food_id=None, seed=9001):
    meal_order = get_meal_order_slots(profile.meal_counts)
    pools = build_meal_pools(food_map, profile.meal_counts, profile)
    pool = pools[slot]                       # đã lọc meal_type + dị ứng
    idx = meal_order.index(slot)
    if new_food_id is None:
        new_food_id = next(fid for fid in pool
                           if fid != food_ids[idx]
                           and fid not in _used_in_meal(food_ids, meal_order, slot))
    if new_food_id not in pool:
        raise ValueError("Món không nằm trong pool hợp lệ cho bữa này")

    new_ids = list(food_ids); new_ids[idx] = new_food_id
    inner_obj = make_menu_objective(profile, new_ids, food_map, targets)
    res = IDBO(n_agents=15, max_iter=25).optimize(inner_obj, dim=len(new_ids),
                                                  lb=25.0, ub=350.0, seed=seed)
    menu = decode_result(new_ids, res.best_x, food_map, profile.meal_counts)
    return menu, validate_menu(menu, profile, targets)
```

**Edge case bắt buộc xử lý:**

| Tình huống | Hành vi |
| :--- | :--- |
| `slot` không thuộc `meal_order` | `400 Bad Request` |
| Hết món khác trong pool | `409 Conflict` + gợi ý món gần nhất |
| `new_food_id` trùng món đang có trong bữa | `400` |
| `new_food_id` vi phạm dị ứng | `400` (đã lọc ở pool, nhưng vẫn chặn) |
| Đổi xong | trả `delta` calo/macro + danh sách vi phạm mới |

---

## Hiển Thị Dinh Dưỡng — Đăng

- **Bảng món:** tên, bữa, gram (cột `portion_g` gốc **và** gram 5g), calo/protein/carb/fat/fiber/natri.
- **Tổng ngày + % đạt target:** thanh tiến độ cho từng chỉ số (calo ±10%, macro ±15/20/30%).
- **Radar dinh dưỡng (Chart.js):** tỷ lệ % đạt target theo 5–6 chỉ số chính.
- **Cảnh báo:** hiển thị badge các vi phạm từ `validate_menu()` (đỏ/vàng).
- **Nút "Thay món"** ngay trên từng dòng → gọi `/api/menu/swap`.

---

## Hiệu Năng & An Toàn

| Vấn đề | Giải pháp |
| :--- | :--- |
| `load_food_db()` 15.929 món | nạp **một lần** (lazy singleton) khi app khởi động, không load mỗi request |
| Solver chậm | config web rút gọn (`outer_iter=25`, `inner_iter=25`, `n_agents=10`); chạy trong `asyncio.to_thread` để không block event loop |
| Input xấu | validate Pydantic (biên tuổi/cân nặng/height, enum) |
| Lộ bí mật | dự án thuần tính toán, **không** nhúng API key/LLM |
| Sai khẩu phần hiển thị | `round_portions(x, step=5)` **chỉ ở output**, optimizer giữ số liên tục |

---

## Bảo Toàn Tái Lập & Số Liệu

- Mọi số trên UI **lấy từ kết quả solver**, không bịa, không estimate.
- Seed mặc định `9001`; cho phép người dùng nhập seed để tái lập.
- Gram lẻ **không** xuất hiện trên bảng/Word — luôn in 2 dòng (gốc / 5g).
- Dùng đúng module diversity đã hợp nhất (`diversity_penalty(..., meal_order=...)`).

---

## Phân Công Tuần 10

| Thành viên | Việc chính | Nhánh |
| :--- | :--- | :--- |
| **Lê Quang Duy** | `app/main.py`, `services.py`, `routes.py`; mount static một cổng; tích hợp `two_tier_optimize`; Mục 1,3 Word T10 | `261017-feat-week10-api` |
| **Đặng Nguyễn Minh Đăng** | Frontend `static/*` (form, bảng món, radar, tiến độ); số liệu + Mục 2 Word T10 | `261017-feat-week10-ui` |
| **Hồ Trung Cương** | `app/api/swap.py` (thay món) + edge cases; `tests/test_api.py`; Mục 4 Word T10 | `261017-feat-week10-swap` |

---

## Checklist Nghiệm Thu Tuần 10

- [ ] `uvicorn app.main:app` chạy 1 lệnh, mở được UI ở một cổng.
- [ ] `/api/targets` trả đúng BMR/TDEE/macro cho P1, P2, P3.
- [ ] `/api/menu/generate` trả menu hợp lệ: `len(food_ids) == sum(meal_counts)`, gram trong `[25, 350]`.
- [ ] `/api/menu/swap` đổi đúng slot, không trùng món trong bữa, dinh dưỡng cập nhật + delta đúng.
- [ ] UI hiển thị bảng món, tổng dinh dưỡng, radar, và cảnh báo vi phạm.
- [ ] `python -m pytest tests/` xanh toàn bộ (gồm `tests/test_api.py`).
- [ ] **Không** commit `experiments/` CSV/PNG.
- [ ] Gram hiển thị luôn làm tròn bội số 5g.
- [ ] Chạy thử preview bằng skill `deploy-website`.

---

## Timeline 7 Ngày

| Ngày | Duy | Đăng | Cương |
| :--- | :--- | :--- | :--- |
| 1–2 | Khung FastAPI + services + `/health`, `/targets` | Khung HTML/CSS + form hồ sơ | `swap_menu_item()` + unit test |
| 3–4 | `/menu/generate` + mount static | Bảng món + radar + nối `/targets` | `/menu/swap` endpoint + edge cases |
| 5 | Tinh chỉnh config web + threadpool | Nối `/generate`, thanh tiến độ | Review swap, `test_api.py` |
| 6–7 | Tổng hợp Word T10 + PR merge `main` | Mục 2 + số liệu | Mục 4 + test cuối |

---

## Khi Kết Quả Chưa Như Kỳ Vọng

1. **Không** xóa kết quả hoặc bịa số.
2. Nếu solver chậm/quá tải web → giảm `outer_iter`/`inner_iter` hoặc thêm cache theo `(profile, seed)`.
3. Nếu swap lạc hậu (món mới vẫn trùng bữa) → tăng phạm vi pool hoặc thêm ràng buộc cứng khi decode.
4. Ghi rõ giới hạn + đề xuất cải tiến trong phần Thảo luận của Word T10.

---

## Không Bao Giờ Sửa

- `src/algorithms/dbo.py`, `idbo.py` — **signature `optimize()`**.
- `src/algorithms/behaviors.py` — 4 hành vi gốc.
- `src/models/menu.py` — API `encode()` / `decode()`.
- `src/algorithms/two_tier_solver.py` — interface `two_tier_optimize()`.

---

## Tài Liệu Tham Khảo

1. `docs/TASK_WEEK8_9.md` — nền tảng solver 2 tầng, 7-day, đa profile, diversity.
2. `README.md` — lộ trình 12 tuần, mô hình bài toán, ràng buộc, hàm mục tiêu.
3. FastAPI Documentation — https://fastapi.tiangolo.com
4. J. Xue and B. Shen, "Dung beetle optimizer," *The Journal of Supercomputing*, vol. 79, 2023.
5. M. Amiri et al., "Personalized Flexible Meal Planning," *JMIR Formative Research*, vol. 7, e46434, 2023.
