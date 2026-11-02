# BÁO CÁO VẤN ĐỀ & HẠN CHẾ CỦA DỰ ÁN

> **Prototype hỗ trợ quyết định thực đơn dinh dưỡng cá nhân hóa (DBO/IDBO)** — đề tài CNTT-KLCN142, ĐH Công Thương TP.HCM.
> **Đây không phải thiết bị y tế.** Mọi kết luận trong tài liệu này chỉ có hiệu lực trong phạm vi dữ liệu, cấu hình và seed đã đo.

| | |
|---|---|
| Ngày lập | 2026-11-01 |
| Code được đo | `30a05fe` (HEAD, nhánh `main`) + thay đổi chưa commit liệt kê ở §1.3 |
| Mục đích | Bản ghi **duy nhất** về vấn đề/hạn chế còn tồn tại, để không phải suy diễn lại khi bảo vệ, viết báo cáo, làm slide hoặc bàn giao |
| Đối tượng dùng | Nhóm thực hiện, giảng viên hướng dẫn, hội đồng phản biện |
| Trạng thái tài liệu | Sống — cập nhật mỗi khi một mục chuyển sang "đã chặn" kèm bằng chứng mới |

---

## 0. Quy ước đọc

Mỗi số liệu trong báo cáo này gắn một nhãn:

| Nhãn | Nghĩa | Ví dụ |
|---|---|---|
| **[ĐO]** | Đọc trực tiếp từ output/CSV/JSON/log do code sinh ra, có đường dẫn | "15/169 menu có natri > 1500 mg" |
| **[SUY RA]** | Kết luận rút từ dữ liệu [ĐO], không phải một con số đo được | "Chưa thể kết luận fitness hồi quy vì hai lần audit khác tập hồ sơ" |
| **[KHÔNG CÓ DỮ LIỆU]** | Thiếu dữ liệu nguồn, không thể suy ra bằng bất kỳ cách nào | "Không có cột total sugar" |

Nguyên tắc diễn đạt: **"đáp ứng/không đáp ứng ngưỡng được cấu hình trong thử nghiệm"**, không dùng "an toàn", "đạt chuẩn lâm sàng", "đạt AHA".

---

## 1. Nguồn số liệu

### 1.1. Bảng nguồn

| # | Nguồn | Thời điểm | Nội dung | Dùng cho |
|---|---|---|---|---|
| N1 | `venv/bin/python -m pytest -q` | 2026-11-01 | **391 passed**, 1 warning, 32.74 s | Bất biến nghiệp vụ, hồi quy |
| N2 | `experiments/audit_live_web_post_fix/` (`summary.json`, `raw_menus.jsonl`, `raw_requests.jsonl`, `run.log`) | 2026-11-01 | 322 request, 169 menu, 50/50 hồ sơ, 0 rerun, 639.4 s — **chạy trên code cuối** | Toàn bộ số liệu hành vi web |
| N3 | `experiments/audit_live_web_20261031_1434/` | 2026-10-31 | 422 request, 219 menu, 100 hồ sơ, 1.143 s — **historical** | Cột "trước" khi đối chiếu |
| N4 | `experiments/week11_role_bounds/` (`runs.csv`, `summary.json`) | 2026-11-01 | 30 seed (8000–8029), P1, config `smoke`, 210 khẩu phần | Kiểm tra biên khẩu phần theo vai trò |
| N5 | `experiments/ablation_dbo_idbo/` (`README.md`, CSV, figures) | 2026-10 | 10 paired seed × 3 cấu hình chẩn đoán + 1 sanity | Tuyên bố DBO vs IDBO, telemetry |
| N6 | Live probe `TestClient(app)` | 2026-11-01 | 1 generate + 1 swap, hồ sơ tiểu đường | Xác nhận hợp đồng API hiện tại |

### 1.2. Cảnh báo so sánh

N2 và N3 **khác tập hồ sơ** (50 vs 100) nên **không phải phép so sánh paired**. Chỉ các chỉ số cấu trúc (trần khẩu phần, khẩu phần phản ẩm thực, lọt dị ứng ngữ nghĩa) là so sánh trực tiếp theo cùng định nghĩa đo. Các chỉ số trung bình (fitness, % menu vi phạm, độ lệch dinh dưỡng) **không dùng** để kết luận cải thiện/hồi quy. Muốn kết luận phải chạy paired cùng seed, cùng tập hồ sơ (xem L02).

### 1.3. Thay đổi chưa commit tại thời điểm lập báo cáo

```
M app/api/services.py          M src/models/constraints.py
M app/api/swap.py              M src/models/dish_category.py
M app/main.py                  M src/models/food_sampler.py
M app/static/js/api.js         M tests/test_week11_fix_ngay_mai.py
M docs/slides/CAU_TRA_LOI_...  M scripts/build_pptx_week8_9_10_11.py
?? src/models/allergen_rules.py            ?? tests/test_safe_allergen_matching.py
?? scripts/check_role_bounds_impact.py     ?? tests/test_week11_role_portion_bounds.py
?? experiments/audit_live_web_post_fix/
```

Chưa có commit. Mọi số liệu N1–N4 đo trên working tree này, **không** đo trên `30a05fe` thuần.

---

