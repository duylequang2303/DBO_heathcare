# Implementation Plan: Tuần 10 — Tích hợp IDBO vào Web API

## Overview

Mục tiêu: Xây dựng FastAPI backend và giao diện web để tạo thực đơn, hiển thị dinh dưỡng, và thay món sử dụng solver IDBO đã có.

Phạm vi công việc:
- Xây dựng REST API với FastAPI
- Tạo giao diện web HTML/CSS/JS
- Tích hợp với solver two_tier_optimize hiện có
- Implement chức năng swap món
- Viết tests và documentation

## Task Dependency Graph

```json
{
  "waves": [
    ["1"],
    ["2"],
    ["3"],
    ["4", "5"],
    ["6"],
    ["7"],
    ["8"],
    ["9", "10"],
    ["11"],
    ["12"],
    ["13"],
    ["14"]
  ]
}
```

## Tasks

### 1. Setup FastAPI project structure

Tạo cấu trúc thư mục app/, setup FastAPI application, cấu hình dependencies.

**Acceptance Criteria:**
- Thư mục app/ với cấu trúc con (api/, static/) được tạo
- File app/main.py với FastAPI() instance
- requirements.txt được cập nhật với fastapi, uvicorn, pydantic, httpx

#### 1.1 Tạo thư mục app/ với cấu trúc con (api/, static/)

Tạo các thư mục: app/, app/api/, app/static/, app/static/css/, app/static/js/

#### 1.2 Tạo app/main.py với FastAPI app instance

Tạo file app/main.py với FastAPI() instance cơ bản và __init__.py

#### 1.3 Cập nhật requirements.txt với dependencies

Thêm dependencies mới: fastapi, uvicorn[standard], pydantic, httpx vào requirements.txt

### 2. Implement API schemas and models
**Depends on:** 1

Định nghĩa Pydantic schemas cho request/response.

**Acceptance Criteria:**
- File app/api/schemas.py với ProfileIn, GenerateIn, SwapIn
- Response schemas: TargetsOut, MenuOut, MenuItem, MacroNutrition
- Tất cả schemas có type hints và validation

#### 2.1 Tạo app/api/schemas.py với request schemas

Tạo file app/api/schemas.py với các Pydantic models: ProfileIn, GenerateIn, SwapIn và __init__.py

#### 2.2 Định nghĩa response schemas

Thêm response schemas: TargetsOut, MenuOut, MenuItem, MacroNutrition vào schemas.py

### 3. Implement core API services
**Depends on:** 2

Xây dựng services.py để bridge với solver hiện có.

**Acceptance Criteria:**
- File app/api/services.py với các functions cốt lõi
- food_db được load một lần duy nhất (singleton pattern)
- Các functions: get_profiles(), calculate_targets(), generate_menu(), round_and_validate()

#### 3.1 Tạo app/api/services.py với food_db singleton loader

Tạo services.py với singleton pattern để load food database một lần duy nhất

#### 3.2 Implement get_profiles() service (P1/P2/P3 presets)

Implement hàm get_profiles() trả về 3 profile mẫu P1, P2, P3

#### 3.3 Implement calculate_targets() service

Implement hàm calculate_targets(profile) sử dụng các hàm từ src/utils/nutrition.py

#### 3.4 Implement generate_menu() service

Implement hàm generate_menu() gọi two_tier_optimize từ src/algorithms/two_tier_solver.py

#### 3.5 Implement round_and_validate() helper

Implement hàm round_and_validate() để làm tròn portions và validate menu

### 4. Implement API routes
**Depends on:** 3

Tạo các endpoint API cho health check, targets, menu generation.

**Acceptance Criteria:**
- File app/api/routes.py với APIRouter
- Endpoints: GET /api/health, GET /api/profiles, POST /api/targets, POST /api/menu/generate
- POST /api/menu/generate sử dụng asyncio.to_thread

#### 4.1 Tạo app/api/routes.py với router setup

Tạo file app/api/routes.py với APIRouter instance

#### 4.2 Implement GET /api/health endpoint

Implement endpoint GET /api/health trả về {"status": "ok"}

#### 4.3 Implement GET /api/profiles endpoint

Implement endpoint GET /api/profiles gọi get_profiles()

#### 4.4 Implement POST /api/targets endpoint

Implement endpoint POST /api/targets nhận ProfileIn và trả về TargetsOut

