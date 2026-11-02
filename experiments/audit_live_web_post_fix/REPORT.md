# BÁO CÁO PHẢN BIỆN & THẨM ĐỊNH HỆ THỐNG GỢI Ý THỰC ĐƠN DBO/IDBO

- Thời điểm chạy: **639 giây** (~11 phút), **322 request HTTP thực tế** vào server `app.main:app`.
- Server: `http://127.0.0.1:8000`, black-box, không import solver, không sửa dữ liệu.
- Thực đơn thu được để phân tích: **169** `[C02]`.
- Toàn bộ số liệu đọc từ `summary.json`, `raw_requests.jsonl`, `raw_menus.jsonl` trong cùng thư mục.
- **Phần diễn giải ở §2–§6 sinh tự động từ `summary.json`**, không có câu nào viết cứng. Mỗi con số mang mã `[Cxx]`; §7 đối chiếu từng mã với đường dẫn dữ liệu, `scripts/check_audit_report.py` kiểm tra lại tự động.

## 1. BẢNG TỔNG KẾT SỐ LIỆU ĐO ĐƯỢC

| Chỉ số | Giá trị | Mã |
|---|---|---|
| Tổng request | 322 | C01 |
| 200 OK | 278 (86.3%) | — |
| 4xx (từ chối đúng) | 44 | C04 |
| 5xx (lỗi server) | 0 | C03 |
| Lỗi kết nối/timeout | 0 | — |
| Latency TB / trung vị / p95 / max | 2,004.7 / 57.0 / 9955.0 / 14,434.3 ms | C25 |
| Generate `web` (TB / p95) | 9,364.8 / 11,319.4 ms (n=60) | — |
| Generate `smoke` (TB) | 163.9 ms (n=85) | — |
| Menu có ≥1 vi phạm | 122/169 (72.2%) | C07 |
| Fitness TB (menu sinh ra) | 66.9 (min -23.8 – max 99.9) | — |
| Menu có fitness âm | 2 | C09 |
| Sodium cao nhất | 3280.4 mg | C10 |
| Menu vượt 1500 mg natri (mọi hồ sơ) | 15/169 | C11 |
| Menu vượt 2300 mg natri | 1/169 | — |
| Hồ sơ tăng huyết áp: menu / vượt 1500 mg | 43 / 1 | [C12] [C13] |
| Độ lệch dinh dưỡng TB (calo+4 macro) | 22.4% (max 59.7%) | — |
| Menu có món kịch trần ≥349.5 g | 0/169 (0.0%) | C15 |
| Menu có khẩu phần phản ẩm thực | 0/169 | C16 |
| Menu sai cơ cấu bữa trưa/tối | 169/169 (100.0%) | C17 |
| Menu sai vai trò slot ẩm thực | 169/169 (100.0%) | — |
| Slot đầu bữa trưa/tối đúng là tinh bột | 22.8% (338 slot) | C18 |
| Menu chứa gia vị như món độc lập | 0/169 | — |
| Menu chứa nguyên liệu thô (bộ dò auditor) | 120/169 | C19 |
| Menu có món chính không nêu cách chế biến | 98.2% (166/169) | C20 |
| Lượt lọt dị ứng ngữ nghĩa (token “hải sản”) | 0/30 | C21 |
| Lượt lọt dị ứng theo khớp chuỗi con (bộ dò auditor) | 1/30 | — |
| Lượt dị ứng trả 400 | 14/30 | C22 |
| Menu trùng món trong ngày | 3 | — |
| Số bước swap đo được | 67 (max portion 250 g) | — |
| Menu swap có trả `fitness` | 67/67 | C14 |
| Biến thiên độ lệch dinh dưỡng qua swap | 31.7 điểm % (đầu → cuối) | C24 |
| 10 swap đồng thời | {'200': 10} · max 814.2 ms | — |
| Tái lập cùng seed | ids giống: True · portion giống: True | [C23] [C23b] |
| Ma trận nhân khẩu | 50 OK / 0 lỗi, 0 rerun seed | C27 |
| Nhất quán calo vs 4P+4C+9F | 169 menu kiểm, lệch max 0.4%, 0 menu >10% | C28 |

