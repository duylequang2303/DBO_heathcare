# CHANGELOG_AI.md — Lịch sử thay đổi do AI hỗ trợ

File này ghi lại các thay đổi do AI Coding Agent thực hiện hoặc hướng dẫn. Không thay thế Git history. Mục tiêu là giúp người và AI ở phiên sau hiểu nhanh điều gì đã thay đổi, bằng chứng xác minh và giới hạn còn lại.

## Quy tắc cập nhật

Mỗi phiên AI phải thêm một entry mới ở đầu phần `Entries`, theo mẫu:

```markdown
## YYYY-MM-DD — Tên nhiệm vụ

### Scope
- Mục tiêu và phạm vi.

### Base
- Branch bắt đầu:
- Base commit:

### Changed
- File và hành vi đã thay đổi.

### Experiments
- Cấu hình, seed và output.

### Verification
- Lệnh đã chạy.
- Kết quả chính xác.

### Artifacts
- CSV, hình, PPTX, patch hoặc bundle.

### Commits
- `<hash>` — `<message>`

### Remaining limitations
- Các giới hạn chưa xử lý.

### Handoff
- Patch:
- Patch SHA-256:
- Changed-files manifest:
- Bundle nếu có:
```

Không ghi "tests pass" nếu không có số lượng và lệnh thực tế. Không ghi "đã sửa" nếu chỉ cập nhật slide nhưng production code chưa thay đổi.

---

# Entries

## 2026-10-20 — Tích hợp bản vá Menu Realism & Đánh giá ngưỡng ứng viên IDBO (0.28)

### Scope
- Áp dụng bản vá từ `DBO_heathcare_INTEGRATED_FIXED.zip` (dynamic role bounds, culinary role filtering, sửa trường `food_name` cho API).
- Chạy lại toàn bộ kế hoạch thực nghiệm chẩn đoán DBO vs IDBO theo `KE_HOACH_CHAY_LAI_DBO_IDBO.md`.
- Hiệu chuẩn ngưỡng độ đa dạng ứng viên `diversity_threshold = 0.28` trên tập hiệu chỉnh (8001–8002).
- Đánh giá độc lập trên tập 8 hạt giống (8003–8010) với đối chuẩn paired DBO vs IDBO.

### Base
- Branch bắt đầu: `main` (commit `8890e23`)
- Nhánh làm việc: `fix/integrated-menu-realism`
- Commit tích hợp: `e022ccf`, `bc80473`, `4c88958`, `a50baed`, `11e4443`, `339051c`

### Changed
- `src/algorithms/two_tier_solver.py`: Dynamic role portion bounds theo từng vai trò ẩm thực (`STAPLE: 100-250g`, `MAIN_PROTEIN: 60-180g`, v.v.).
- `src/models/dish_category.py`: Xử lý an toàn `None`/`nan`, fallback món không rõ về `RAW_INGREDIENT` để loại khỏi menu người dùng.
- `src/models/food_selector.py`: Bổ sung `_is_user_facing_food` và `_roles_for_slot` cho layout 2+2+2+1.
- `app/api/services.py` & `app/api/swap.py`: Sửa `name` thành `food_name`.
- `scripts/audit_menu_realism.py`: Thêm công cụ chẩn đoán kiểm toán thực đơn người dùng.
- `scripts/calibrate_diversity_threshold.py`: Thêm script hiệu chuẩn ngưỡng độ đa dạng (th=0.25, 0.28, 0.32).
- `scripts/evaluate_candidate_threshold.py`: Thêm script đánh giá độc lập ngưỡng ứng viên 0.28.
- `tests/test_api.py`, `tests/test_food_selector.py`, `tests/test_menu_realism_audit.py`: Bổ sung tests bảo vệ.

### Experiments
- **Ablation Full Benchmark (10 seeds, 3 configs, 60 runs):**
  - Cấu hình cũ (th <= 0.05): DBO và IDBO hòa 100% (min_diversity ~0.25 > 0.05 nên 0 collapse events).
- **Candidate Threshold 0.28 Evaluation (10 seeds, outer_iter=100, stag=10):**
  - Tập hiệu chỉnh (8001–8002): 1 Thắng / 1 Thua (+0.7838 điểm).
  - Tập đánh giá độc lập (8003–8010): 5 Thắng / 0 Hòa / 3 Thua.
  - Chênh lệch điểm trung bình: +0.1659 điểm (trung vị: +0.1115 điểm).
  - Runtime tăng: +7.22 giây (+14.6%).
  - Kiểm định: Wilcoxon p = 0.6406, Sign test p = 0.7266 (chưa đạt mức ý nghĩa thống kê ở alpha=0.05).
  - Ràng buộc: 0 vi phạm kỹ thuật trên 100% các seed.

### Verification
```bash
./venv/bin/pytest -q
# 217 passed, 4 warnings in 21s
```

### Artifacts
- `experiments/ablation_dbo_idbo/candidate_threshold_028_eval.csv`
- `experiments/ablation_dbo_idbo/candidate_threshold_028_diffs.csv`
- `experiments/ablation_dbo_idbo/threshold_calibration_2seeds.csv`
- `experiments/ablation_dbo_idbo/CANDIDATE_THRESHOLD_028_REPORT.md`

### Remaining limitations
- Chưa thực hiện benchmark kiểm soát cùng ngân sách số lần gọi hàm mục tiêu (budget-matched).
- Cỡ mẫu đánh giá độc lập hiện tại (N=8) còn nhỏ để đạt ý nghĩa thống kê cho mức chênh lệch nhỏ (+0.1659 điểm).

