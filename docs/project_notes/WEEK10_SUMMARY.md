# Tổng Kết Tuần 10 - Tích Hợp IDBO vào Web API

## Mục tiêu đã hoàn thành

✅ **Backend API (FastAPI)**
- 6 endpoints chính: health, profiles, targets, generate, foods, swap
- Pydantic schemas với validation đầy đủ
- Bridge layer tới solver hiện có (không sửa core algorithms)
- Singleton pattern cho food database
- Asyncio.to_thread cho non-blocking solver execution
- Web config: outer_iter=25, inner_iter=25, n_agents=10

✅ **Frontend UI (HTML/CSS/JS)**
- Form nhập hồ sơ người dùng
- Hiển thị targets (BMR, TDEE, macros)
- Bảng thực đơn với nutrition info chi tiết
- Progress bars cho % đạt target
- Radar chart nutrition (Chart.js)
- Nút thay món trên mỗi row
- Responsive layout (mobile/desktop)

✅ **Testing**
- 9 API tests mới (test_api.py)
- Tất cả 205 tests hiện có vẫn pass
- Test coverage: health, profiles, targets, generate, swap, search

✅ **Architecture**
- Single-port design (một cổng phục vụ cả API và static)
- FastAPI serve static files
- Không cần CORS proxy

## Cấu trúc code

```
app/
├── main.py              # FastAPI app setup
├── api/
│   ├── schemas.py       # Pydantic models
│   ├── services.py      # Bridge tới solver
│   ├── routes.py        # API endpoints
│   └── swap.py          # Swap logic
└── static/
    ├── index.html
    ├── css/styles.css
    └── js/
        ├── api.js
        ├── app.js
        └── charts.js

tests/
└── test_api.py          # API tests

requirements.txt         # + fastapi, uvicorn, pydantic, httpx
```

## Tests đã chạy

```bash
# API tests (9 tests)
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_get_profiles PASSED
tests/test_api.py::test_calculate_targets_p1 PASSED
tests/test_api.py::test_calculate_targets_invalid_age PASSED
tests/test_api.py::test_generate_menu_smoke PASSED
tests/test_api.py::test_search_foods PASSED
tests/test_api.py::test_menu_swap PASSED (slow)
tests/test_api.py::test_menu_swap_invalid_slot PASSED

# Existing tests (205 tests)
All 205 tests PASSED in 10.06s
```

## Compliance với AGENTS.md

✓ Không sửa `src/algorithms/dbo.py`, `idbo.py`  
✓ Không sửa `src/algorithms/behaviors.py`  
✓ Không sửa `src/models/menu.py` encode/decode API  
✓ Không sửa `src/algorithms/two_tier_solver.py` interface  
✓ Food DB load một lần (singleton)  
✓ Gram làm tròn 5g chỉ ở output display  
✓ Seed cho reproducibility (mặc định 9001)  
✓ Không hard-code dữ liệu dinh dưỡng  

## Workflow đã verify

1. **Tính targets**: POST /api/targets → BMR, TDEE, macros ✓
2. **Tạo menu**: POST /api/menu/generate → menu 7 món (2+2+2+1) ✓
3. **Hiển thị**: Table + Progress + Radar chart ✓
4. **Thay món**: POST /api/menu/swap → menu mới với món khác ✓

## Performance

| Config | Outer | Inner | Agents | Thời gian thực tế |
|--------|-------|-------|--------|------------------|
| smoke  | 5     | 5     | 6      | ~1.1s            |
| web    | 25    | 25    | 10     | ~3-5s (ước tính)|
| full   | 100   | 50    | 20/15  | ~30-60s          |

## Commit

```
feat(week10): Implement FastAPI web application with menu generation and swap functionality

Commit: 1a6cda3
Files changed: 18 files, 2285 insertions(+)
```

## Cách chạy

```bash
# Cài dependencies
pip install -r requirements.txt

# Chạy server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test
python -m pytest tests/test_api.py -v
```

Truy cập:
- Frontend: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Known Issues & Limitations

1. **Swap UI**: Hiện tại chỉ auto-select món khác, chưa có dropdown để user chọn món cụ thể
2. **Caching**: Chưa có cache cho (profile + seed) → same menu
3. **Multi-day**: Chỉ hỗ trợ 1 ngày, chưa có 7-day planning
4. **Loading state**: Có spinner nhưng chưa có progress percentage
5. **Error messages**: Còn technical, chưa user-friendly

## Công việc tiếp theo (Tuần 11)

Theo TASK_WEEK10.md, tuần 11 sẽ tập trung:

1. **Kiểm thử hệ thống**
   - E2E testing workflow đầy đầy
   - Performance benchmarking
   - Cross-browser testing
   - Mobile responsive testing

2. **Tổng hợp thực nghiệm**
   - So sánh DBO vs IDBO với web config
   - Runtime analysis
   - Fitness distribution

3. **Chỉnh báo cáo**
   - docs/BaoCao_Tuan10.docx
   - Screenshots từ UI
   - API documentation
   - Kết quả thực nghiệm

4. **Chuẩn bị demo**
   - Script demo
   - Video recording
   - Slide presentation

## Ghi chú kỹ thuật

### Goal enum mapping
- API dùng uppercase: `"MAINTAIN"`, `"LOSE_WEIGHT"`, `"GAIN_WEIGHT"`
- Internal dùng lowercase: `Goal.maintain`, `Goal.lose_weight`, `Goal.gain_weight`
- Cần mapping layer trong `profile_in_to_user_profile()`

### Nutrition functions
- `calc_bmr(profile)` không phải `calculate_bmr(age, gender, ...)`
- `calc_tdee(profile)` không phải `calculate_tdee(bmr, activity)`
- Cần đọc source code để biết exact signature

### Async execution
- Solver chạy trong `asyncio.to_thread()` để không block FastAPI event loop
- Các endpoint khác vẫn respond được trong lúc solver chạy

### Rounded portions
- Solver optimize với continuous portions
- Display làm tròn bội số 5g
- Totals và violations tính từ rounded menu