## 2. Tóm tắt điều hành

13 hạn chế còn tồn tại. "Mức" xét theo **tác động tới việc bảo vệ/sử dụng**, không theo công sức sửa.

| ID | Hạn chế | Mức | Trạng thái | Ảnh hưởng trực tiếp |
|---|---|---|---|---|
| **L01** | Không có dữ liệu đường tổng (total sugar) | Cao | **Không thể xử lý trong phạm vi đề tài** | Không đánh giá được đường huyết; đã giảm thiểu bằng cảnh báo + `data_limitations` |
| **L02** | Chưa có thí nghiệm paired chứng minh fitness/gap sau Tuần 11 | Cao | Chưa xử lý | Không được nói "cải thiện"; số 85.8 → 66.9 là khác tập hồ sơ |
| **L03** | Natri không có trần cứng; 1 case 3280 mg ở hồ sơ THA | Cao | Chưa xử lý | Ngưỡng 1500 mg chỉ được kiểm tra/báo, một món mặn cực đoan vẫn lọt |
| **L04** | 72.2% menu vi phạm ít nhất một ngưỡng dinh dưỡng | Cao | Chưa xử lý | Fiber là loại vi phạm phổ biến nhất (116/169) |
| **L05** | Cơ cấu bữa và culinary slots sai 100% theo bộ đo độc lập | Cao | Chưa xử lý (thuộc "đang hoàn thiện") | Thực đơn không giống bữa ăn Việt Nam thật |
| **L06** | Tên món vẫn là tên nguyên liệu, 98.2% không nêu cách chế biến | Cao | Chưa xử lý | Người dùng nhận danh sách đi chợ, không phải thực đơn |
| **L07** | Dị ứng hẹp trả 400 (14/30 lượt) | Trung bình | Đúng hành vi, thiếu thông điệp | Người dùng không hiểu vì sao không tạo được |
| **L08** | Taxonomy dị ứng chỉ 4 nhóm + fallback chuỗi con | Trung bình | Một phần | Gluten/đậu nành/không dung nạp dựa vào so khớp chuỗi |
| **L09** | IDBO chưa chứng minh vượt DBO; cơ chế không kích hoạt | Cao | Đã kết luận trung thực, chưa có cải tiến | 10/10 hòa, Δ = 0.0000 |
| **L10** | API không trả telemetry IDBO | Trung bình | Chưa xử lý | Không thể kiểm chứng kích hoạt từ web/audit |
| **L11** | Swap không bảo đảm không xấu đi | Trung bình | Chưa xử lý | Gap biến thiên 31.7 điểm % qua chuỗi swap |
| **L12** | `generate` web mất 9.36 s trung bình, không có tiến trình/huỷ | Trung bình | Chưa xử lý | Người dùng dễ bấm lặp; p95 11.32 s |
| **L13** | Tài liệu/provenance chưa nhất quán | Trung bình | (a) đã sửa 2026-11-01; (b)(c) chưa | `docs/ROADMAP.md` vẫn chưa có; ablation README còn hai bộ số |

---

## 3. Đã xử lý ở Tuần 11 — để không đọc nhầm mục 4

Các mục dưới đây **đã đóng**, có bằng chứng; nêu ra để phần hạn chế không bị hiểu là "chưa làm gì".

| Vấn đề | Trước (N3) | Sau (N2) | Bằng chứng |
|---|---|---|---|
| Món kịch trần 350 g | 65/219 (29.7%) | **0/169** | `summary.json` `at_cap_menus` |
| Khẩu phần phản ẩm thực | 51/219 | **0/169** | `absurd_menus` |
| Bước swap chạm trần | 55/67 | **0/67** | `swap.steps_with_cap`, `max_portion_overall` 350 → **250 g** |
| Lọt dị ứng ngữ nghĩa | 1/30 | **0/30** | `allergy.semantic_leak_runs` |
| Gia vị như món độc lập | 0 | **0/169** | `condiment_menus` |
| Lỗi 5xx | 0 | **0** (322 request) | `n_5xx` |
| Tái lập cùng seed | True / True | **True / True** | `determinism.same_ids`, `same_portions` |
| Cảnh báo bệnh lý trong response | Không có | **Có** | N6: `warnings`, `data_limitations` |
| Swap trả `fitness` | Không | **Có** (`66.48`) | N6: key của `SwapOut` |
| Sai lệch calo vs 4/4/9 | — | max **0.4%**, 0 menu > 10% | `cal_macro_mismatch_pct` |

Ghi chú: `allergy.leak_runs = 1` trong N2 **không phải lọt dị ứng**. Đó là false-positive của bộ dò chuỗi con trong auditor: món "Gạo nếp **cái**" khớp "cá". Chỉ số đúng là `semantic_leak_runs = 0`. Xem L08.

---

## 4. Chi tiết từng hạn chế

### L01 — Không có dữ liệu đường tổng (total sugar)

