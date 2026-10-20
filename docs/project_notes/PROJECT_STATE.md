# PROJECT_STATE.md — Trạng thái hiện tại của DBO_heathcare

> File này là bản tóm tắt trạng thái có thể kiểm chứng của dự án. AI Coding Agent phải đọc `AGENTS.md`, sau đó đọc file này trước khi sửa code. Trước khi kết thúc mỗi nhiệm vụ, AI phải cập nhật file này bằng kết quả thật đã chạy.

## 1. Repository snapshot

- Project: `DBO_heathcare`
- Main language: Python 3.12
- Current branch: `main`
- Last verified commit: `339051c`
- Last verified date: `2026-10-20`
- Current milestone: **Hoàn thành Tích hợp Menu Realism & Đánh giá Ngưỡng Ứng Viên IDBO (0.28)**

## 2. Verified status

Các mục dưới đây đã được xác minh thực tế trên codebase hiện tại:

- Test suite gần nhất: **`217 passed, 4 warnings in 21s`**
- Lệnh xác minh:

```bash
./venv/bin/pytest -q
# Output: 217 passed, 4 warnings in ~21s
```

### Tuần 10: Web API Integration (COMPLETED)

- **FastAPI backend** đã hoàn thành với 6 endpoints:
  * `GET /api/health` - health check ✓
  * `GET /api/profiles` - 3 preset profiles P1/P2/P3 ✓
  * `POST /api/targets` - tính BMR/TDEE/macros ✓
  * `POST /api/menu/generate` - tạo menu bằng IDBO solver ✓
  * `GET /api/foods` - search food database ✓
  * `POST /api/menu/swap` - thay món và re-optimize ✓

- **Frontend UI** HTML/CSS/JS:
  * Form nhập hồ sơ người dùng ✓
  * Display targets (BMR, TDEE, macros) ✓
  * Bảng thực đơn với nutrition info ✓
  * Progress bars (% đạt target) ✓
  * Radar chart nutrition (Chart.js) ✓
  * Nút thay món trên mỗi row ✓
  * Responsive layout mobile/desktop ✓

- **Architecture**:
  * Single-port design (FastAPI serve cả API và static files) ✓
  * Singleton food_db loader ✓
  * Asyncio.to_thread cho non-blocking solver ✓
  * Web config: outer_iter=25, inner_iter=25, n_agents=10 ✓

- **Testing**:
  * 9 API tests mới trong `tests/test_api.py` ✓
  * Tất cả 205 tests hiện có vẫn pass ✓
  * Generate menu smoke test: ~1.1s ✓

- **Files mới**:
```
app/
├── __init__.py
├── main.py
├── README.md
├── api/
│   ├── __init__.py
│   ├── schemas.py
│   ├── services.py
│   ├── routes.py
│   └── swap.py
└── static/
    ├── index.html
    ├── css/styles.css
    └── js/ (api.js, app.js, charts.js)

tests/test_api.py
WEEK10_SUMMARY.md
tasks.md
```

- Tuần 8-9: Ablation DBO/IDBO đã hoàn thành (xem phần 3).
- Slide tuần 8-9 đã được sinh và kiểm tra.
- Validation natri cho profile tăng huyết áp đã được bổ sung.
- Khẩu phần 5g được dùng để decode, tính lại dinh dưỡng và validation.
- Dataset hiện chưa có trường total sugar đáng tin cậy.

> Nếu bất kỳ mục nào không còn đúng sau thay đổi, AI phải sửa mục đó ngay. Không được giữ số test, đường dẫn hoặc kết luận cũ chỉ vì chúng từng đúng.

## 3. Current findings

### Tuần 10: Web API

- FastAPI serve cả API (`/api/*`) và static files (`/*`) từ một cổng
- Food database (~15929 món) được load một lần khi startup
- Generate menu với web config (~3-5s ước tính, ~1.1s với smoke config)
- Swap món re-optimize với inner solver (IDBO, 15 agents, 25 iterations)
- Gram làm tròn 5g chỉ ở output display, không trong tính toán
- Seed mặc định 9001 cho reproducibility

### DBO và IDBO (Tuần 8-9)