Phân bố tuổi / BMI / vận động / cấu trúc bữa trong ma trận: `{'18-25': 13, '26-45': 13, '46-65': 12, '>65': 12}`, BMI `{'underweight': 12, 'normal': 12, 'overweight': 10, 'obese1': 8, 'obese2': 8}`, vận động `{'SEDENTARY': 20, 'LIGHT': 20, 'MODERATE': 10}`, bữa `{'3meals': 15, '4meals': 15, 'big': 10, 'light': 10}`.

## 2. DIỄN GIẢI TỰ ĐỘNG

### 2.1. Lỗi server và thông điệp lỗi

- `[C03]` Không có request nào trả 5xx trên **322** request: server không sập, không rò traceback ra client.
- `[C04]` Trong **44** phản hồi 4xx, **0** phản hồi chứa mẫu lỗi Pydantic tiếng Anh (`Input should…`, `String should…`, `Field required`) `[C06]`.
- `[C05]` **14** phản hồi 400 có `detail` chứa thuật ngữ nội bộ tiếng Anh (`min_pool_size`, `has size …`) — người dùng cuối vẫn đọc thấy thông điệp kỹ thuật dù phần đầu câu đã tiếng Việt.

### 2.2. Swap: fitness, khẩu phần, độ lệch

- Đo được **67** bước swap trên **5** chuỗi `[C29]` `[C30]`.
- `[C14]` `SwapOut` **có** trả `fitness`: **67/67** menu swap có trường này (min -23.77 – max 98.02). Vì vậy báo cáo dùng cả `fitness` (điểm solver trả về) và `gap` (độ lệch dinh dưỡng so với target, đơn vị %, là đại lượng suy ra chứ không phải fitness).
- Chuỗi 5 lần swap cùng slot: **3** chuỗi xấu đi, **2** chuỗi tốt lên, **0** chuỗi không đổi. Biến thiên trung bình đầu→cuối: `[C24]` **31.7** điểm %.
  - SwapA: 50.1 → 55.7 (xấu đi), min 49.8, max 55.7
  - SwapB: 41.2 → 43.1 (xấu đi), min 41.2, max 46.3
  - SwapC: 41.4 → 52.6 (xấu đi), min 41.2, max 52.6
  - SwapD: 30.8 → 28.0 (tốt lên), min 28.0, max 32.5
  - SwapE: 59.2 → 52.6 (tốt lên), min 52.0, max 59.7
- `[SUY RA]` Dữ liệu cho thấy `gap` có thể **tăng** sau swap; audit này không ghi nhận cơ chế nào từ chối phương án có `gap`/`fitness` tệ hơn phương án trước.
- Tổng số bước swap có ít nhất một món chạm trần ≥349.5 g: **0/67**; khẩu phần lớn nhất sau swap: **250 g** `[C31]` `[C32]`.

### 2.3. Bệnh lý

- Alias tiếng Việt: `hypertension` → 1500.0 mg, `tăng huyết áp` → 1500.0 mg, `cao huyết áp` → 1500.0 mg.
- `[C26]` Hồ sơ tiểu đường: **3/3** lần gọi trả 200 **đều có trường cảnh báo** (`derived.diabetes_warn = True`) và **đều nhắc tới sugar/đường** trong payload. Danh sách key trả về: `['data_limitations', 'diversity_pct', 'fitness', 'items', 'runtime_s', 'targets', 'totals', 'violations', 'warnings']`.
- Bệnh lý không được mô hình hoá: `gout` → 2300.0 mg; `suy thận` → 2300.0 mg — trả 200 nhưng `sodium_target` không đổi so với hồ sơ khỏe mạnh, tức không có ngưỡng riêng và không có cảnh báo “chưa hỗ trợ” trong payload.

### 2.4. Natri

- Toàn bộ 169 menu: natri TB **710.6 mg** `[C33]`, cao nhất `[C10]` **3,280.4 mg**; `[C11]` **15** menu vượt 1500 mg và **1** menu vượt 2300 mg.
- Hồ sơ tăng huyết áp: `[C12]` **43** menu, target trả về `[1500.0]` mg; `[C13]` **1** menu vượt 1500 mg (1 vượt cả 2300 mg), natri cao nhất **3,280.4 mg**.
- `[SUY RA]` Ràng buộc natri **được kiểm tra và báo vi phạm**, nhưng **không được solver ép thoả** trong mọi trường hợp. Không thể tuyên bố “đáp ứng ngưỡng natri 1500 mg cho mọi thực đơn”.
  - seed 129 (smoke): **3,280 mg**