**Hiện trạng [KHÔNG CÓ DỮ LIỆU].** Dataset huấn luyện/khai thác không có trường `total_sugar`. Hệ quả: không có bất kỳ ngưỡng đường nào được kiểm tra cho hồ sơ tiểu đường.
- Bằng chứng nguồn: `data/processed/PROVENANCE.md` §"No total sugar column"; `src/models/constraints.py` (docstring nêu rõ không được kết luận an toàn từ proxy carbohydrate).
- Đã giảm thiểu [ĐO — N6]: hồ sơ `["tiểu đường"]` nhận `warnings = ["Dữ liệu chưa có chỉ số đường tổng (sugar), thực đơn này chỉ hỗ trợ kiểm soát calo và tinh bột, không bảo đảm an toàn lâm sàng cho bệnh nhân tiểu đường."]` và `data_limitations = ["Sản phẩm là prototype kỹ thuật hỗ trợ quyết định, không phải thiết bị y tế."]`.
- Chỉ số đường **không** được bịa bằng `carbs × 0.15`; nếu sau này dùng, phải đặt tên `sugar_proxy_g` kèm `sugar_is_estimated = True` và không dùng để kết luận.

**Tác động.** P2 (tiểu đường) chỉ là hồ sơ mô phỏng cho benchmark, không đại diện cho một chế độ ăn điều trị.

**Vì sao chưa xử lý.** Không phải lỗi code — thiếu dữ liệu nguồn. Viết code cho ràng buộc đường khi chưa có số đo là tạo cảm giác an toàn giả.

**Hướng xử lý & điều kiện đóng.** Chỉ đóng khi: bảng thành phần có `total_sugar_g/100g` kèm provenance, phủ ≥95% pool 163 món, có test bất biến cho ngưỡng đường, và báo cáo ghi rõ nguồn đo. Trước đó: giữ cảnh báo, giữ nhãn "không đánh giá được đường huyết".

---

### L02 — Chưa có thí nghiệm paired cho fitness/gap sau Tuần 11

**Hiện trạng [ĐO — N2 vs N3].**

| Chỉ số | Trước (100 hồ sơ) | Sau (50 hồ sơ) |
|---|---|---|
| `fitness.mean` | 85.8 | 66.9 |
| `fitness.min` | 32.5 | **−23.8** |
| `menus_with_violation_pct` | 61.6% | 72.2% |
| `gap.mean` (proxy độ lệch dinh dưỡng) | 18.0% | 22.4% |

**[SUY RA]** Không thể quy chênh lệch này cho thay đổi Tuần 11. Hai lần chạy khác tập hồ sơ; thay đổi Tuần 11 chủ yếu thêm vector biên cho `swap`, kẹp biên sau làm tròn và truyền `food_map` cho validator. Tầng generate đã dùng `ROLE_PORTION_BOUNDS` từ trước.

**Tác động.** Nếu slide/báo cáo ghi "cải thiện chất lượng thực đơn" thì đó là claim không có bằng chứng. Ngược lại cũng không được nói "hồi quy" — chưa đo được.

**Hướng xử lý & điều kiện đóng.** Chạy paired: cùng 50 hồ sơ, cùng seed, hai nhánh bật/tắt kẹp-biên-vai-trò, báo best/mean/median/std/worst, paired difference, wins/ties/losses, Wilcoxon nếu phân phối phù hợp. Đóng khi có `experiments/<tên>/` chứa raw paired runs + summary CSV + README. Song song: xem xét lại việc **fitness âm** (−23.8) — 2 menu trong N2 có fitness < 0, không có ý nghĩa với người dùng cuối; hoặc chuẩn hoá về [0, 100], hoặc không hiển thị fitness thô cho người dùng.

---

### L03 — Natri: kiểm tra được, nhưng không có trần cứng

**Hiện trạng [ĐO — N2].**
- Toàn bộ 169 menu: natri trung bình **710.6 mg**, cao nhất **3280.4 mg**; **15** menu > 1500 mg; **1** menu > 2300 mg.
- Riêng hồ sơ tăng huyết áp (target = 1500 mg, 43 menu): **1/43 vượt 1500**, và chính menu đó vượt cả 2300 (3280.4 mg).
- `violation_types.sodium_mg = 1` — khớp với 1 menu thực sự vượt target của nó; 14 menu còn lại >1500 mg thuộc hồ sơ có target 2300 mg nên **không** phải vi phạm.

**Case cụ thể [ĐO]** — `hyp_seed129`, config `smoke`, seed 129:

```
Trứng chim cút 130 g (183 mg) · Sữa bò tươi 120 g (456 mg) · Chân giò lợn 160 g (75 mg)
Bí đao 220 g (29 mg) · Gạo nếp cái 250 g (8 mg) · Mề gà 165 g (114 mg)
Dưa chuột hộp 200 g (2416 mg)            ← 73.7% tổng natri của bữa
Tổng 3280.4 mg / target 1500 mg
```

Nguyên nhân gốc: pool 163 món (đo qua `get_food_map()`) có đúng **1 món ≥ 800 mg Na/100 g** — `VN_11002 "Dưa chuột hộp"` (1208 mg/100 g, sản phẩm muối chua). Solver không phạt món này vì natri chỉ là ràng buộc **được kiểm tra sau khi giải**, không nằm trong hàm mục tiêu hay ràng buộc cứng của tầng trong.

**Tác động.** Với người tăng huyết áp, đây là lỗi chức năng nghiêm trọng nhất còn lại: 1/43 khả năng nhận thực đơn vượt hơn gấp đôi ngưỡng. Tần suất thấp nhưng biên độ lớn — không thể gọi là "đáp ứng ngưỡng natri".

