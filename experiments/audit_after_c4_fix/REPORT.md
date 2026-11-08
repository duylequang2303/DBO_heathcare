# BÁO CÁO PHẢN BIỆN & THẨM ĐỊNH HỆ THỐNG GỢI Ý THỰC ĐƠN DBO/IDBO

- Thời điểm chạy: **816 giây** (~14 phút), **246 request HTTP thực tế** vào server `app.main:app`.
- Server: `http://127.0.0.1:8012`, black-box, không import solver, không sửa dữ liệu.
- Thực đơn thu được để phân tích: **133** `[C02]`.
- Toàn bộ số liệu đọc từ `summary.json`, `raw_requests.jsonl`, `raw_menus.jsonl` trong cùng thư mục.
- **Phần diễn giải ở §2–§6 sinh tự động từ `summary.json`**, không có câu nào viết cứng. Mỗi con số mang mã `[Cxx]`; §7 đối chiếu từng mã với đường dẫn dữ liệu, `scripts/check_audit_report.py` kiểm tra lại tự động.

## 1. BẢNG TỔNG KẾT SỐ LIỆU ĐO ĐƯỢC

| Chỉ số | Giá trị | Mã |
|---|---|---|
| Tổng request | 246 | C01 |
| 200 OK | 204 (82.9%) | — |
| 4xx (từ chối đúng) | 42 | C04 |
| 5xx (lỗi server) | 0 | C03 |
| Lỗi kết nối/timeout | 0 | — |
| Latency TB / trung vị / p95 / max | 3,365.7 / 146.0 / 28814.1 / 38,221.1 ms | C25 |
| Generate `web` (TB / p95) | 28,430.5 / 38,022.1 ms (n=22) | — |
| Generate `smoke` (TB) | 294.2 ms (n=85) | — |
| Menu có ≥1 vi phạm | 114/133 (85.7%) | C07 |
| Fitness TB (menu sinh ra) | 73.7 (min 37.2 – max 99.9) | — |
| Menu có fitness âm | 0 | C09 |
| Sodium cao nhất | 2300.8 mg | C10 |
| Menu vượt 1500 mg natri (mọi hồ sơ) | 1/133 | C11 |
| Menu vượt 2300 mg natri | 1/133 | — |
| Hồ sơ tăng huyết áp: menu / vượt 1500 mg | 43 / 0 | [C12] [C13] |
| Độ lệch dinh dưỡng TB (calo+4 macro) | 18.0% (max 44.4%) | — |
| Menu có món kịch trần ≥349.5 g | 0/133 (0.0%) | C15 |
| Menu có khẩu phần phản ẩm thực | 0/133 | C16 |
| Menu sai cơ cấu bữa trưa/tối | 0/133 (0.0%) | C17 |
| Menu sai vai trò slot ẩm thực | 0/133 (0.0%) | — |
| Slot đầu bữa trưa/tối đúng là tinh bột | 100.0% (266 slot) | C18 |
| Menu chứa gia vị như món độc lập | 0/133 | — |
| Menu có nguyên liệu gốc bị coi là thô | 130/133 | C19 |
| Menu hiển thị tên nguyên liệu thô | 0/133 | C19b |
| Menu có món chính không nêu cách chế biến | 0.0% (0/133) | C20 |
| Lượt lọt dị ứng ngữ nghĩa (token “hải sản”) | 0/30 | C21 |
| Lượt lọt dị ứng theo khớp chuỗi con (bộ dò auditor) | 2/30 | — |
| Lượt dị ứng trả 400 | 12/30 | C22 |
| Menu trùng món trong ngày | 0 | — |
| Số bước swap đo được | 62 (max portion 250 g) | — |
| Menu swap có trả `fitness` | 62/62 | C14 |
| Biến thiên gap toàn chuỗi swap | 9.9 điểm % (baseline → cuối) | C24 |
| Biến thiên gap 5 bước cuối | -4.1 điểm % (signed; abs 5.4) | C24b |
| 10 swap đồng thời | {'200': 10} · max 1564.0 ms | — |
| Tái lập cùng seed | ids giống: True · portion giống: True | [C23] [C23b] |
| Ma trận nhân khẩu | 12 OK / 0 lỗi, 0 rerun seed | C27 |
| Nhất quán calo vs 4P+4C+9F | 133 menu kiểm, lệch max 0.3%, 0 menu >10% | C28 |

Phân bố tuổi / BMI / vận động / cấu trúc bữa trong ma trận: `{'18-25': 3, '26-45': 3, '46-65': 3, '>65': 3}`, BMI `{'underweight': 4, 'normal': 4, 'overweight': 4}`, vận động `{'SEDENTARY': 12}`, bữa `{'3meals': 5, '4meals': 5, 'big': 2}`.