---

## 2026-01-18 — Tuần 10: Web API Integration

### Scope
- Xây dựng FastAPI backend với 6 endpoints chính (health, profiles, targets, generate, foods, swap)
- Tạo frontend HTML/CSS/JS với form nhập hồ sơ, hiển thị menu, progress bars, radar chart
- Implement swap functionality với re-optimization
- Single-port architecture (FastAPI serve cả API và static files)
- Viết API tests với TestClient
- Tài liệu hóa API và usage guide

### Base
- Branch bắt đầu: `experiment/dbo-idbo-ablation`
- Base commit: `b32c6afec9f36bd421f48a4bdb6f9b1594b47f1f`

### Changed
**Backend:**
- Tạo `app/main.py`: FastAPI app, mount static files, startup event
- Tạo `app/api/schemas.py`: Pydantic models (ProfileIn, GenerateIn, SwapIn, MenuOut, etc.)
- Tạo `app/api/services.py`: Bridge layer tới solver, singleton food_db, profile conversion
- Tạo `app/api/routes.py`: Endpoints health, profiles, targets, generate
- Tạo `app/api/swap.py`: Swap logic và foods search endpoint

**Frontend:**
- Tạo `app/static/index.html`: Form nhập hồ sơ, menu table, progress bars, radar chart canvas
- Tạo `app/static/css/styles.css`: Responsive layout cho desktop và mobile
- Tạo `app/static/js/api.js`: Fetch wrappers cho API calls
- Tạo `app/static/js/app.js`: Main logic (form handling, render functions, swap handling)
- Tạo `app/static/js/charts.js`: Chart.js radar chart setup và update

**Testing:**
- Tạo `tests/test_api.py`: 9 API tests (health, profiles, targets, generate, swap, foods, validation)

**Dependencies:**
- Cập nhật `requirements.txt`: thêm fastapi, uvicorn[standard], pydantic, httpx

**Documentation:**
- Tạo `app/README.md`: API docs, architecture, usage guide
- Tạo `WEEK10_SUMMARY.md`: Complete summary of accomplishments
- Tạo `tasks.md`: Implementation plan (format Kiro, nhưng orchestrator không parse được)

### Experiments
N/A - Tuần này tập trung vào web development, không có benchmark experiment mới.

### Verification

**API Tests (9 tests):**
```bash
python -m pytest tests/test_api.py -v
# tests/test_api.py::test_health_check PASSED
# tests/test_api.py::test_get_profiles PASSED
# tests/test_api.py::test_calculate_targets_p1 PASSED
# tests/test_api.py::test_calculate_targets_invalid_age PASSED
# tests/test_api.py::test_generate_menu_smoke PASSED (1.13s)
# tests/test_api.py::test_search_foods PASSED
# tests/test_api.py::test_menu_swap PASSED
# tests/test_api.py::test_menu_swap_invalid_slot PASSED
# 9 passed, 4 warnings in ~1.5s
```

**Existing Tests (205 tests):**
```bash
python -m pytest tests/ --ignore=tests/test_api.py -v
# 205 passed in 10.06s
```

**Total: 214 tests passed**

### Artifacts
- `app/` - Toàn bộ web application code
- `tests/test_api.py` - API test suite
- `app/README.md` - API documentation
- `WEEK10_SUMMARY.md` - Summary và kết quả

### Commits
- `1a6cda3` — feat(week10): Implement FastAPI web application with menu generation and swap functionality
- `c8f741b` — docs(week10): Add README and summary documentation

### Remaining limitations
1. **Swap UI**: Chỉ auto-select món khác, chưa có dropdown để user chọn món cụ thể
2. **Caching**: Chưa có cache cho (profile + seed) → same menu
3. **Multi-day**: Chỉ hỗ trợ 1 ngày, chưa có 7-day planning (week 9 có nhưng chưa integrate vào API)
4. **Performance**: Web config runtime chưa được benchmark chính thức (ước tính 3-5s, smoke ~1.1s)
5. **Error messages**: Còn technical, chưa user-friendly
6. **Orchestrator**: tasks.md format không parse được bởi Kiro task system (đã thử nhiều format)
7. **Culinary roles**: Chưa enforce ENFORCED status từ AGENTS.md trong API output

### Handoff
- Patch: `latest_changes.patch` (cần tạo)
- Base commit đã lưu trong `.ai_base_commit`: `b32c6afec9f36bd421f48a4bdb6f9b1594b47f1f`
- Current HEAD: `c8f741b`
- Files changed: 18 files, 2633 insertions total

**Files mới:**
```
app/__init__.py
app/main.py
app/README.md
app/api/__init__.py
app/api/schemas.py
app/api/services.py
app/api/routes.py
app/api/swap.py
app/static/index.html
app/static/css/styles.css
app/static/js/api.js
app/static/js/app.js
app/static/js/charts.js
tests/test_api.py
WEEK10_SUMMARY.md
tasks.md
.ai_base_commit
```

**Files modified:**
```
requirements.txt (added 4 dependencies)
PROJECT_STATE.md (updated with week 10 status)
CHANGELOG_AI.md (this entry)
```

### Next Steps (Tuần 11)
1. E2E testing workflow đầy đủ
2. Performance benchmarking với web config
3. Báo cáo Word `docs/BaoCao_Tuan10.docx` với screenshots
4. Demo script và video recording
5. Cross-browser và mobile testing

---