**Vì sao chưa xử lý.** Hai hướng có hệ quả trái ngược, phải đo trước khi chọn: (a) ép cứng ≤1500 mg có thể làm bài toán **vô nghiệm** với pool hiện tại; (b) lọc món mặn khỏi pool sẽ nghèo đa dạng và có thể tăng tỷ lệ 400. Đây là quyết định sản phẩm, không phải bug sửa mù.

**Hướng xử lý & điều kiện đóng.** (1) Đo feasibility: 30 seed × P3 với natri là ràng buộc cứng, đếm số lần infeasible. (2) Nếu feasible: thêm natri vào hàm mục tiêu + trần cứng cho hồ sơ THA, cộng test hồi quy cho `hyp_seed129`. (3) Nếu không feasible: thêm luật loại món ≥ 800 mg/100 g khỏi pool THA + cảnh báo khi không tìm được nghiệm dưới ngưỡng. Đóng khi 30/30 seed P3 có natri ≤ 1500 mg **hoặc** hệ thống từ chối tạo thực đơn kèm thông điệp rõ ràng.

---

### L04 — 72.2% menu vi phạm ít nhất một ngưỡng dinh dưỡng

**Hiện trạng [ĐO — N2].** 122/169 menu có ≥ 1 vi phạm. Phân bố theo loại:

| Loại | Số menu |
|---|---|
| `fiber_g` | 116 |
| `carbs_g` | 61 |
| `fat_g` | 48 |
| `energy` | 41 |
| `protein_g` | 37 |
| `sodium_mg` | 1 |
| trùng món trong ngày | 6 (3 menu) |

Trong nhóm hồ sơ tăng huyết áp (30 seed): `energy_violation = 3`, `protein_violation = 8`.

**Tác động.** Đây là **hành vi đã biết**: solver tối ưu fitness, không ép thoả tuyệt đối các dải ±10/±15/±20/±30%. Fiber là điểm yếu hệ thống (116/169) — pool ít món giàu xơ.

**Vì sao chưa xử lý.** Ép cứng mọi ngưỡng làm bài toán dễ vô nghiệm; cần quyết định ngưỡng nào là cứng, ngưỡng nào là mềm. Đây là thay đổi kiến trúc objective, không phải sửa lỗi.

**Hướng xử lý & điều kiện đóng.** Phân loại ràng buộc cứng/mềm rõ ràng trong `two_tier_solver`; thêm trọng số phạt cho fiber; báo cáo tỷ lệ đáp ứng theo từng ngưỡng thay vì gộp. Đóng khi có bảng tỷ lệ đáp ứng theo ngưỡng trên ≥ 50 hồ sơ, cùng tuyên bố "đáp ứng ngưỡng được cấu hình trong thử nghiệm".

---

### L05 — Cơ cấu bữa và culinary slots

**Hiện trạng [ĐO — N2].** `structure_fail_pct = 100%` (169/169), `slot_misplaced_pct = 100%`, `slot0_staple_pct = 22.8%` trên 338 slot đầu bữa trưa/tối. Nghĩa là slot đầu bữa trưa/tối chỉ đúng là tinh bột trong 22.8% trường hợp.

**Cảnh báo đo lường [SUY RA].** Auditor dùng **từ vựng độc lập** với `DishRole` của hệ thống. 100% "sai" một phần là khác định nghĩa slot, chưa chắc hoàn toàn là lỗi sản phẩm. Trước khi "sửa cho hết đỏ" phải đối chiếu hai định nghĩa — nếu không sẽ chạy theo thước đo của người khác.

**Tác động.** Thực đơn hiện là tập hợp món thoả dinh dưỡng, chưa phải cấu trúc bữa Việt Nam (cơm – mặn – canh – rau).

**Vì sao chưa xử lý.** Thuộc danh mục "đang hoàn thiện"; đụng `food_selector` (bố cục bữa) và cách đặt tên slot, dễ vỡ các test bất biến hiện có. **Không được tuyên bố đã chặn.**

**Hướng xử lý & điều kiện đóng.** Định nghĩa slot template theo bữa (ví dụ trưa = [tinh bột, đạm, rau, canh]), ràng buộc khi chọn món, test cho từng template, và đối chiếu lại với định nghĩa của auditor. Đóng khi `slot0_staple_pct` ≥ 90% **theo định nghĩa đã thống nhất**.

---

### L06 — Tên món là tên nguyên liệu, không nêu cách chế biến

**Hiện trạng [ĐO — N2].** `no_prep_menus = 166/169` (**98.2%**) có ít nhất một món chính không nêu cách chế biến; `raw_menus = 120/169` bị bộ dò độc lập của auditor nhận là nguyên liệu thô (ví dụ "Gạo lứt", "Khoai tây", "Măng tre", "Đuôi lợn"). Pool hiện tại: **163 món** đã qua whitelist + lọc vai trò, nhưng `display_name` vẫn là tên nguyên liệu.

**Tác động.** Đây là vấn đề UX nghiêm trọng nhất theo phản biện: người dùng nhận "danh sách đi chợ" thay vì thực đơn. Rẻ nhất để cải thiện, vì chỉ chạm lớp hiển thị.

