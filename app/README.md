# DBO Healthcare Web API - Tuần 10

API web cho hệ thống đề xuất thực đơn dinh dưỡng cá nhân hóa sử dụng IDBO solver.

## Kiến trúc

```
FastAPI (single port)
├── /api/*          → REST API endpoints
└── /*              → Static files (HTML/CSS/JS frontend)
```

## API Endpoints

### Health & Info
- `GET /api/health` - Health check
- `GET /api/profiles` - Danh sách 3 preset profiles (P1, P2, P3)

### Menu Generation
- `POST /api/targets` - Tính BMR, TDEE và macro targets
- `POST /api/menu/generate` - Tạo thực đơn mới

### Menu Modification
- `POST /api/menu/swap` - Thay một món trong menu
- `GET /api/foods?q=&limit=` - Tìm kiếm món ăn

## Cách chạy

### Development
```bash
# Cài dependencies
pip install -r requirements.txt

# Chạy server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Hoặc
python app/main.py
```

Truy cập:
- Frontend: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

### Testing
```bash
# Test API endpoints
python -m pytest tests/test_api.py -v

# Test toàn bộ (bao gồm cả tests cũ)
python -m pytest tests/ -v
```

## Cấu hình Solver

Ba modes được hỗ trợ:

| Mode   | Outer Iter | Inner Iter | Agents | Thời gian ước tính |
|--------|-----------|-----------|--------|-------------------|
| smoke  | 5         | 5         | 6      | ~1s               |
| web    | 25        | 25        | 10     | ~3-5s             |
| full   | 100       | 50        | 20/15  | ~30-60s           |

Mặc định sử dụng `web` mode cho ứng dụng web.

## Đặc điểm kỹ thuật

### Backend
- **Framework**: FastAPI
- **Async**: `asyncio.to_thread` cho solver (không block event loop)
- **Singleton**: Food database load một lần duy nhất
- **Validation**: Pydantic schemas với type hints đầy đủ
- **Error handling**: HTTP status codes và error messages rõ ràng

### Frontend
- **Pure HTML/CSS/JS**: Không dùng framework nặng
- **Responsive**: Layout tương thích mobile/desktop
- **Chart**: Chart.js cho radar nutrition
- **Real-time**: AJAX calls cho smooth UX

### Data Flow
1. User nhập profile → Frontend
2. POST /api/menu/generate → Backend
3. two_tier_optimize (IDBO) → Solver
4. Decode + Validate + Round → Processing
5. JSON response → Frontend
6. Render table + chart + progress bars → UI

## Compliance với AGENTS.md

✓ Không sửa signature DBO/IDBO  
✓ Không sửa Menu encode/decode API  
✓ Không hard-code dữ liệu dinh dưỡng  
✓ Food DB singleton pattern  
✓ Gram làm tròn 5g chỉ ở output  
✓ Seed cho reproducibility  
✓ asyncio.to_thread cho non-blocking  

## Files

```
app/
├── __init__.py
├── main.py              # FastAPI app, mount static, startup
├── api/
│   ├── __init__.py
│   ├── schemas.py       # Pydantic request/response models
│   ├── services.py      # Bridge tới solver (singleton, converters)
│   ├── routes.py        # Endpoints: health, profiles, targets, generate
│   └── swap.py          # Swap logic và /api/foods endpoint
└── static/
    ├── index.html       # Main UI
    ├── css/
    │   └── styles.css   # Responsive layout
    └── js/
        ├── api.js       # Fetch wrappers
        ├── app.js       # Main logic (form, render, swap)
        └── charts.js    # Chart.js radar chart
```

## Example Usage

### Tính targets
```bash
curl -X POST http://localhost:8000/api/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Duy",
    "age": 22,
    "gender": "male",
    "height_cm": 170,
    "weight_kg": 65,
    "activity_level": "MODERATE",
    "goal": "MAINTAIN",
    "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
    "medical_conditions": [],
    "allergies": [],
    "dislikes": []
  }'
```

### Tạo menu
```bash
curl -X POST http://localhost:8000/api/menu/generate \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {...},
    "seed": 9001,
    "config": "web"
  }'
```

## Known Limitations

- Food DB load vào memory (~15929 món, ~50MB)
- Solver blocking 3-5s với web config (dùng asyncio.to_thread để không block endpoint khác)
- Chưa có caching cho same profile + seed
- Chưa support multiple days (1 ngày)
- Swap chỉ auto-select món khác, chưa có UI chọn món cụ thể

## Next Steps (Tuần 11)

1. E2E testing toàn bộ workflow
2. Performance benchmarking
3. Báo cáo Word với screenshots
4. Demo video