- Hệ quả siết muối: **3 menu vi phạm năng lượng**, **8 menu vi phạm đạm** trên cùng bộ seed `[C34]` `[C35]`.

### 2.5. Dị ứng

- `[C22]` 30 lượt sinh menu với nhiều cấu hình token loại trừ (đơn, bộ ba, 10 và 20 token); trạng thái: `{'200': 16, '400': 14}`; **14** lượt trả 400.
- `[C21]` Lượt còn món biển sau khi loại trừ token **“hải sản”**: **0/30** (khớp theo ranh giới từ, không phải chuỗi con).
- Bộ dò của auditor còn ghi **1** lượt “lọt” theo **khớp chuỗi con**: `[{'label': 'triple:tôm+cua+cá', 'leaks': ['Gạo nếp cái']}]`. Đây là false-positive của bộ dò (ví dụ “Gạo nếp **cái**” chứa “cá”), không phải món hải sản; chỉ số đúng là `[C21]`.
- Loại trừ **một** nhóm quen thuộc cũng làm hỏng yêu cầu: `['single:bò', 'single:trứng', 'single:sữa']` trả 400, vì pool ứng viên còn lại nhỏ hơn `min_pool_size`. Hệ thống từ chối tạo thực đơn thay vì crash, nhưng người dùng không nhận được gợi ý nới điều kiện.

### 2.6. Khẩu phần và ẩm thực

- `[C15]` Menu có món chạm trần ≥349.5 g: **0/169** (0.0%). `[C16]` Khẩu phần bị coi là phản ẩm thực: **0** menu.
- `[C18]` Slot đầu bữa trưa/tối đúng là tinh bột: **22.8%** trên 338 slot; `[C17]` **169/169** (100.0%) menu bị coi là sai cơ cấu bữa.
- `[CẢNH BÁO ĐO LƯỜNG]` Auditor phân vai trò món bằng **từ vựng độc lập** với `DishRole` của hệ thống, nên 100% “sai” không đồng nghĩa 100% lỗi sản phẩm. Phải đối chiếu hai định nghĩa slot trước khi sửa theo con số này.
- `[C19]` **120/169** menu chứa món bị bộ dò coi là nguyên liệu thô; `[C20]` **98.2%** menu có món chính không nêu cách chế biến. Đây là giới hạn của lớp tên hiển thị (tên nguyên liệu thay vì tên món), không phải lỗi dinh dưỡng.
- Không có menu nào chứa gia vị như món độc lập trong đợt chạy này.
- `[C28]` Nhất quán calo vs 4P+4C+9F: lệch lớn nhất **0.4%**, **0** menu lệch >10%.

### 2.7. Dữ liệu món ăn

- Mẫu **137** món `[C36]` lấy từ `/api/foods`; trong mẫu đó có **0** tên gia vị, **10** tên nguyên liệu thô, **97** tên không nêu cách chế biến.
- Natri/100 g cao nhất: `[['Dưa chuột hộp', 1208.0], ['Tôm đồng', 418.0], ['Sữa bò tươi', 380.0], ['Nước ép cà chua', 269.0], ['Bầu dục bò', 200.0]]` — những món này một mình đã chiếm phần lớn ngưỡng 1500 mg/ngày.

### 2.8. Chaos / fuzzing