**Vì sao chưa xử lý.** Cần công sức curate (đặt tên món cho 163 mục), không phải việc code.

**Hướng xử lý & điều kiện đóng.** Thêm lớp tên món ăn vào `data/vn_food_display.json` (`"Gạo lứt"` → `"Cơm gạo lứt"`, `"Khoai tây"` → `"Khoai tây luộc"`), **không** đổi nutrient, không đổi solver, không đổi `food_id`. Test: không nutrient nào thay đổi sau khi đổi tên (dinh dưỡng tính theo `food_id`, không theo tên). Đóng khi `no_prep_pct` < 10% **và** tên món vẫn giữ được truy vết tới `food_id`. Lưu ý: giảm chỉ số này là giảm chỉ số **của auditor**, không phải chứng minh "đã chặn nguyên liệu thô".

---

### L07 — Dị ứng hẹp trả 400

**Hiện trạng [ĐO — N2].** 30 lượt kiểm tra dị ứng: 16 × 200, **14 × 400**. Các tổ hợp trả 400: `bò`, `trứng`, `sữa` (đơn lẻ), `bò+heo+gà`, `trứng+sữa+đậu phộng`, 10 token, 20 token. Hành vi **giữ nguyên** so với N3.

**Tác động.** Hành vi đúng về mặt nghiệp vụ (loại trừ xong thì pool không đủ món để tạo thực đơn), nhưng người dùng chỉ thấy 400 và không hiểu. Đây là vấn đề **thông điệp**, không phải vấn đề logic.

**Vì sao chưa xử lý.** Cải thiện thông điệp là việc nhỏ nhưng cần thống nhất câu chữ với phần còn lại của UI.

**Hướng xử lý & điều kiện đóng.** Trả 400 kèm `detail` giải thích: đã loại bao nhiêu món, còn bao nhiêu, gợi ý bỏ bớt một dị ứng. Đóng khi mỗi mã 400 có `detail` tiếng Việt nêu được nguyên nhân và hành động gợi ý, có test cho 3 trường hợp trên.

---

### L08 — Taxonomy dị ứng chưa đầy đủ

**Hiện trạng.** `src/models/allergen_rules.py` có 4 nhóm: hải sản, đậu phộng, sữa, trứng; khớp theo ranh giới từ, có cụm ngoại lệ. Token không thuộc 4 nhóm rơi về **fallback so khớp chuỗi con**.
- Hệ quả tích cực [ĐO — N2]: `semantic_leak_runs = 0` (trước: 1), tức không còn món hải sản lọt vào menu đã yêu cầu loại trừ.
- Hệ quả tiêu cực: các dị ứng/dung nạp khác (gluten, đậu nành, hạt cây, hải sản có vỏ khác…) vẫn dựa vào so khớp chuỗi, có thể vừa bỏ sót vừa bắt nhầm. Ví dụ false-positive đã gặp: "Gạo nếp **cái**" khớp "cá" → `leak_runs = 1` trong N2. Chính auditor cũng có lỗi tương tự, nên con số `leak_runs` **không** dùng được để kết luận.

**Tác động.** An toàn dị ứng là lĩnh vực không cho phép sai số, trong khi đây là prototype với taxonomy tự viết tay.

**Vì sao chưa xử lý.** Cần một nguồn taxonomy chuẩn (ví dụ danh mục allergen của cơ quan quản lý) + kiểm định thủ công, vượt phạm vi tuần 11.

**Hướng xử lý & điều kiện đóng.** Thay fallback chuỗi con bằng token khớp có ranh giới từ; thêm test âm cho các cặp dễ nhầm ("cái"/"cá", "bò"/"bò cạp"); bổ sung nhóm gluten/đậu nành. Đóng khi có bộ test false-positive/false-negative cho từng nhóm.

---

### L09 — IDBO chưa chứng minh vượt DBO

**Hiện trạng [ĐO — N5].** 10 paired seed × 3 cấu hình chẩn đoán trên P1:

| Cấu hình | min diversity | ngưỡng collapse | perturbations | restarts | wins/ties/losses | paired Δ |
|---|---|---|---|---|---|---|
| baseline_short | 0.2462 ± 0.005 | 0.001 | **0** | **0** | 0 / 10 / 0 | 0.0000 |
| diagnostic_balanced | 0.2462 ± 0.005 | 0.010 | **0** | **0** | 0 / 10 / 0 | 0.0000 |
| diagnostic_aggressive_150 | 0.2462 ± 0.005 | 0.050 | **0** | **0** | 0 / 10 / 0 | 0.0000 |

Độ đa dạng tự nhiên của quần thể (~0.246) **luôn cao hơn** mọi ngưỡng sụp đổ (0.001 → 0.05) ⇒ điều kiện `diversity < threshold` luôn False ⇒ cả nhánh perturbation và restart không bao giờ chạy.
Cấu hình `controlled_activation` (`diversity_threshold = 0.50`) kích hoạt được: 17–21 outer perturbations, 9–13 restarts, `wiring_verified = True` trên 3/3 seed. **Đây là kiểm tra đường dây, không phải benchmark** — không được dùng để nói IDBO tốt hơn.