> Ghi chú: phần bị cắt do ngân sách thời gian: `{'matrix': 18}`.

## 2. DIỄN GIẢI TỰ ĐỘNG

### 2.1. Lỗi server và thông điệp lỗi

- `[C03]` Không có request nào trả 5xx trên **246** request: server không sập, không rò traceback ra client.
- `[C04]` Trong **42** phản hồi 4xx, **0** phản hồi chứa mẫu lỗi Pydantic tiếng Anh (`Input should…`, `String should…`, `Field required`) `[C06]`.
- `[C05]` Không phản hồi 400 nào chứa thuật ngữ nội bộ (`min_pool_size`).

### 2.2. Swap: fitness, khẩu phần, độ lệch

- Đo được **62** bước swap trên **5** chuỗi `[C29]` `[C30]`.
- `[C14]` `SwapOut` **có** trả `fitness`: **62/62** menu swap có trường này (min 37.22 – max 97.68). Vì vậy báo cáo dùng cả `fitness` (điểm solver trả về) và `gap` (độ lệch dinh dưỡng so với target, đơn vị %, là đại lượng suy ra chứ không phải fitness).
- Chuỗi 5 lần swap cùng slot: **2** chuỗi xấu đi, **3** chuỗi tốt lên, **0** chuỗi không đổi. Biến thiên trung bình đầu→cuối của đúng 5 bước: `[C24b]` **-4.1** điểm % (abs 5.4). Toàn chuỗi (gồm các bước tuần tự trước đó): `[C24]` **9.9** điểm %.
  - SwapA: 28.5 → 29.8 (xấu đi), min 19.5, max 29.9
  - SwapB: 44.4 → 25.1 (tốt lên), min 25.1, max 38.7
  - SwapC: 12.8 → 12.3 (tốt lên), min 12.3, max 18.3
  - SwapD: 22.3 → 18.3 (tốt lên), min 18.3, max 23.8
  - SwapE: 23.3 → 25.2 (xấu đi), min 24.5, max 27.8
- `[SUY RA]` Dữ liệu cho thấy `gap` có thể **tăng** sau swap; audit này không ghi nhận cơ chế nào từ chối phương án có `gap`/`fitness` tệ hơn phương án trước.
- Tổng số bước swap có ít nhất một món chạm trần ≥349.5 g: **0/62**; khẩu phần lớn nhất sau swap: **250 g** `[C31]` `[C32]`.

### 2.3. Bệnh lý

- Alias tiếng Việt: `hypertension` → 1500.0 mg, `tăng huyết áp` → 1500.0 mg, `cao huyết áp` → 1500.0 mg.
- `[C26]` Hồ sơ tiểu đường: **3/3** lần gọi trả 200 **đều có trường cảnh báo** (`derived.diabetes_warn = True`) và **đều nhắc tới sugar/đường** trong payload. Danh sách key trả về: `['data_limitations', 'diversity_pct', 'fitness', 'items', 'runtime_s', 'targets', 'totals', 'violations', 'warnings']`.
- Bệnh lý không được mô hình hoá: `gout` → 2300.0 mg; `suy thận` → 2300.0 mg — trả 200 nhưng `sodium_target` không đổi so với hồ sơ khỏe mạnh, tức không có ngưỡng riêng và không có cảnh báo “chưa hỗ trợ” trong payload.

### 2.4. Natri

- Toàn bộ 133 menu: natri TB **442.1 mg** `[C33]`, cao nhất `[C10]` **2,300.8 mg**; `[C11]` **1** menu vượt 1500 mg và **1** menu vượt 2300 mg.
- Hồ sơ tăng huyết áp: `[C12]` **43** menu, target trả về `[1500.0]` mg; `[C13]` **0** menu vượt 1500 mg (0 vượt cả 2300 mg), natri cao nhất **1,340.5 mg**.
- `[SUY RA]` Trong bộ seed này không có menu nào vượt 1500 mg; đây là kết quả trong phạm vi thử nghiệm, không phải bảo đảm lâm sàng. Ràng buộc natri vẫn là kiểm tra sau khi giải, không phải ràng buộc cứng của solver.
- Hệ quả siết muối: **1 menu vi phạm năng lượng**, **7 menu vi phạm đạm** trên cùng bộ seed `[C34]` `[C35]`.

### 2.5. Dị ứng