| Case | Kỳ vọng | Thực tế | Kết luận |
|---|---|---|---|
| age=0 | 4xx | 422 | PASS |
| age=-10 | 4xx | 422 | PASS |
| age=200 | 4xx | 422 | PASS |
| age='hai mươi tuổi' | 4xx | 422 | PASS |
| height=30cm | any | 200 | INFO |
| height=300cm | 4xx | 422 | PASS |
| weight=5kg | any | 200 | INFO |
| weight=400kg | any | 200 | INFO |
| meal_counts toàn 0 | 4xx | 400 | PASS |
| chỉ snack x3 | 4xx | 400 | PASS |
| snack=10 | 4xx | 422 | PASS |
| breakfast=-1 | 4xx | 422 | PASS |
| meal key 'brunch' | 4xx | 422 | PASS |
| allergy rỗng | 4xx | 422 | PASS |
| allergy '<script>' | any | 200 | INFO |
| allergy emoji | any | 200 | INFO |
| allergy null byte | any | 200 | INFO |
| allergy 10.000 ký tự | any | 200 | INFO |
| allergy 1000 token | any | 200 | INFO |
| name SQL injection | any | 200 | INFO |
| name 10.000 ký tự | any | 200 | INFO |
| medical SQL | any | 200 | INFO |
| extra field | any | 200 | INFO |
| thiếu profile | 4xx | 422 | PASS |
| gender 'other' | 4xx | 422 | PASS |
| activity thường | 4xx | 422 | PASS |
| seed=-1 | 4xx | 422 | PASS |
| config='turbo' | 4xx | 422 | PASS |
| foods q SQL | any | 200 | INFO |
| foods q 10.000 | any | 200 | INFO |
| foods limit=0 | 4xx | 422 | PASS |
| foods limit=1000 | 4xx | 422 | PASS |
| swap slot lạ | 4xx | 400 | PASS |
| swap thiếu food_ids | 4xx | 422 | PASS |
| swap food_id lạ | 4xx | 400 | PASS |
| swap new_food lạ | 4xx | 400 | PASS |
| swap old_portions lệch | 4xx | 422 | PASS |
| swap old_portions=0 | 4xx | 422 | PASS |
| swap old_portions=1e9 | 4xx | 422 | PASS |
| swap food_ids rỗng | 4xx | 422 | PASS |
| swap trùng món trong bữa | 4xx | 400 | PASS |
| targets age=0 | 4xx | 422 | PASS |
| JSON hỏng | 4xx | 422 | PASS |
| content-type text/plain | 4xx | 422 | PASS |

- **0 case FAIL**, **0 case 500**.
- **3** hồ sơ phi thực tế vẫn trả 200 (height=30cm, weight=5kg, weight=400kg): thiếu kiểm tra hợp lý sinh học, không phải lỗi crash.

## 3. NHỮNG THỰC ĐƠN TỆ NHẤT GHI NHẬN ĐƯỢC

> Danh sách dưới đây do hàm chấm điểm của auditor xếp hạng từ chính `raw_menus.jsonl`.

**1. [clinical] hyp_seed102** — 1,822 kcal, natri 397 mg, lệch target 29.7%
   - Món: Sữa dê tươi 50g; Đậu tương (đậu nành) 105g; Gạo nếp cái 125g; Tôm đồng 70g; Cá thu đao 60g; Măng tre 165g; Hạt điều 125g
   - Cơ cấu bữa: breakfast: thiếu tinh bột; dinner: thiếu tinh bột
   - Nguyên liệu thô (theo bộ dò): Đậu tương (đậu nành); Gạo nếp cái; Măng tre
   - Vi phạm: carbs_g: 159.4 outside [195.1, 263.9]; fat_g: 87.9 outside [49.0, 73.4]; fiber_g: 13.0 outside [26.6, 49.4]

**2. [matrix] Audit-047** — 2,207 kcal, natri 183 mg, lệch target 7.7%
   - Món: Đậu xanh (đậu tắt) 200g; Đậu tương (đậu nành) 115g; Hành củ tươi 210g; Củ sắn 220g; Cải bắp đỏ 220g; Dạ dày bò 60g; Hạt điều 90g
   - Cơ cấu bữa: breakfast: thiếu tinh bột; lunch: thiếu tinh bột; dinner: thiếu tinh bột
   - Nguyên liệu thô (theo bộ dò): Đậu xanh (đậu tắt); Đậu tương (đậu nành); Củ sắn

**3. [allergy] single:hải sản** — 2,373 kcal, natri 318 mg, lệch target 5.4%
   - Món: Đậu tương (đậu nành) 240g; Trứng chim cút 180g; Gạo lứt 100g; Măng tre 140g; Gạo nếp cái 180g; Rau câu tươi 220g; Hồng xiêm 200g
   - Cơ cấu bữa: breakfast: thiếu tinh bột
   - Nguyên liệu thô (theo bộ dò): Đậu tương (đậu nành); Gạo lứt; Măng tre; Gạo nếp cái

**4. [swap] gen_SwapA** — 2,373 kcal, natri 154 mg, lệch target 8.7%
   - Món: Đậu hà lan (hạt) 50g; Đậu tương (đậu nành) 185g; Gạo lứt 190g; Cá thu 80g; Bí đao (bí xanh) 105g; Củ cái 220g; Hạt điều 65g
   - Cơ cấu bữa: breakfast: thiếu tinh bột; dinner: thiếu tinh bột
   - Nguyên liệu thô (theo bộ dò): Đậu hà lan (hạt); Đậu tương (đậu nành); Gạo lứt
   - Vi phạm: fiber_g: 23.2 outside [26.6, 49.4]