#### 4.5 Implement POST /api/menu/generate endpoint

Implement endpoint POST /api/menu/generate với asyncio.to_thread để không block event loop

### 5. Implement swap functionality
**Depends on:** 3

Xây dựng logic thay món và endpoint tương ứng.

**Acceptance Criteria:**
- File app/api/swap.py với swap_menu_item() function
- Endpoints: GET /api/foods, POST /api/menu/swap
- Error handling cho edge cases: slot invalid, pool exhausted, duplicates

#### 5.1 Tạo app/api/swap.py với swap_menu_item() function

Tạo file app/api/swap.py với hàm swap_menu_item() để thay đổi một món trong menu

#### 5.2 Implement GET /api/foods endpoint

Implement endpoint GET /api/foods?q=&limit= để search food database

#### 5.3 Implement POST /api/menu/swap endpoint

Implement endpoint POST /api/menu/swap nhận SwapIn và trả về menu mới

#### 5.4 Handle edge cases

Thêm error handling cho các trường hợp: slot không hợp lệ, hết món trong pool, món trùng

### 6. Mount static files and integration
**Depends on:** 4

Cấu hình FastAPI để serve static files từ một cổng.

**Acceptance Criteria:**
- StaticFiles được mount trong app/main.py
- Routers được include vào main app
- Server khởi động thành công với uvicorn

#### 6.1 Mount StaticFiles trong app/main.py

Import và mount StaticFiles từ fastapi.staticfiles trong app/main.py

#### 6.2 Include routers

Include APIRouter từ routes.py và swap.py vào main FastAPI app

#### 6.3 Test server khởi động

Test chạy uvicorn app.main:app --reload và verify server start thành công

### 7. Implement frontend structure
**Depends on:** 6

Xây dựng HTML/CSS/JS cơ bản cho giao diện.

**Acceptance Criteria:**
- File app/static/index.html với form nhập hồ sơ
- File app/static/css/styles.css với layout responsive
- File app/static/js/api.js với fetch wrappers

#### 7.1 Tạo app/static/index.html

Tạo index.html với form nhập hồ sơ người dùng (tuổi, giới tính, chiều cao, cân nặng, etc.)

#### 7.2 Tạo app/static/css/styles.css

Tạo styles.css với layout responsive cho desktop và mobile

#### 7.3 Tạo app/static/js/api.js

Tạo api.js với các wrapper functions để gọi API endpoints

### 8. Implement frontend menu display
**Depends on:** 7

Hiển thị thực đơn, dinh dưỡng, và progress bars.

**Acceptance Criteria:**
- File app/static/js/app.js với event handlers
- Functions: renderTargets(), renderMenu(), renderProgress(), renderViolations()
- UI hiển thị đầy đủ thông tin dinh dưỡng

#### 8.1 Tạo app/static/js/app.js

Tạo app.js với event handlers cho form submission

#### 8.2 Implement renderTargets()

Implement function renderTargets() để hiển thị BMR, TDEE và macro targets

#### 8.3 Implement renderMenu()

Implement function renderMenu() để render bảng thực đơn với thông tin dinh dưỡng

#### 8.4 Implement renderProgress()

Implement function renderProgress() với progress bars cho từng macro

#### 8.5 Implement renderViolations()

Implement function renderViolations() để hiển thị các vi phạm ràng buộc

### 9. Implement nutrition visualization
**Depends on:** 8

Tạo biểu đồ radar nutrition với Chart.js.

**Acceptance Criteria:**
- Chart.js được thêm vào index.html
- File app/static/js/charts.js với setupRadarChart(), updateRadarChart()
- Radar chart hiển thị % đạt target cho các macro

#### 9.1 Thêm Chart.js vào index.html

Thêm script tag để load Chart.js CDN trong index.html

#### 9.2 Tạo app/static/js/charts.js

Tạo charts.js với function setupRadarChart() khởi tạo canvas

#### 9.3 Implement updateRadarChart()

Implement function updateRadarChart() để update chart với dữ liệu dinh dưỡng mới

### 10. Implement swap UI functionality
**Depends on:** 8, 5

Thêm nút thay món và xử lý swap interaction.

**Acceptance Criteria:**
- Nút "Thay món" xuất hiện trên mỗi row của bảng menu
- Function handleSwap() gọi API và update UI
- Hiển thị delta nutrition sau swap