**Tác động.** Câu trả lời đúng khi bảo vệ: "Trong cấu hình thử nghiệm hiện tại, chưa ghi nhận IDBO vượt trội hơn DBO." Nguyên nhân đã được chứng minh bằng telemetry (cơ chế không kích hoạt), không phải "hai thuật toán giống nhau về bản chất".

**Vì sao chưa xử lý.** Cải tiến IDBO để kích hoạt có ý nghĩa trên bài toán rời rạc này là hướng nghiên cứu, cần thiết kế lại ngưỡng/độ đo đa dạng và đo lại paired — không phải chỉnh tham số cho đến khi IDBO thắng.

**Hướng xử lý & điều kiện đóng.** Thiết kế lại chỉ số đa dạng trên không gian `z` (rời rạc, không phải vector liên tục) để ngưỡng có ý nghĩa; sau đó chạy paired cùng seed, cùng số lần đánh giá, và báo đủ best/mean/median/std/worst + wins/ties/losses. Đóng khi có kết luận paired trên ≥ 30 seed với cơ chế **thực sự kích hoạt**.

---

### L10 — API không trả telemetry IDBO

**Hiện trạng [ĐO — `app/api/schemas.py`].** `GenerateOut` và `SwapOut` có `fitness`, `warnings`, `data_limitations` nhưng **không** có `n_perturbations`, `n_restarts`, stagnation. Telemetry chỉ tồn tại ở tầng `IDBOResult` (`src/algorithms/idbo.py`).

**Tác động.** Không thể kiểm chứng từ web/audit xem cơ chế IDBO có kích hoạt hay không; mọi tuyên bố về hành vi IDBO phải chạy script nội bộ. Auditor black-box hiện **không** đo được điều này.

**Hướng xử lý & điều kiện đóng.** Thêm khối `telemetry` (chỉ hiển thị ở chế độ demo/nâng cao) vào response generate; test rằng với cấu hình chính telemetry bằng 0, với `controlled_activation` lớn hơn 0. Đóng khi audit black-box đọc được telemetry.

---

### L11 — Swap không bảo đảm không xấu đi

**Hiện trạng [ĐO — N2].** 67 bước swap, `max_portion_overall = 250 g`, `steps_with_cap = 0` (đã sửa xong trần khẩu phần). Nhưng `swap.gap_first_last_delta = 31.7` điểm % — độ lệch dinh dưỡng biến thiên mạnh qua chuỗi swap; một số chuỗi xấu đi (SwapA 50.1 → 55.7; SwapC 41.4 → 52.6), một số tốt lên (SwapD 30.8 → 28.0; SwapE 59.2 → 52.6).

**Tác động.** Người dùng bấm "Thay món" có thể nhận thực đơn tệ hơn mà không biết. `SwapOut` đã trả `fitness` (N6: 66.48) nên có đủ dữ liệu để chặn, nhưng chưa chặn.

**Hướng xử lý & điều kiện đóng.** So sánh fitness trước/sau; nếu tệ hơn ngưỡng ε thì trả phương án tốt nhất tìm được kèm cờ `worse_than_before: true`, hoặc từ chối và giải thích. Đóng khi có test: swap không bao giờ trả fitness thấp hơn đầu vào quá ε mà không gắn cờ.

---

### L12 — Hiệu năng `generate` web và thiếu phản hồi tiến trình

**Hiện trạng [ĐO — N2].**

| Chỉ số | `web` (n=60) | `smoke` (n=85) |
|---|---|---|
| mean | 9364.8 ms | 163.9 ms |
| median | 9056.0 ms | 120.2 ms |
| p95 | 11319.4 ms | 221.3 ms |
| max | 14434.3 ms | 5894.9 ms |

Toàn bộ 322 request: mean 2004.7 ms, median 57.0 ms, p95 9955.0 ms, max 14434.3 ms. Swap đồng thời 10 request: 10/10 thành công, max 814.2 ms, 9 kết quả phân biệt.

**Tác động.** Trên server nội bộ đã ~9.4 s; deploy xa sẽ tệ hơn. Không có ước lượng thời gian, không có huỷ — người dùng dễ bấm lặp. (Nút đã disable trong lúc chờ, nên không tạo request trùng.)

**Hướng xử lý & điều kiện đóng.** Giảm ngân sách outer/inner cho cấu hình web, hoặc trả kết quả sớm + stream tiến trình. Đóng khi p95 < 3 s ở cấu hình demo **hoặc** UI có tiến trình/huỷ rõ ràng.

---

### L13 — Tài liệu và provenance chưa nhất quán

Ba lỗi cụ thể, đều đã kiểm chứng:

**(a) `experiments/audit_live_web_post_fix/REPORT.md` tự mâu thuẫn — ĐÃ SỬA 2026-11-01.**
- Trước khi sửa, dòng ~80 (mục "Những hạn chế") viết "response **có** chứa bất kỳ trường cảnh báo…" — thiếu chữ "không"; và §1.2 viết "`POST /api/menu/swap` không trả `fitness`, `diversity_pct`, `runtime_s`" trong khi `SwapOut` **có** trả `fitness`.
- Nguyên nhân: `scripts/build_audit_report.py` chứa **văn bản hard-code** của bản audit trước khi sửa, nên khi dựng lại từ `raw_*` mới thì bảng số mới mà phần diễn giải vẫn cũ.
- Đã sửa: `render_markdown` sinh toàn bộ §2–§6 từ `summary.json` (khối `derived`), mỗi con số gắn mã `[Cxx]` và được liệt kê trong bảng đối chiếu §7. `scripts/check_audit_report.py` so lại 36 khẳng định với `summary.json`, bắt lệch §1↔§7, §7↔summary, và chặn tái xuất hiện 8 câu hard-code cũ — hiện **PASS**. `raw_*`, `run.log`, `config.json` giữ nguyên mtime 14:14; chỉ `summary.json`, `REPORT.md`, `README.md` được dựng lại. Thư mục historical `experiments/audit_live_web_20261031_1434/` **không bị ghi đè** (checker bỏ qua và báo SKIP).

**(b) `docs/ROADMAP.md` không tồn tại.** `AGENTS.md` dòng 34 và `experiments/audit_live_web_post_fix/POST_FIX_DELTA.md` dòng 58 đều trỏ tới file này để giải thích danh mục "đang hoàn thiện". Không có file ⇒ nhóm hạn chế L04–L06 không có nơi theo dõi chính thức. Báo cáo này là bản thay thế tạm thời; nên tạo `docs/ROADMAP.md` trỏ về đây.

**(c) `experiments/ablation_dbo_idbo/README.md` có hai bộ số khác nhau cho cùng cấu hình.** §3 ghi `diagnostic_aggressive_150` mean fitness **99.2555**; §6 ghi **96.3323** (worst 84.08 @seed 8002). Một trong hai phải sai hoặc đo trên tập khác — cần xác định trước khi trích dẫn vào báo cáo/bảo vệ.

**Tác động.** Đây là rủi ro bảo vệ cao nhất về mặt tài liệu: hội đồng đối chiếu bảng và phần diễn giải sẽ thấy mâu thuẫn ngay trong cùng một file.

**Hướng xử lý & điều kiện đóng.** (1) ✅ **Đã xong 2026-11-01**: `build_audit_report.py` sinh diễn giải từ dữ liệu, `REPORT.md` dựng lại, `check_audit_report.py` PASS 36/36. (2) Tạo `docs/ROADMAP.md` với DoD cho từng mục L. (3) Xác định lại bộ số đúng của ablation, ghi rõ cấu hình/tập seed. Đóng hẳn khi `docs/ROADMAP.md` tồn tại và cả 3 tài liệu trỏ đúng nhau.

Lưu ý vận hành: nếu chạy lại audit end-to-end (`auditor_grill_live_web.py`) thì `REPORT.md` được sinh trực tiếp và vẫn phải chạy `python scripts/check_audit_report.py <thư-mục>` để xác nhận không lệch.

---

## 5. Những câu **không được** đưa vào slide/báo cáo

| ❌ Không nói | ✅ Nói thay thế |
|---|---|
| "An toàn cho người tiểu đường" | "Không đánh giá được đường huyết vì dataset thiếu total sugar; thực đơn kèm cảnh báo" |
| "Đạt chuẩn lâm sàng" / "đạt AHA" | "Đáp ứng/không đáp ứng ngưỡng dinh dưỡng được cấu hình trong thử nghiệm" |
| "Đã chặn nguyên liệu thô và culinary slots" | "Danh mục nguyên liệu thô và culinary slots đang hoàn thiện, chưa ENFORCED" |
| "IDBO vượt trội DBO" | "Trong cấu hình thử nghiệm hiện tại, chưa ghi nhận IDBO vượt trội hơn DBO (10/10 hòa, Δ=0.0000, cơ chế không kích hoạt)" |
| "Fitness cải thiện từ 85.8 lên…" | "Hai lần audit khác tập hồ sơ, không so sánh paired" |
| "Natri đã an toàn" | "15/169 menu > 1500 mg; riêng hồ sơ THA 1/43 vượt ngưỡng, nghiêm trọng nhất 3280 mg" |
| "Menu đã đạt cơ cấu bữa chuẩn" | "72.2% menu còn vi phạm ≥1 ngưỡng; cơ cấu bữa chưa được mô hình hoá" |

---

## 6. Câu hỏi bảo vệ thường gặp & trả lời ngắn

1. **"Hệ thống có đảm bảo an toàn cho người tiểu đường không?"**
   Không. Dataset không có cột đường tổng, nên chỉ kiểm soát được calo và tinh bột. Mọi thực đơn cho hồ sơ tiểu đường đều kèm cảnh báo nói rõ điều này.

2. **"Vì sao 72% thực đơn vẫn vi phạm ngưỡng?"**
   Solver tối ưu fitness, không ép thoả tuyệt đối. Vi phạm nhiều nhất là fiber (116/169) do pool ít món giàu xơ. Đây là hành vi đã biết, được báo cáo minh bạch, không phải lỗi ẩn.

3. **"IDBO có tốt hơn DBO không?"**
   Trong cấu hình hiện tại chưa. 10/10 paired seed hòa, Δ = 0.0000. Nguyên nhân đã chứng minh bằng telemetry: độ đa dạng quần thể (~0.246) luôn cao hơn ngưỡng sụp đổ (0.001–0.05) nên cơ chế perturbation/restart không chạy. Cấu hình `controlled_activation` chứng minh code chạy đúng khi ngưỡng được đặt phù hợp, nhưng đó là kiểm tra đường dây, không phải benchmark.