**5. [matrix] Audit-017** — 1,938 kcal, natri 157 mg, lệch target 8.2%
   - Món: Đậu tương (đậu nành) 250g; Gạo lứt 190g; Măng tre 220g; Cá chép 180g; Cải bắp đỏ 170g
   - Cơ cấu bữa: breakfast: thiếu tinh bột; dinner: thiếu tinh bột
   - Nguyên liệu thô (theo bộ dò): Đậu tương (đậu nành); Gạo lứt; Măng tre

**6. [matrix] Audit-036** — 1,605 kcal, natri 589 mg, lệch target 6.8%
   - Món: Đậu tương (đậu nành) 235g; Dạ dày lợn 65g; Măng tre 220g; Gạo nếp cái 135g; Tôm đồng 125g
   - Cơ cấu bữa: breakfast: thiếu tinh bột; lunch: thiếu tinh bột
   - Nguyên liệu thô (theo bộ dò): Đậu tương (đậu nành); Măng tre; Gạo nếp cái

## 4. CÂU HỎI “BẪY” VÀ CÂU TRẢ LỜI SINH TỪ SỐ LIỆU

**Câu 1. “Hệ thống khẳng định thực đơn an toàn cho người tăng huyết áp. Vậy vì sao có seed ra 3,280 mg natri?”**
- Trả lời: “Không. Chúng em chỉ khẳng định thực đơn **đáp ứng hoặc không đáp ứng ngưỡng được cấu hình trong thử nghiệm**. Trong 43 thực đơn của hồ sơ tăng huyết áp, 1 thực đơn vượt 1500 mg và hệ thống báo vi phạm đúng; đây là hạn chế của bộ giải, không phải bảo đảm lâm sàng. Đây không phải thiết bị y tế.”

**Câu 2. “Món ‘Gạo lứt 115 g’ là món gì? Ai ăn gạo sống?”**
- Trả lời: “Dữ liệu gốc là bảng thành phần dinh dưỡng theo 100 g nguyên liệu, nên tên hiển thị hiện là tên nguyên liệu; 98.2% thực đơn trong đợt test dính vấn đề này. Đây là khoảng trống giữa dữ liệu dinh dưỡng và thực đơn ẩm thực, không phải kết quả tối ưu. Hướng khắc phục là lớp tên món ăn, chỉ chạm hiển thị, không đổi hàm dinh dưỡng.”

**Câu 3. “Nếu tôi dị ứng hải sản và gõ ‘hải sản’, hệ thống có loại tôm cua cá không?”**
- Trả lời: “Trong 30 lượt thử, **không lượt nào còn món biển** sau khi loại trừ token ‘hải sản’ (`[C21]` = 0). Bộ dò chuỗi con của auditor vẫn ghi 1 lượt, nhưng đó là false-positive như ‘Gạo nếp **cái**’ chứa ‘cá’. Giới hạn còn lại: taxonomy hiện chỉ phủ một số nhóm thực phẩm, dị ứng ngoài các nhóm đó vẫn dựa vào so khớp chuỗi.”

**Câu 4. “Điểm fitness nghĩa là gì với bệnh nhân? Bấm Đổi món 5 lần thì điểm có đổi không?”**
- Trả lời: “Fitness là hàm mục tiêu nội bộ, không phải chỉ số sức khỏe. `SwapOut` **có** trả `fitness` (67/67 menu swap), nên giao diện cập nhật được điểm sau mỗi lần đổi món. Vấn đề còn lại là ý nghĩa: một con số 0–100 không cho người bệnh biết đang thiếu hay thừa chất gì.”

**Câu 5. “Vì sao bảng thực đơn có nhiều món là nguyên liệu thô như ‘Măng tre 220 g’?”**
- Trả lời: “Đó là lớp tên hiển thị, không phải khẩu phần: 98.2% menu có món chính không nêu cách chế biến (`[C20]`), và 120/169 menu bị bộ dò độc lập coi là có nguyên liệu thô (`[C19]`). Trong đợt chạy này không có món nào chạm trần khẩu phần ≥349.5 g (`[C15]` = 0).”

