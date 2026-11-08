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

- Git commit của server: `bab4d409f9fe48e310654c1ca1a861311af35d96` (nhánh `fix/c4-c6-takeover`).
- Server chạy `app.main:app` tại `http://127.0.0.1:8010`; audit là black-box HTTP, không import solver.
- `raw_requests.jsonl` và `raw_menus.jsonl` được giữ nguyên trong thư mục này để tái dựng `summary.json`/`REPORT.md` bằng `scripts/rebuild_audit_report.py`.
- `C19` đếm **nguyên liệu gốc** (bảng dinh dưỡng 100 g) thuộc nhóm bộ dò coi là thô; `C19b` đếm tên **hiển thị** còn là nguyên liệu thô. `C19b = 0` không có nghĩa `C19 = 0`: lớp ghép món chỉ đổi tên, không thay dữ liệu dinh dưỡng gốc.
- Đây là kiểm tra trong phạm vi thử nghiệm, không phải thẩm định lâm sàng. Các menu còn vi phạm ngưỡng dinh dưỡng phải được báo đúng là vi phạm, không được gọi là “đạt chuẩn”.