- `[C22]` 30 lượt sinh menu với nhiều cấu hình token loại trừ (đơn, bộ ba, 10 và 20 token); trạng thái: `{'200': 18, '400': 12}`; **12** lượt trả 400.
- `[C21]` Lượt còn món biển sau khi loại trừ token **“hải sản”**: **0/30** (khớp theo ranh giới từ, không phải chuỗi con).
- Bộ dò của auditor còn ghi **2** lượt “lọt” theo **khớp chuỗi con**: `[{'label': 'single:cá', 'leaks': ['Cơm gạo nếp cái']}, {'label': 'triple:tôm+cua+cá', 'leaks': ['Cơm gạo nếp cái']}]`. Đây là false-positive của bộ dò (ví dụ “Gạo nếp **cái**” chứa “cá”), không phải món hải sản; chỉ số đúng là `[C21]`.
- Loại trừ **một** nhóm quen thuộc cũng làm hỏng yêu cầu: `['single:trứng', 'single:sữa']` trả 400, vì pool ứng viên còn lại nhỏ hơn `min_pool_size`. Hệ thống từ chối tạo thực đơn thay vì crash, nhưng người dùng không nhận được gợi ý nới điều kiện.

### 2.6. Khẩu phần và ẩm thực

- `[C15]` Menu có món chạm trần ≥349.5 g: **0/133** (0.0%). `[C16]` Khẩu phần bị coi là phản ẩm thực: **0** menu.
- `[C18]` Slot đầu bữa trưa/tối đúng là tinh bột: **100.0%** trên 266 slot; `[C17]` **0/133** (0.0%) menu bị coi là sai cơ cấu bữa.
- `[CẢNH BÁO ĐO LƯỜNG]` Auditor phân vai trò món bằng **từ vựng độc lập** với `DishRole` của hệ thống, nên 100% “sai” không đồng nghĩa 100% lỗi sản phẩm. Phải đối chiếu hai định nghĩa slot trước khi sửa theo con số này.
- `[C19]` **130/133** menu có nguyên liệu gốc thuộc nhóm bị bộ dò coi là thô; `[C19b]` **0/133** menu còn hiển thị tên nguyên liệu thô; `[C20]` **0.0%** menu có món chính không nêu cách chế biến. C19 là giới hạn dữ liệu gốc (bảng dinh dưỡng theo 100 g nguyên liệu), không phải lỗi dinh dưỡng; C19b/C20 đo lớp ghép món hiển thị và phải đọc cùng C19.
- Không có menu nào chứa gia vị như món độc lập trong đợt chạy này.
- `[C28]` Nhất quán calo vs 4P+4C+9F: lệch lớn nhất **0.3%**, **0** menu lệch >10%.

### 2.7. Dữ liệu món ăn

- Mẫu **137** món `[C36]` lấy từ `/api/foods`; trong mẫu đó có **0** tên gia vị, **11** tên nguyên liệu thô, **98** tên không nêu cách chế biến.
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

**1. [clinical] hyp_seed127** — 1,758 kcal, natri 208 mg, lệch target 23.2%
   - Món: Đậu tương (đậu nành) hấp 100g; Đậu hà lan (hạt) luộc 80g; Cơm gạo nếp cái 100g; Thịt bồ câu ra ràng xào 60g; Cơm gạo nếp máy (loại thường) 100g; Cá mòi áp chảo 160g; Nước cam tươi (ăn tươi) 50g
   - Nguyên liệu thô (theo bộ dò): Đậu tương (đậu nành); Đậu hà lan (hạt); Gạo nếp cái; Gạo nếp máy (loại thường)
   - Vi phạm: protein_g: 107.6 outside [78.0, 105.6]; fiber_g: 10.5 outside [26.6, 49.4]

**2. [swap] SwapA:seq:breakfast_0** — 2,377 kcal, natri 227 mg, lệch target 14.7%
   - Món: Khoai tây luộc 100g; Đậu hà lan (hạt) luộc 220g; Cơm gạo lứt 165g; Rau mồng tơi luộc 220g; Cơm gạo nếp cái 100g; Thịt bồ câu ra ràng xào 180g; Chuối tây (ăn tươi) 50g
   - Nguyên liệu thô (theo bộ dò): Khoai tây; Đậu hà lan (hạt); Gạo lứt; Gạo nếp cái
   - Vi phạm: carbs_g: 343.8 outside [252.0, 340.9]

**3. [swap] gen_SwapA** — 2,360 kcal, natri 171 mg, lệch target 8.4%
   - Món: Đậu tương (đậu nành) hấp 115g; Đậu hà lan (hạt) luộc 160g; Cơm gạo lứt 120g; Rau mồng tơi luộc 80g; Cơm gạo nếp cái 100g; Thịt bồ câu ra ràng xào 150g; Chuối tây (ăn tươi) 200g
   - Nguyên liệu thô (theo bộ dò): Đậu tương (đậu nành); Đậu hà lan (hạt); Gạo lứt; Gạo nếp cái

