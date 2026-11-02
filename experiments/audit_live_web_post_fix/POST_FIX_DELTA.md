# Đối chiếu thẩm định trước / sau Tuần 11

So sánh hai lần chạy cùng công cụ `scripts/auditor_grill_live_web.py`:

| | Trước | Sau |
|---|---|---|
| Thư mục | `experiments/audit_live_web_20261031_1434/` | `experiments/audit_live_web_post_fix/` |
| Hồ sơ ma trận | 100 | 50 |
| Request | 422 | 322 |
| Menu phân tích | 219 | 169 |
| Thời gian | 1.143 s | 639 s |

> **Cảnh báo so sánh:** hai lần chạy khác số hồ sơ ma trận (100 vs 50) nên tập
> menu không trùng nhau. Các chỉ số cấu trúc (trần khẩu phần, khẩu phần phản ẩm
> thực, lọt dị ứng ngữ nghĩa) là so sánh trực tiếp theo cùng định nghĩa đo; các
> chỉ số trung bình (fitness, % menu vi phạm, độ lệch dinh dưỡng) **không phải**
> phép so sánh paired và không dùng để kết luận cải thiện/hồi quy.

## 1. Kết quả đo được

| Chỉ số | Trước | Sau |
|---|---|---|
| Lỗi 5xx | 0 | **0** |
| Lỗi kết nối/timeout | 0 | **0** |
| Menu có món kịch trần 350 g | 65/219 (29.7%) | **0/169 (0.0%)** |
| Menu có khẩu phần phản ẩm thực | 51/219 | **0/169** |
| Bước swap chạm trần 350 g | 55/67 | **0/67** |
| Khẩu phần lớn nhất sau swap | 350 g | **250 g** |
| Lọt dị ứng ngữ nghĩa (`semantic_leak_runs`) | 1/30 | **0/30** |
| Menu chứa gia vị như món độc lập | 0/219 | **0/169** |
| Tái lập cùng seed (ids / portion) | True / True | **True / True** |
| Ma trận nhân khẩu | 100 OK, 0 rerun | **50 OK, 0 rerun** |

### 1.1. Về "1/30 lượt lọt dị ứng" ở cột Sau

`summary.json` ghi `leak_runs = 1` với `leak_examples = ["Gạo nếp cái"]` cho hồ sơ
`tôm+cua+cá`. Đây là **false-positive của bộ dò chuỗi con trong auditor**, không
phải món hải sản: "cá" nằm trong "cái". Trường `semantic_leak_runs` (khớp theo
ranh giới từ) bằng **0**. Bộ dò của auditor được giữ nguyên (black-box, không
import solver); chỉ số đáng tin là `semantic_leak_runs`.

### 1.2. Về fitness và % menu vi phạm

- `fitness.mean`: 85.8 → 66.9; `fitness.min`: 32.5 → −23.8.
- `menus_with_violation_pct`: 61.6% → 72.2%.
- `gap.mean` (độ lệch dinh dưỡng): 18.0% → 22.4%.

Không thể quy các chênh lệch này cho thay đổi Tuần 11: tầng generate đã dùng
`ROLE_PORTION_BOUNDS` từ trước (trong `two_tier_solver.portion_bounds`); thay đổi
chỉ bổ sung vector bounds cho **swap**, kẹp biên sau làm tròn và truyền `food_map`
cho validator. Hai lần chạy cũng khác tập hồ sơ. Cần một thí nghiệm paired
(cùng seed, cùng tập hồ sơ, bật/tắt kẹp-vai-trò) trước khi kết luận về fitness.

## 2. Việc còn tồn tại (báo cáo trung thực)

- `structure_fail_pct = 100%`, `slot_misplaced_pct = 100%`: cơ cấu bữa và culinary
  slots vẫn là hạn chế đã biết, thuộc danh mục **đang hoàn thiện** trong
  `docs/ROADMAP.md`. Không tuyên bố đã chặn.
- `no_prep_pct = 98.2%`: tên món vẫn là tên nguyên liệu, chưa nêu cách chế biến.
- `raw_menus = 120/169`: auditor vẫn nhận diện một số món là nguyên liệu thô theo
  từ vựng độc lập của nó (ví dụ "Gạo lứt", "Khoai tây", "Măng tre"). Đây là điểm
  chưa xử lý, không phải hồi quy của lần sửa này.
- Dị ứng "bò", "trứng", "sữa" (đơn lẻ) vẫn trả 400 vì pool candidate không đủ món
  sau khi loại trừ — hành vi giữ nguyên so với lần trước (14 phản hồi 400 ở cả hai
  lần chạy).
- Natri: 15/169 menu vượt 1500 mg, 1/169 vượt 2300 mg (trước: 17/219 và 1/219).
  Ràng buộc natri được **kiểm tra và báo vi phạm**, không phải được solver ép thoả.

## 3. Tái lập

```bash
venv/bin/python -m pytest -q                                   # 391 passed
venv/bin/python scripts/check_role_bounds_impact.py --seeds 30 --config smoke \
    --out experiments/week11_role_bounds                        # 0 out-of-bounds
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
venv/bin/python scripts/auditor_grill_live_web.py \
    --base-url http://127.0.0.1:8000 --profiles 50 --hypertension-web 10 \
    --min-seconds 0 --max-seconds 900 --out experiments/audit_live_web_post_fix
```

Số liệu trong tài liệu này đọc từ `experiments/audit_live_web_post_fix/summary.json`
và `experiments/audit_live_web_20261031_1434/summary.json`, không chỉnh tay.