- Benchmark 10 paired seeds (8001–8010) qua 3 cấu hình cho DBO và IDBO kết quả đồng nhất 100% (10/10 hòa, hiệu số Δ = 0.0000).
- Bằng chứng telemetry trực tiếp: `outer_min_diversity` thấp nhất quan sát được là 0.2422 > các ngưỡng `diversity_threshold` (0.001, 0.01, 0.05), do đó điều kiện collapse không xảy ra (0 perturbations, 0 restarts).
- Controlled activation test khẳng định Two-Tier IDBO wiring hoạt động hoàn hảo khi thiết lập ngưỡng thích hợp (0.50).
- Kết quả hiện tại chưa chứng minh IDBO vượt trội hơn DBO trên bài toán tối ưu thực đơn 2 tầng. Nhóm báo cáo trung thực, không suy diễn vượt quá dữ liệu đo được.

### Nutrition and medical claims

- Natri có dữ liệu trực tiếp và có thể được kiểm tra nếu production validation thực sự dùng `sodium_mg`.
- Total sugar chưa có dữ liệu trực tiếp.
- P1/P2/P3 là profile mô phỏng phục vụ benchmark kỹ thuật.
- Không dùng "an toàn y tế", "đạt AHA", "điều trị" hoặc kết luận lâm sàng trong code, CSV, slide hay báo cáo.

### Culinary realism

- Culinary roles, ingredient filtering và realistic portion bounds phải được đánh dấu đúng trạng thái `ENFORCED`, `PARTIAL` hoặc `TARGET` theo `AGENTS.md`.
- Không được tuyên bố đã loại bỏ hoàn toàn nguyên liệu thô nếu demo hoặc test vẫn sinh ra được nguyên liệu như món độc lập.

## 4. Active work

### Completed: Tuần 10 - Web API Integration

✅ Backend API với FastAPI  
✅ Frontend UI với HTML/CSS/JS  
✅ Menu generation endpoint  
✅ Swap functionality  
✅ API tests  
✅ Documentation (app/README.md, WEEK10_SUMMARY.md)

### Next: Tuần 11

Theo TASK_WEEK10.md, tuần 11 sẽ tập trung:

1. **Kiểm thử hệ thống**: E2E testing, cross-browser, mobile responsive
2. **Tổng hợp thực nghiệm**: Performance benchmarking, DBO vs IDBO với web config
3. **Chỉnh báo cáo**: docs/BaoCao_Tuan10.docx với screenshots và kết quả
4. **Chuẩn bị demo**: Script demo, video recording

### Expected branch

```text
experiment/dbo-idbo-ablation (hoặc feature/week10-web-api nếu tách riêng)
```

### Expected outputs

```text
docs/BaoCao_Tuan10.docx
experiments/week10_benchmarks/
  - performance_web_config.csv
  - runtime_comparison.png
screenshots/
  - ui_profile_form.png
  - ui_menu_display.png
  - ui_swap_demo.png
```

## 5. Pending tasks

### Tuần 11
1. E2E testing workflow: profile → targets → generate → swap
2. Performance benchmark web config
3. Báo cáo Word với screenshots
4. Demo video/script

### Technical Debt
1. Tiếp tục hoàn thiện DishRole, Culinary Slots và realistic portion bounds theo trạng thái trong `AGENTS.md`.
2. Bổ sung nguồn dữ liệu total sugar đáng tin cậy trước khi áp ràng buộc đường thật.
3. Caching cho (profile + seed) → same menu
4. User-friendly error messages
5. Dropdown UI cho swap món cụ thể

## 6. Known limitations

- Không có total sugar đáng tin cậy trong dataset hiện tại.
- Swap UI chỉ auto-select món khác, chưa có dropdown chọn món cụ thể.
- Chưa có caching cho same (profile + seed).
- Web API chỉ hỗ trợ 1 ngày, chưa có 7-day planning.
- Runtime web config chưa được benchmark chính thức (ước tính 3-5s).
- Candidate filtering và serving bounds cần được xác minh bằng demo thực tế, không chỉ unit tests.

## 7. Mandatory verification before completion

AI phải chạy các lệnh phù hợp với phạm vi thay đổi:

```bash
# All tests
python -m pytest tests/ -v

# API tests
python -m pytest tests/test_api.py -v

# Existing tests (verify không break)
python -m pytest tests/ --ignore=tests/test_api.py -v

# Specific modules
python -m pytest tests/test_two_tier_solver.py -v
python -m pytest tests/test_constraints.py tests/test_menu.py -v
```