**4. [clinical] diabetes_seed7** — 1,446 kcal, natri 379 mg, lệch target 25.3%
   - Món: Đậu tương (đậu nành) hấp 105g; Trứng gà luộc 130g; Cơm gạo tẻ giã 100g; Rau húng luộc 80g; Cơm gạo nếp máy (loại thường) 100g; Rau bí luộc 110g; Dâu tây (ăn tươi) 195g
   - Nguyên liệu thô (theo bộ dò): Đậu tương (đậu nành); Gạo tẻ giã; Gạo nếp máy (loại thường)
   - Vi phạm: energy 1445 kcal outside [1062, 1298]; carbs_g: 195.2 outside [100.3, 135.6]

**5. [swap] SwapB:chain5:4** — 1,445 kcal, natri 322 mg, lệch target 25.1%
   - Món: Đậu xanh (đậu tắt) hấp 100g; Đậu phụ sốt cà 95g; Cơm kê 100g; Măng tre luộc 220g; Cơm gạo lứt 100g; Cá trích áp chảo 180g; Dứa tây (ăn tươi) 50g
   - Nguyên liệu thô (theo bộ dò): Đậu xanh (đậu tắt); Măng tre; Gạo lứt
   - Vi phạm: energy 1445 kcal outside [1117, 1366]; carbs_g: 203.0 outside [105.5, 142.8]; fat_g: 33.0 outside [33.1, 49.7]

**6. [allergy] triple:tôm+cua+cá** — 2,351 kcal, natri 644 mg, lệch target 23.1%
   - Món: Khoai tây luộc 100g; Trứng vịt luộc 180g; Cơm gạo nếp máy (loại thường) 245g; Thịt lợn nạc xào 180g; Cơm gạo nếp cái 130g; Sườn lợn hầm 180g; Dứa ta (ăn tươi) 155g
   - Nguyên liệu thô (theo bộ dò): Khoai tây; Gạo nếp máy (loại thường); Gạo nếp cái
   - Vi phạm: fiber_g: 4.2 outside [26.6, 49.4]

## 4. CÂU HỎI “BẪY” VÀ CÂU TRẢ LỜI SINH TỪ SỐ LIỆU

**Câu 1. “Hệ thống khẳng định thực đơn an toàn cho người tăng huyết áp. Vậy vì sao có seed ra 1,340 mg natri?”**
- Trả lời: “Không. Chúng em chỉ khẳng định thực đơn **đáp ứng hoặc không đáp ứng ngưỡng được cấu hình trong thử nghiệm**. Trong 43 thực đơn của hồ sơ tăng huyết áp, 0 thực đơn vượt 1500 mg và hệ thống báo vi phạm đúng; đây là hạn chế của bộ giải, không phải bảo đảm lâm sàng. Đây không phải thiết bị y tế.”

**Câu 2. “Món ‘Gạo lứt 115 g’ là món gì? Ai ăn gạo sống?”**
- Trả lời: “Bảng dinh dưỡng lưu tên nguyên liệu theo 100 g; menu hiển thị tên món đã ghép ở lớp trình bày. Bộ đo tên nguyên liệu thô hiển thị (`[C19b]`) ghi nhận 0/133 thực đơn (0.0%). Chỉ số này khác với việc thiếu mô tả cách chế biến (`[C20]`). Tên món ghép không thay đổi dữ liệu dinh dưỡng gốc.”

**Câu 3. “Nếu tôi dị ứng hải sản và gõ ‘hải sản’, hệ thống có loại tôm cua cá không?”**
- Trả lời: “Trong 30 lượt thử, **không lượt nào còn món biển** sau khi loại trừ token ‘hải sản’ (`[C21]` = 0). Bộ dò chuỗi con của auditor vẫn ghi 2 lượt, nhưng đó là false-positive như ‘Gạo nếp **cái**’ chứa ‘cá’. Giới hạn còn lại: taxonomy hiện chỉ phủ một số nhóm thực phẩm, dị ứng ngoài các nhóm đó vẫn dựa vào so khớp chuỗi.”

**Câu 4. “Điểm fitness nghĩa là gì với bệnh nhân? Bấm Đổi món 5 lần thì điểm có đổi không?”**
- Trả lời: “Fitness là hàm mục tiêu nội bộ, không phải chỉ số sức khỏe. `SwapOut` **có** trả `fitness` (62/62 menu swap), nên giao diện cập nhật được điểm sau mỗi lần đổi món. Vấn đề còn lại là ý nghĩa: một con số 0–100 không cho người bệnh biết đang thiếu hay thừa chất gì.”

