# Audit live web

Thư mục này do `scripts/auditor_grill_live_web.py` tạo: black-box HTTP vào server
`app.main:app` đang chạy, không import solver, không sửa dữ liệu.

- `config.json`: tham số lần chạy
- `raw_requests.jsonl`: toàn bộ request/status/latency
- `raw_menus.jsonl`: toàn bộ thực đơn sinh ra
- `summary.json`: số liệu tổng hợp
- `REPORT.md`: báo cáo thẩm định
- `run.log`: log tiến độ