Nếu sửa slide:

```bash
python scripts/build_pptx_week8_9.py
```

AI phải báo chính xác:

- số test passed/failed;
- seed và cấu hình experiment;
- file output;
- commit hash;
- giới hạn chưa xử lý.

## 8. Handoff protocol for future AI sessions

Khi bắt đầu phiên mới, cung cấp tối thiểu:

```text
AGENTS.md
PROJECT_STATE.md
CHANGELOG_AI.md
WEEK10_SUMMARY.md
latest_changes.patch
```

Nếu patch quá lớn hoặc chứa binary, cung cấp thêm incremental bundle hoặc các binary artifact riêng.

AI mới phải:

1. đọc `AGENTS.md`;
2. đọc `PROJECT_STATE.md`;
3. đọc các entry mới nhất trong `CHANGELOG_AI.md`;
4. chạy `git status --short --branch`;
5. xác minh base commit của patch;
6. không giả định patch đã được áp dụng nếu chưa kiểm tra Git history hoặc working tree.

## 9. Bắt buộc tạo patch sau mỗi phiên AI

Trước khi chỉnh sửa, AI phải lưu base commit:

```bash
BASE_COMMIT=$(git rev-parse HEAD)
printf '%s\n' "$BASE_COMMIT" > .ai_base_commit
```

Sau khi sửa, test và commit xong, AI phải tạo patch chứa toàn bộ commit mới kể từ base:

```bash
git format-patch \
  --stdout \
  "$(cat .ai_base_commit)"..HEAD \
  > latest_changes.patch
```

Nếu thay đổi chưa commit, tạo thêm working-tree patch:

```bash
git diff --binary > latest_worktree.patch
git diff --cached --binary > latest_staged.patch
```

Kiểm tra patch commit có thể áp dụng:

```bash
git apply --check latest_changes.patch
```

> `git apply --check` không phải lúc nào phù hợp với mail patch từ `git format-patch`. Khi cần giữ commit history, kiểm tra trong clone tạm bằng `git am --3way latest_changes.patch`.

Cách kiểm tra an toàn trong clone tạm:

```bash
TMP_DIR=$(mktemp -d)
git clone . "$TMP_DIR/repo"
cd "$TMP_DIR/repo"
git reset --hard "$(cat /path/to/original/repo/.ai_base_commit)"
git am --3way /path/to/original/repo/latest_changes.patch
python -m pytest -q
```

Sau khi tạo patch, AI phải cập nhật các trường sau trong file này:

```text
Last verified commit
Last verified date
Current milestone
Active work
Pending tasks
Known limitations
```

AI phải thêm entry tương ứng vào `CHANGELOG_AI.md`.

## 10. Patch delivery rules

- `latest_changes.patch` chỉ chứa thay đổi text và commit metadata phù hợp.
- Binary lớn như PPTX, PNG hoặc dataset nên được cung cấp riêng hoặc qua incremental Git bundle.
- Nếu patch có binary nhỏ và thực sự cần thiết, dùng `git diff --binary`.
- Không đưa secret, `.env`, token, `.venv`, cache hoặc temporary files vào patch.
- Ghi SHA-256 để phát hiện file truyền lỗi:

```bash
sha256sum latest_changes.patch > latest_changes.patch.sha256
```

- AI phải liệt kê các file được patch bao phủ:

```bash
git diff --name-status "$(cat .ai_base_commit)"..HEAD \
  > latest_changes.files.txt
```

## 11. End-of-session output contract

Trước khi kết thúc, AI phải để lại:

```text
PROJECT_STATE.md                # trạng thái mới nhất
CHANGELOG_AI.md                 # entry của phiên vừa làm
latest_changes.patch            # commit patch từ base đến HEAD
latest_changes.patch.sha256     # checksum
latest_changes.files.txt        # danh sách file thay đổi
```

Nếu có binary hoặc lịch sử Git phức tạp, tạo thêm:

```text
latest_changes.bundle
```

Bằng lệnh:

```bash
git bundle create latest_changes.bundle \
  "$(cat .ai_base_commit)"..HEAD
```

AI không được kết luận "đã hoàn tất" nếu chưa cập nhật handoff files hoặc chưa giải thích rõ vì sao không thể tạo chúng.
