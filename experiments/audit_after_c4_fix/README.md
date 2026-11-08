# Audit live web

Thư mục này do `scripts/auditor_grill_live_web.py` tạo: black-box HTTP vào server
`app.main:app` đang chạy, không import solver, không sửa dữ liệu.

- `config.json`: tham số lần chạy
- `raw_requests.jsonl`: toàn bộ request/status/latency
- `raw_menus.jsonl`: toàn bộ thực đơn sinh ra
- `summary.json`: số liệu tổng hợp (khối `derived` chứa mọi dữ kiện dùng để diễn giải)
- `REPORT.md`: báo cáo thẩm định — §2–§6 sinh từ `summary.json`, §7 đối chiếu từng khẳng định
- `run.log`: log tiến độ

Kiểm tra báo cáo khớp dữ liệu (chạy từ thư mục gốc repo, sau mọi lần dựng lại):

    python scripts/check_audit_report.py experiments/<thư-mục-này>

## Ghi chú provenance (đợt chạy 2026-11-08)

- Git commit của server khi chạy audit: `d018ea5dec2b49d58b18bc5666a99e62d6f6d8c2` (nhánh `fix/c4-c6-takeover`).
- Server chạy `app.main:app` tại `http://127.0.0.1:8012`; audit là black-box HTTP.
- `raw_requests.jsonl` và `raw_menus.jsonl` được giữ nguyên trong thư mục này. Nếu chỉnh tiêu chí phân tích, dùng `scripts/rebuild_audit_report.py` để dựng lại `summary.json`/`REPORT.md`, không gõ lại request vào server.
- `C19` đếm **nguyên liệu gốc** thuộc nhóm bị bộ dò coi là thô; `C19b` đếm tên **hiển thị** còn là nguyên liệu thô. Lớp ghép món không làm đổi dữ liệu dinh dưỡng gốc và không được dùng để che C19.
- Đây là kiểm tra trong phạm vi thử nghiệm, không phải thẩm định lâm sàng.