#### 10.1 Thêm nút "Thay món" vào từng dòng menu

Thêm button "Thay món" vào mỗi row của bảng menu trong renderMenu()

#### 10.2 Implement handleSwap()

Implement function handleSwap(slot) để gọi API swap

#### 10.3 Hiển thị delta nutrition sau swap

Hiển thị thông tin chênh lệch dinh dưỡng sau khi swap thành công

#### 10.4 Update UI với menu mới

Update toàn bộ UI (menu, progress, radar) với dữ liệu menu mới

### 11. Write API tests
**Depends on:** 4, 5

Viết tests cho các endpoints API.

**Acceptance Criteria:**
- File tests/test_api.py với pytest fixtures
- Tests cho tất cả endpoints: health, profiles, targets, generate, swap
- Tests bao gồm edge cases

#### 11.1 Tạo tests/test_api.py với TestClient setup

Tạo file tests/test_api.py với pytest fixtures và TestClient

#### 11.2 Test GET endpoints

Viết tests cho endpoints GET /api/health và /api/profiles

#### 11.3 Test POST /api/targets

Viết tests cho endpoint POST /api/targets với các profile P1, P2, P3

#### 11.4 Test POST /api/menu/generate

Viết tests cho endpoint POST /api/menu/generate và validate response structure

#### 11.5 Test POST /api/menu/swap

Viết tests cho endpoint POST /api/menu/swap bao gồm các edge cases

### 12. Performance optimization and config
**Depends on:** 6

Tối ưu hiệu năng và tạo config profiles.

**Acceptance Criteria:**
- Config cho web mode với iterations và agents giảm xuống
- food_db singleton pattern hoạt động đúng
- Optional caching cho profiles

#### 12.1 Tạo config cho web mode

Tạo config dictionary cho web mode với outer_iter=25, inner_iter=25, n_agents=10

#### 12.2 Implement singleton pattern cho food_db

Đảm bảo food_db chỉ được load một lần khi app khởi động

#### 12.3 Add caching nếu cần
**Optional**

Thêm caching cho profile calculations nếu cần thiết

### 13. Documentation and verification
**Depends on:** 11

Tạo tài liệu và verify toàn bộ hệ thống.

**Acceptance Criteria:**
- File docs/BaoCao_Tuan10.docx outline
- Tất cả tests pass
- Manual testing thành công
- Verify deterministic và gram rounding

#### 13.1 Tạo docs/BaoCao_Tuan10.docx outline

Tạo outline báo cáo tuần 10 với các mục chính

#### 13.2 Chạy pytest và verify

Chạy python -m pytest tests/ và verify tất cả tests pass

#### 13.3 Test manual với uvicorn

Khởi động server và test manual các chức năng chính

#### 13.4 Verify deterministic với cùng seed

Verify cùng input và seed cho ra cùng menu (deterministic)

#### 13.5 Verify gram làm tròn 5g

Verify portions được làm tròn bội số 5g trong output hiển thị

### 14. Final integration and demo
**Depends on:** 13

Tích hợp cuối cùng và chuẩn bị demo.

**Acceptance Criteria:**
- Smoke test toàn bộ workflow pass
- Không có nutrient âm, NaN, infinity
- Không có raw ingredients trong output
- Test với cả 3 profiles thành công
- Demo script và screenshots sẵn sàng

#### 14.1 Smoke test toàn bộ flow

Chạy smoke test toàn bộ workflow: nhập hồ sơ → tạo menu → swap món

#### 14.2 Kiểm tra nutrient hợp lệ

Verify không có giá trị dinh dưỡng âm, NaN hoặc infinity trong output

#### 14.3 Verify không có raw ingredients

Verify không có nguyên liệu thô xuất hiện như món độc lập

#### 14.4 Test với 3 profiles

Test hệ thống với cả 3 profiles P1, P2, P3 để đảm bảo hoạt động đúng

#### 14.5 Chuẩn bị demo

Chuẩn bị script demo và chụp screenshots cho báo cáo

## Notes

- Tuân thủ AGENTS.md về không sửa signature của DBO/IDBO
- Không hard-code dữ liệu dinh dưỡng, lấy từ solver
- Làm tròn gram chỉ ở output display, không trong tính toán
- Seed mặc định 9001 cho reproducibility
- Web config: outer_iter=25, inner_iter=25, n_agents=10 (giảm từ 200/200/30)
