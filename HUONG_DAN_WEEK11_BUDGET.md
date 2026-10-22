# HƯỚNG DẪN CHẠY BUDGET-MATCHED — TUẦN 11 (CƯƠNG)

## 1. Kiểm thử

Từ thư mục `DBO_heathcare-main` trên PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q
```

## 2. Smoke test 2 seed

Chạy thử **ngân sách kỹ thuật nhỏ** (150 evaluations) để kiểm tra cơ chế, **không dùng kết quả này để kết luận thuật toán nào tốt hơn**:

```powershell
.\.venv\Scripts\python.exe -m scripts.experiment_week11_budget --smoke --max-evaluations 150 --outer-max-iter 2 --inner-max-iter 2 --output-dir results/week11_budget_smoke_150
```

Nếu bị ngắt, tiếp tục cùng cấu hình:

```powershell
.\.venv\Scripts\python.exe -m scripts.experiment_week11_budget --smoke --max-evaluations 150 --outer-max-iter 2 --inner-max-iter 2 --output-dir results/week11_budget_smoke_150 --resume
```

**Đối với thực nghiệm thật**, nhóm phải chốt một ngân sách chung trước, sau đó thay `--max-evaluations` và dùng thư mục output **mới**. Không lấy mặc định 150 làm ngân sách khoa học. Tệp kế hoạch Tuần 11 không chốt giá trị ngân sách.

## 3. Kết quả

- `config_locked.json`: cấu hình, `config_hash`, Git commit.
- `runs/8001_dbo.json`, `runs/8001_idbo.json`, ...: lưu tự động sau từng lượt chạy, không mất kết quả đã hoàn thành khi gián đoạn.
- `paired_runs.csv`: tổng hợp số liệu từng lượt.
- `--resume`: bỏ qua các lượt đã hoàn thành, chỉ chạy các lượt thiếu; từ chối nếu commit/cấu hình thay đổi.

Nếu Git không có trong bản ZIP, `git_commit=UNKNOWN_NO_GIT` sẽ được ghi và cảnh báo. **Trường hợp này chưa đáp ứng điều kiện truy xuất Git commit của kế hoạch**. Cần thực hiện trong repository Git có commit thực tế trước khi chạy benchmark chính thức.

## 4. Giới hạn và điều kiện

- `outer_diversity_threshold=0.28` được cố định.
- `inner_diversity_threshold=None` (chưa hiệu chỉnh). Muốn chỉ định phải có kết quả hiệu chỉnh độc lập.
- `max_evaluations` là **giới hạn trên chung** Outer + tất cả Inner + Final Inner. Do cơ chế cấp ngân sách, tổng evaluations thực tế có thể nhỏ hơn giới hạn và khác nhau giữa DBO/IDBO. Phải so sánh số evaluations thực tế, không tự nhận đã tiêu thụ chính xác bằng nhau.
- **Không chạy seed 8003–8010** cho tới khi 8 điều kiện ở mục 7 kế hoạch Tuần 11 đều được kiểm tra. Script chặn các seed ngoài 8001–8002 nếu không xác nhận `--allow-independent`.
- Không dùng kết quả smoke kỹ thuật nhỏ để kết luận IDBO vượt trội.
