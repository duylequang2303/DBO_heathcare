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