## 5. VIỆC CẦN FIX — CHỈ HIỆN KHI CHỈ SỐ TƯƠNG ỨNG KHÁC 0

1. **Natri ở hồ sơ tăng huyết áp**: 1/43 menu vượt 1500 mg (cao nhất 3,280 mg). Cần đo feasibility của trần cứng trước khi chọn giữa (a) ràng buộc cứng và (b) loại món có natri/100 g rất cao khỏi pool.
2. **Dị ứng**: mở rộng taxonomy allergen và bỏ fallback so khớp chuỗi con; 14 lượt trả 400 cần thông điệp nêu rõ món nào đang chặn pool.
3. **Thông điệp lỗi**: 14 phản hồi 400 còn lộ thuật ngữ nội bộ (`min_pool_size`) — cần Việt hoá trọn câu.
4. **Lớp tên món**: 98.2% menu có món chính không nêu cách chế biến; thêm tên món ăn ở lớp hiển thị, không đổi nutrient hay `food_id`.
5. **Cơ cấu bữa**: 100.0% menu bị coi là sai cấu trúc theo bộ đo độc lập; cần đối chiếu định nghĩa slot trước khi sửa.

## 6. GHI CHÚ THỦ CÔNG — KHÔNG SINH TỪ DỮ LIỆU

> Mục này **cố ý** không suy ra từ `summary.json`. Nó là quan sát giao diện, kiểm bằng cách đọc code frontend, nên **không tự cập nhật** khi chạy lại audit. Sửa UI thì phải sửa tay mục này.

- Bảng thực đơn hiển thị song song khẩu phần thô và khẩu phần đã làm tròn (`portion_g` → `portion_g_rounded`) — `app/static/js/app.js`, khối `renderMenu`.
- Dòng “Tổng ngày” in số tuyệt đối; ngưỡng cá nhân không nằm cạnh con số mà chỉ xuất hiện trong khối vi phạm bên dưới — cùng file, phần `totalRow` và `renderViolations`.
- Seed và cấu hình solver nằm trong `<details class="advanced-settings">` (`app/static/index.html`), đã thu gọn mặc định.
- Thông điệp 422 được Việt hoá ở cả backend và `formatFieldError()` trong `app/static/js/api.js`; cảnh báo bệnh lý hiển thị qua `renderWarnings`.

## 7. BẢNG ĐỐI CHIẾU KHẲNG ĐỊNH ↔ DỮ LIỆU

Mỗi dòng: mã — đường dẫn trong `summary.json` — giá trị đã in ở trên. `scripts/check_audit_report.py <thư-mục>` đọc bảng này, so lại với `summary.json` và báo lệch.

```text
C01	n_requests	322
C02	n_menus	169
C03	n_5xx	0
C04	derived.n_4xx	44
C05	derived.n_400_internal_message	14
C06	derived.n_4xx_english_pydantic	0
C07	menus_with_violation	122
C09	derived.n_menus_fitness_negative	2
C10	sodium.max	3280.4
C11	sodium.n_over_1500	15
C12	derived.n_hyp_menus	43
C13	derived.n_hyp_over_1500	1
C14	derived.n_swap_menus_with_fitness	67
C15	at_cap_menus	0
C16	absurd_menus	0
C17	structure_fail_menus	169
C18	slot0_staple_pct	22.8
C19	raw_menus	120
C20	no_prep_pct	98.2
C21	allergy.semantic_leak_runs	0
C22	derived.n_allergy_menus_400	14
C23	determinism.same_ids	True
C23b	determinism.same_portions	True
C24	swap.gap_first_last_delta	31.7
C25	latency_all.p95	9955.0
C26	derived.diabetes_warn	True
C27	matrix.ok	50
C28	cal_macro_mismatch_pct.max	0.4
C29	swap.n_swap_steps	67
C30	swap.n_chains	5
C31	swap.steps_with_cap	0
C32	swap.max_portion_overall	250.0
C33	sodium.mean	710.6
C34	clinical.hypertension.energy_violation	3
C35	clinical.hypertension.protein_violation	8
C36	inventory.n_foods_sampled	137
```

---
*Số liệu sinh tự động từ 322 request trong 639 giây; toàn bộ phần diễn giải đọc từ `summary.json` (xem §7), không có câu nào viết cứng. Đọc/ghi chỉ trong thư mục `experiments/` của đợt chạy; không đụng dữ liệu production.*
