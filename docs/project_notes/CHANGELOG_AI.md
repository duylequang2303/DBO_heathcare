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