**Câu 5. “Vì sao bảng thực đơn có nhiều món là nguyên liệu thô như ‘Măng tre 220 g’?”**
- Trả lời: “Tên hiển thị đã được ghép thành món: 0/133 menu còn hiển thị tên nguyên liệu thô (`[C19b]`), 0.0% menu có món chính không nêu cách chế biến (`[C20]`). Tuy nhiên 130/133 menu vẫn có nguyên liệu gốc thuộc nhóm thô (`[C19]`), vì dữ liệu dinh dưỡng là bảng theo 100 g nguyên liệu và chưa có bảng món nấu chín tương ứng. Đây là giới hạn dữ liệu, không phải khẩu phần thô được phục vụ. Trong đợt chạy này không có món nào chạm trần khẩu phần ≥349.5 g (`[C15]` = 0).”

## 5. VIỆC CẦN FIX — CHỈ HIỆN KHI CHỈ SỐ TƯƠNG ỨNG KHÁC 0

1. **Dị ứng**: mở rộng taxonomy allergen và bỏ fallback so khớp chuỗi con; 12 lượt trả 400 cần thông điệp nêu rõ món nào đang chặn pool.

## 6. GHI CHÚ THỦ CÔNG — KHÔNG SINH TỪ DỮ LIỆU

> Mục này **cố ý** không suy ra từ `summary.json`. Nó là quan sát giao diện, kiểm bằng cách đọc code frontend, nên **không tự cập nhật** khi chạy lại audit. Sửa UI thì phải sửa tay mục này.

- Bảng thực đơn hiển thị song song khẩu phần thô và khẩu phần đã làm tròn (`portion_g` → `portion_g_rounded`) — `app/static/js/app.js`, khối `renderMenu`.
- Dòng “Tổng ngày” in số tuyệt đối; ngưỡng cá nhân không nằm cạnh con số mà chỉ xuất hiện trong khối vi phạm bên dưới — cùng file, phần `totalRow` và `renderViolations`.
- Seed và cấu hình solver nằm trong `<details class="advanced-settings">` (`app/static/index.html`), đã thu gọn mặc định.
- Thông điệp 422 được Việt hoá ở cả backend và `formatFieldError()` trong `app/static/js/api.js`; cảnh báo bệnh lý hiển thị qua `renderWarnings`.

## 7. BẢNG ĐỐI CHIẾU KHẲNG ĐỊNH ↔ DỮ LIỆU

Mỗi dòng: mã — đường dẫn trong `summary.json` — giá trị đã in ở trên. `scripts/check_audit_report.py <thư-mục>` đọc bảng này, so lại với `summary.json` và báo lệch.

```text
C01	n_requests	246
C02	n_menus	133
C03	n_5xx	0
C04	derived.n_4xx	42
C05	derived.n_400_internal_message	0
C06	derived.n_4xx_english_pydantic	0
C07	menus_with_violation	114
C09	derived.n_menus_fitness_negative	0
C10	sodium.max	2300.8
C11	sodium.n_over_1500	1
C12	derived.n_hyp_menus	43
C13	derived.n_hyp_over_1500	0
C14	derived.n_swap_menus_with_fitness	62
C15	at_cap_menus	0
C16	absurd_menus	0
C17	structure_fail_menus	0
C18	slot0_staple_pct	100.0
C19	raw_menus	130
C19b	raw_display_menus	0
C20	no_prep_pct	0.0
C21	allergy.semantic_leak_runs	0
C22	derived.n_allergy_menus_400	12
C23	determinism.same_ids	True
C23b	determinism.same_portions	True
C24	swap.gap_first_last_delta	9.9
C24b	swap.gap_chain5_delta_signed	-4.1
C25	latency_all.p95	28814.1
C26	derived.diabetes_warn	True
C27	matrix.ok	12
C28	cal_macro_mismatch_pct.max	0.3
C29	swap.n_swap_steps	62
C30	swap.n_chains	5
C31	swap.steps_with_cap	0
C32	swap.max_portion_overall	250.0
C33	sodium.mean	442.1
C34	clinical.hypertension.energy_violation	1
C35	clinical.hypertension.protein_violation	7
C36	inventory.n_foods_sampled	137
```

---
*Số liệu sinh tự động từ 246 request trong 816 giây; toàn bộ phần diễn giải đọc từ `summary.json` (xem §7), không có câu nào viết cứng. Đọc/ghi chỉ trong thư mục `experiments/` của đợt chạy; không đụng dữ liệu production.*