4. **"Vì sao thực đơn ghi 'Gạo lứt 115 g' thay vì tên món?"**
   Lớp hiển thị hiện dùng tên nguyên liệu trong dataset. Đây là hạn chế đã biết (L06), hướng xử lý là thêm lớp tên món chỉ chạm hiển thị, không đổi dinh dưỡng.

5. **"Người tăng huyết áp có bị vượt muối không?"**
   Có, 1/43 thực đơn trong đợt audit cuối (3280 mg so với ngưỡng 1500 mg), do pool có một món muối chua 1208 mg/100 g và natri chưa phải ràng buộc cứng. Đây là lỗi chức năng đã ghi nhận, chưa sửa.

6. **"Vì sao không dùng `carbs × 0.15` để ước lượng đường?"**
   Vì đó là proxy, không phải số đo. Nếu dùng phải đặt tên `sugar_proxy_g`, gắn `sugar_is_estimated = True`, và không được dùng để kết luận an toàn cho tiểu đường.

---

## 7. Thứ tự ưu tiên & công sức (ước lượng)

| Ưu tiên | Việc | Lý do | Ước lượng |
|---|---|---|---|
| ~~P0~~ | ~~L13a — sinh diễn giải từ dữ liệu, dựng lại `REPORT.md`~~ | ✅ **Xong 2026-11-01**, checker PASS 36/36 | — |
| **P0** | L13b — tạo `docs/ROADMAP.md` trỏ về báo cáo này, có DoD | Hiện không có nơi theo dõi | 1 giờ |
| **P0** | L07 — `detail` rõ ràng cho 400 khi pool dị ứng quá hẹp | Rẻ, giảm ma sát người dùng | 30 phút |
| **P1** | L06 — lớp tên món ăn cho 163 mục | Cải thiện UX lớn nhất trên mỗi giờ công | 1–2 ngày |
| **P1** | L03 — đo feasibility natri rồi chốt cứng/mềm | Lỗi chức năng nghiêm trọng nhất còn lại | 1–2 ngày |
| **P1** | L02 — paired run bật/tắt kẹp biên vai trò | Chỉ cần nếu có claim về fitness | 1 buổi |
| **P2** | L09/L10 — thiết kế lại chỉ số đa dạng, trả telemetry | Hướng nghiên cứu | 1–2 tuần |
| **P2** | L05 — culinary slots + cơ cấu bữa | Đụng `food_selector`, dễ vỡ bất biến | 3–5 ngày |
| **P3** | L11 — chặn swap làm xấu đi; L12 — hiệu năng; L08 — taxonomy dị ứng | Cải thiện dần | 1–3 ngày mỗi mục |

Nguyên tắc: **không** làm P2/P3 trước P0 vì P0 chính là thứ khiến các tuyên bố hiện tại không trung thực.

---

## 8. Tái lập

```bash
# 1. Toàn bộ test
venv/bin/python -m pytest -q                      # 391 passed

# 2. Kiểm tra biên khẩu phần theo vai trò
venv/bin/python scripts/check_role_bounds_impact.py --seeds 30 --config smoke \
    --out experiments/week11_role_bounds          # 0 ngoài biên

# 3. Audit end-to-end (cần server)
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
venv/bin/python scripts/auditor_grill_live_web.py \
    --base-url http://127.0.0.1:8000 --profiles 50 --hypertension-web 10 \
    --min-seconds 0 --max-seconds 900 --out experiments/audit_live_web_post_fix

# 4. Tái hiện case natri L03
venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)
prof = dict(name="Audit", age=55, gender="male", height_cm=168.0, weight_kg=75.0,
            activity_level="SEDENTARY", goal="MAINTAIN",
            meal_counts={"breakfast":2,"lunch":2,"dinner":2,"snack":1},
            medical_conditions=["hypertension"], allergies=[], dislikes=[])
d = c.post("/api/menu/generate", json={"profile":prof,"seed":129,"config":"smoke"}).json()
print(d["totals"]["sodium_mg"], d["targets"]["sodium_mg"], d["violations"])
PY
```

Cấu hình/seed dùng cho mọi số liệu: xem §1. Không có số liệu nào trong báo cáo này được nhập tay từ suy đoán.

---

## 9. Lịch sử cập nhật

| Ngày | Thay đổi | Bằng chứng |
|---|---|---|
| 2026-11-01 | Lập báo cáo từ N1–N6 | `pytest -q` 391 passed; `audit_live_web_post_fix/summary.json`; `ablation_dbo_idbo/README.md` |
| 2026-11-01 | Đóng L13a: `REPORT.md` sinh từ dữ liệu + có checker | `python scripts/check_audit_report.py experiments/audit_live_web_post_fix` → PASS 36/36 |

Khi một mục chuyển trạng thái, **bắt buộc** thêm dòng vào bảng này kèm script + thư mục output, và sửa cột "Trạng thái" ở §2. Không đổi số liệu mà không chạy lại nguồn tương ứng.
