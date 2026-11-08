# BÁO CÁO PHẢN BIỆN & THẨM ĐỊNH HỆ THỐNG GỢI Ý THỰC ĐƠN DBO/IDBO

- Thời điểm chạy: **806 giây** (~13 phút), **250 request HTTP thực tế** vào server `app.main:app`.
- Server: black-box, không import solver, không sửa dữ liệu.
- Thực đơn thu được để phân tích: **133** `[C02]`.
- Toàn bộ số liệu đọc từ `summary.json`, `raw_requests.jsonl`, `raw_menus.jsonl` trong cùng thư mục.
- **Phần diễn giải ở §2–§6 sinh tự động từ `summary.json`**, không có câu nào viết cứng. Mỗi con số mang mã `[Cxx]`; §7 đối chiếu từng mã với đường dẫn dữ liệu, `scripts/check_audit_report.py` kiểm tra lại tự động.

## 1. BẢNG TỔNG KẾT SỐ LIỆU ĐO ĐƯỢC

| Chỉ số | Giá trị | Mã |
|---|---|---|
| Tổng request | 250 | C01 |
| 200 OK | 206 (82.4%) | — |
| 4xx (từ chối đúng) | 44 | C04 |
| 5xx (lỗi server) | 0 | C03 |
| Lỗi kết nối/timeout | 0 | — |
| Latency TB / trung vị / p95 / max | 3,293.1 / 139.4 / 27245.1 / 34,872.1 ms | C25 |
| Generate `web` (TB / p95) | 26,515.9 / 31,094.4 ms (n=24) | — |
| Generate `smoke` (TB) | 256.9 ms (n=85) | — |
| Menu có ≥1 vi phạm | 112/133 (84.2%) | C07 |
| Fitness TB (menu sinh ra) | 71.5 (min 34.1 – max 99.1) | — |
| Menu có fitness âm | 0 | C09 |
| Sodium cao nhất | 3205.9 mg | C10 |
| Menu vượt 1500 mg natri (mọi hồ sơ) | 5/133 | C11 |
| Menu vượt 2300 mg natri | 1/133 | — |
| Hồ sơ tăng huyết áp: menu / vượt 1500 mg | 43 / 0 | [C12] [C13] |
| Độ lệch dinh dưỡng TB (calo+4 macro) | 20.1% (max 50.8%) | — |
| Menu có món kịch trần ≥349.5 g | 0/133 (0.0%) | C15 |
| Menu có khẩu phần phản ẩm thực | 0/133 | C16 |
| Menu sai cơ cấu bữa trưa/tối | 0/133 (0.0%) | C17 |
| Menu sai vai trò slot ẩm thực | 7/133 (5.3%) | — |
| Slot đầu bữa trưa/tối đúng là tinh bột | 100.0% (266 slot) | C18 |
| Menu chứa gia vị như món độc lập | 0/133 | — |
| Menu có nguyên liệu gốc bị coi là thô | 132/133 | C19 |
| Menu hiển thị tên nguyên liệu thô | 0/133 | C19b |
| Menu có món chính không nêu cách chế biến | 0.0% (0/133) | C20 |
| Lượt lọt dị ứng ngữ nghĩa (token “hải sản”) | 0/30 | C21 |
| Lượt lọt dị ứng theo khớp chuỗi con (bộ dò auditor) | 2/30 | — |
| Lượt dị ứng trả 400 | 14/30 | C22 |
| Menu trùng món trong ngày | 0 | — |
| Số bước swap đo được | 62 (max portion 250 g) | — |
| Menu swap có trả `fitness` | 62/62 | C14 |
| Biến thiên gap toàn chuỗi swap | 13.0 điểm % (baseline → cuối) | C24 |
| Biến thiên gap 5 bước cuối | 0.4 điểm % (signed; abs 5.2) | C24b |
| 10 swap đồng thời | {'200': 10} · max 1977.7 ms | — |
| Tái lập cùng seed | ids giống: True · portion giống: True | [C23] [C23b] |
| Ma trận nhân khẩu | 14 OK / 0 lỗi, 0 rerun seed | C27 |
| Nhất quán calo vs 4P+4C+9F | 133 menu kiểm, lệch max 0.3%, 0 menu >10% | C28 |

Phân bố tuổi / BMI / vận động / cấu trúc bữa trong ma trận: `{'18-25': 4, '26-45': 4, '46-65': 3, '>65': 3}`, BMI `{'underweight': 4, 'normal': 4, 'overweight': 4, 'obese1': 2}`, vận động `{'SEDENTARY': 14}`, bữa `{'3meals': 5, '4meals': 5, 'big': 4}`.

> Ghi chú: phần bị cắt do ngân sách thời gian: `{'matrix': 16}`.

## 2. DIỄN GIẢI TỰ ĐỘNG

### 2.1. Lỗi server và thông điệp lỗi

- `[C03]` Không có request nào trả 5xx trên **250** request: server không sập, không rò traceback ra client.
- `[C04]` Trong **44** phản hồi 4xx, **0** phản hồi chứa mẫu lỗi Pydantic tiếng Anh (`Input should…`, `String should…`, `Field required`) `[C06]`.
- `[C05]` Không phản hồi 400 nào chứa thuật ngữ nội bộ (`min_pool_size`).

### 2.2. Swap: fitness, khẩu phần, độ lệch

- Đo được **62** bước swap trên **5** chuỗi `[C29]` `[C30]`.
- `[C14]` `SwapOut` **có** trả `fitness`: **62/62** menu swap có trường này (min 34.11 – max 97.19). Vì vậy báo cáo dùng cả `fitness` (điểm solver trả về) và `gap` (độ lệch dinh dưỡng so với target, đơn vị %, là đại lượng suy ra chứ không phải fitness).
- Chuỗi 5 lần swap cùng slot: **3** chuỗi xấu đi, **2** chuỗi tốt lên, **0** chuỗi không đổi. Biến thiên trung bình đầu→cuối của đúng 5 bước: `[C24b]` **0.4** điểm % (abs 5.2). Toàn chuỗi (gồm các bước tuần tự trước đó): `[C24]` **13.0** điểm %.
  - SwapA: 21.6 → 28.5 (xấu đi), min 21.6, max 28.5
  - SwapB: 46.0 → 50.1 (xấu đi), min 38.7, max 50.8
  - SwapC: 19.8 → 23.0 (xấu đi), min 19.8, max 23.0
  - SwapD: 33.9 → 32.5 (tốt lên), min 15.7, max 33.9
  - SwapE: 31.2 → 20.6 (tốt lên), min 15.1, max 31.2
- `[SUY RA]` Dữ liệu cho thấy `gap` có thể **tăng** sau swap; audit này không ghi nhận cơ chế nào từ chối phương án có `gap`/`fitness` tệ hơn phương án trước.
- Tổng số bước swap có ít nhất một món chạm trần ≥349.5 g: **0/62**; khẩu phần lớn nhất sau swap: **250 g** `[C31]` `[C32]`.

### 2.3. Bệnh lý

- Alias tiếng Việt: `hypertension` → 1500.0 mg, `tăng huyết áp` → 1500.0 mg, `cao huyết áp` → 1500.0 mg.
- `[C26]` Hồ sơ tiểu đường: **3/3** lần gọi trả 200 **đều có trường cảnh báo** (`derived.diabetes_warn = True`) và **đều nhắc tới sugar/đường** trong payload. Danh sách key trả về: `['data_limitations', 'diversity_pct', 'fitness', 'items', 'runtime_s', 'targets', 'totals', 'violations', 'warnings']`.
- Bệnh lý không được mô hình hoá: `gout` → 2300.0 mg; `suy thận` → 2300.0 mg — trả 200 nhưng `sodium_target` không đổi so với hồ sơ khỏe mạnh, tức không có ngưỡng riêng và không có cảnh báo “chưa hỗ trợ” trong payload.

### 2.4. Natri

- Toàn bộ 133 menu: natri TB **543.1 mg** `[C33]`, cao nhất `[C10]` **3,205.9 mg**; `[C11]` **5** menu vượt 1500 mg và **1** menu vượt 2300 mg.
- Hồ sơ tăng huyết áp: `[C12]` **43** menu, target trả về `[1500.0]` mg; `[C13]` **0** menu vượt 1500 mg (0 vượt cả 2300 mg), natri cao nhất **1,172.6 mg**.
- `[SUY RA]` Trong bộ seed này không có menu nào vượt 1500 mg; đây là kết quả trong phạm vi thử nghiệm, không phải bảo đảm lâm sàng. Ràng buộc natri vẫn là kiểm tra sau khi giải, không phải ràng buộc cứng của solver.
- Hệ quả siết muối: **1 menu vi phạm năng lượng**, **5 menu vi phạm đạm** trên cùng bộ seed `[C34]` `[C35]`.

### 2.5. Dị ứng

- `[C22]` 30 lượt sinh menu với nhiều cấu hình token loại trừ (đơn, bộ ba, 10 và 20 token); trạng thái: `{'200': 16, '400': 14}`; **14** lượt trả 400.
- `[C21]` Lượt còn món biển sau khi loại trừ token **“hải sản”**: **0/30** (khớp theo ranh giới từ, không phải chuỗi con).
- Bộ dò của auditor còn ghi **2** lượt “lọt” theo **khớp chuỗi con**: `[{'label': 'single:cá', 'leaks': ['Cơm gạo nếp cái']}, {'label': 'triple:tôm+cua+cá', 'leaks': ['Cơm gạo nếp cái']}]`. Đây là false-positive của bộ dò (ví dụ “Gạo nếp **cái**” chứa “cá”), không phải món hải sản; chỉ số đúng là `[C21]`.
- Loại trừ **một** nhóm quen thuộc cũng làm hỏng yêu cầu: `['single:bò', 'single:trứng', 'single:sữa']` trả 400, vì pool ứng viên còn lại nhỏ hơn `min_pool_size`. Hệ thống từ chối tạo thực đơn thay vì crash, nhưng người dùng không nhận được gợi ý nới điều kiện.

### 2.6. Khẩu phần và ẩm thực

- `[C15]` Menu có món chạm trần ≥349.5 g: **0/133** (0.0%). `[C16]` Khẩu phần bị coi là phản ẩm thực: **0** menu.
- `[C18]` Slot đầu bữa trưa/tối đúng là tinh bột: **100.0%** trên 266 slot; `[C17]` **0/133** (0.0%) menu bị coi là sai cơ cấu bữa.
- `[CẢNH BÁO ĐO LƯỜNG]` Auditor phân vai trò món bằng **từ vựng độc lập** với `DishRole` của hệ thống, nên 100% “sai” không đồng nghĩa 100% lỗi sản phẩm. Phải đối chiếu hai định nghĩa slot trước khi sửa theo con số này.
- `[C19]` **132/133** menu có nguyên liệu gốc thuộc nhóm bị bộ dò coi là thô; `[C19b]` **0/133** menu còn hiển thị tên nguyên liệu thô; `[C20]` **0.0%** menu có món chính không nêu cách chế biến. C19 là giới hạn dữ liệu gốc (bảng dinh dưỡng theo 100 g nguyên liệu), không phải lỗi dinh dưỡng; C19b/C20 đo lớp ghép món hiển thị và phải đọc cùng C19.
- Không có menu nào chứa gia vị như món độc lập trong đợt chạy này.
- `[C28]` Nhất quán calo vs 4P+4C+9F: lệch lớn nhất **0.3%**, **0** menu lệch >10%.

### 2.7. Dữ liệu món ăn

- Mẫu **137** món `[C36]` lấy từ `/api/foods`; trong mẫu đó có **0** tên gia vị, **13** tên nguyên liệu thô, **97** tên không nêu cách chế biến.
- Natri/100 g cao nhất: `[('Dưa chuột hộp', 1208.0), ('Tôm đồng', 418.0), ('Sữa bò tươi', 380.0), ('Nước ép cà chua', 269.0), ('Bầu dục bò', 200.0)]` — những món này một mình đã chiếm phần lớn ngưỡng 1500 mg/ngày.

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

**1. [swap] SwapA:seq:breakfast_0** — 2,322 kcal, natri 1,500 mg, lệch target 36.6%
   - Món: Khoai tây luộc 250g; Sữa bò tươi xào 180g; Cơm gạo lứt 250g; Măng chua luộc 220g; Cơm gạo nếp cái 250g; Tôm đồng hấp 180g; Chanh (ăn tươi) 200g
   - Nguyên liệu thô (theo bộ dò): Khoai tây; Gạo lứt; Gạo nếp cái
   - Vi phạm: protein_g: 90.3 outside [100.8, 136.4]; carbs_g: 441.2 outside [252.0, 340.9]; fat_g: 22.5 outside [63.2, 94.9]; fiber_g: 24.1 outside [26.6, 49.4]

**2. [allergy] single:heo** — 1,838 kcal, natri 881 mg, lệch target 30.3%
   - Món: Khoai tây luộc 150g; Đậu hà lan (hạt) (ăn tươi) 200g; Cơm gạo lứt 125g; Rau mồng tơi luộc 220g; Ngô bắp tươi luộc 165g; Tôm đồng hấp 180g; Lựu (ăn tươi) 165g
   - Nguyên liệu thô (theo bộ dò): Khoai tây; Đậu hà lan (hạt); Gạo lứt
   - Vi phạm: energy 1838 kcal outside [2134, 2609]; fat_g: 13.9 outside [63.2, 94.9]

**3. [swap] SwapD:seq:lunch_1** — 1,614 kcal, natri 270 mg, lệch target 27.5%
   - Món: Đậu xanh (đậu tắt) hấp 100g; Đậu phụ sốt cà 70g; Cơm gạo tẻ giã 130g; Cá thu áp chảo 180g; Cơm gạo lứt 100g; Thịt lợn nạc xào 60g; Hồng ngâm (ăn tươi) 120g
   - Nguyên liệu thô (theo bộ dò): Đậu xanh (đậu tắt); Gạo tẻ giã; Gạo lứt
   - Vi phạm: protein_g: 94.3 outside [69.6, 94.2]; fat_g: 33.3 outside [43.7, 65.5]; fiber_g: 12.3 outside [26.6, 49.4]

**4. [clinical] hyp_seed126** — 1,967 kcal, natri 1,173 mg, lệch target 27.1%
   - Món: Đậu xanh (đậu tắt) hấp 100g; Trứng vịt luộc 150g; Cơm gạo nếp cái 100g; Tôm đồng hấp 160g; Cơm gạo nếp máy (loại thường) 160g; Lưỡi lợn hầm 165g; Nho ta (nho chua) (ăn tươi) 200g
   - Nguyên liệu thô (theo bộ dò): Đậu xanh (đậu tắt); Gạo nếp cái; Gạo nếp máy (loại thường)
   - Vi phạm: protein_g: 118.6 outside [78.0, 105.6]; fiber_g: 10.9 outside [26.6, 49.4]

**5. [clinical] hyp_seed110** — 2,222 kcal, natri 218 mg, lệch target 25.2%
   - Món: Đậu tương (đậu nành) hấp 215g; Sữa dê tươi (ăn tươi) 120g; Cơm gạo lứt 175g; Rau kinh giới luộc 150g; Cơm gạo nếp cái 140g; Cà rốt (củ đỏ, vàng) luộc 220g; Chuối tây (ăn tươi) 135g
   - Nguyên liệu thô (theo bộ dò): Đậu tương (đậu nành); Gạo lứt; Gạo nếp cái
   - Vi phạm: energy 2223 kcal outside [1652, 2020]; protein_g: 111.0 outside [78.0, 105.6]; carbs_g: 328.1 outside [195.1, 263.9]

**6. [clinical] hyp_seed125** — 1,931 kcal, natri 94 mg, lệch target 19.7%
   - Món: Đậu xanh (đậu tắt) hấp 175g; Đậu phụ sốt cà 80g; Cơm gạo tẻ giã 110g; Măng tây luộc 125g; Cơm gạo nếp máy (loại thường) 100g; Đuôi lợn hầm 100g; Mít dai (ăn tươi) 145g
   - Nguyên liệu thô (theo bộ dò): Đậu xanh (đậu tắt); Gạo tẻ giã; Gạo nếp máy (loại thường)
   - Vi phạm: carbs_g: 268.4 outside [195.1, 263.9]; fiber_g: 14.4 outside [26.6, 49.4]

## 4. CÂU HỎI “BẪY” VÀ CÂU TRẢ LỜI SINH TỪ SỐ LIỆU

**Câu 1. “Hệ thống khẳng định thực đơn an toàn cho người tăng huyết áp. Vậy vì sao có seed ra 1,173 mg natri?”**
- Trả lời: “Không. Chúng em chỉ khẳng định thực đơn **đáp ứng hoặc không đáp ứng ngưỡng được cấu hình trong thử nghiệm**. Trong 43 thực đơn của hồ sơ tăng huyết áp, 0 thực đơn vượt 1500 mg và hệ thống báo vi phạm đúng; đây là hạn chế của bộ giải, không phải bảo đảm lâm sàng. Đây không phải thiết bị y tế.”

**Câu 2. “Món ‘Gạo lứt 115 g’ là món gì? Ai ăn gạo sống?”**
- Trả lời: “Dữ liệu gốc là bảng thành phần dinh dưỡng theo 100 g nguyên liệu, nên tên hiển thị hiện là tên nguyên liệu; 0.0% thực đơn trong đợt test dính vấn đề này. Đây là khoảng trống giữa dữ liệu dinh dưỡng và thực đơn ẩm thực, không phải kết quả tối ưu. Hướng khắc phục là lớp tên món ăn, chỉ chạm hiển thị, không đổi hàm dinh dưỡng.”

**Câu 3. “Nếu tôi dị ứng hải sản và gõ ‘hải sản’, hệ thống có loại tôm cua cá không?”**
- Trả lời: “Trong 30 lượt thử, **không lượt nào còn món biển** sau khi loại trừ token ‘hải sản’ (`[C21]` = 0). Bộ dò chuỗi con của auditor vẫn ghi 2 lượt, nhưng đó là false-positive như ‘Gạo nếp **cái**’ chứa ‘cá’. Giới hạn còn lại: taxonomy hiện chỉ phủ một số nhóm thực phẩm, dị ứng ngoài các nhóm đó vẫn dựa vào so khớp chuỗi.”

**Câu 4. “Điểm fitness nghĩa là gì với bệnh nhân? Bấm Đổi món 5 lần thì điểm có đổi không?”**
- Trả lời: “Fitness là hàm mục tiêu nội bộ, không phải chỉ số sức khỏe. `SwapOut` **có** trả `fitness` (62/62 menu swap), nên giao diện cập nhật được điểm sau mỗi lần đổi món. Vấn đề còn lại là ý nghĩa: một con số 0–100 không cho người bệnh biết đang thiếu hay thừa chất gì.”

**Câu 5. “Vì sao bảng thực đơn có nhiều món là nguyên liệu thô như ‘Măng tre 220 g’?”**
- Trả lời: “Tên hiển thị đã được ghép thành món: 0/133 menu còn hiển thị tên nguyên liệu thô (`[C19b]`), 0.0% menu có món chính không nêu cách chế biến (`[C20]`). Tuy nhiên 132/133 menu vẫn có nguyên liệu gốc thuộc nhóm thô (`[C19]`), vì dữ liệu dinh dưỡng là bảng theo 100 g nguyên liệu và chưa có bảng món nấu chín tương ứng. Đây là giới hạn dữ liệu, không phải khẩu phần thô được phục vụ. Trong đợt chạy này không có món nào chạm trần khẩu phần ≥349.5 g (`[C15]` = 0).”

## 5. VIỆC CẦN FIX — CHỈ HIỆN KHI CHỈ SỐ TƯƠNG ỨNG KHÁC 0

1. **Dị ứng**: mở rộng taxonomy allergen và bỏ fallback so khớp chuỗi con; 14 lượt trả 400 cần thông điệp nêu rõ món nào đang chặn pool.

## 6. GHI CHÚ THỦ CÔNG — KHÔNG SINH TỪ DỮ LIỆU

> Mục này **cố ý** không suy ra từ `summary.json`. Nó là quan sát giao diện, kiểm bằng cách đọc code frontend, nên **không tự cập nhật** khi chạy lại audit. Sửa UI thì phải sửa tay mục này.

- Bảng thực đơn hiển thị song song khẩu phần thô và khẩu phần đã làm tròn (`portion_g` → `portion_g_rounded`) — `app/static/js/app.js`, khối `renderMenu`.
- Dòng “Tổng ngày” in số tuyệt đối; ngưỡng cá nhân không nằm cạnh con số mà chỉ xuất hiện trong khối vi phạm bên dưới — cùng file, phần `totalRow` và `renderViolations`.
- Seed và cấu hình solver nằm trong `<details class="advanced-settings">` (`app/static/index.html`), đã thu gọn mặc định.
- Thông điệp 422 được Việt hoá ở cả backend và `formatFieldError()` trong `app/static/js/api.js`; cảnh báo bệnh lý hiển thị qua `renderWarnings`.

## 7. BẢNG ĐỐI CHIẾU KHẲNG ĐỊNH ↔ DỮ LIỆU

Mỗi dòng: mã — đường dẫn trong `summary.json` — giá trị đã in ở trên. `scripts/check_audit_report.py <thư-mục>` đọc bảng này, so lại với `summary.json` và báo lệch.

```text
C01	n_requests	250
C02	n_menus	133
C03	n_5xx	0
C04	derived.n_4xx	44
C05	derived.n_400_internal_message	0
C06	derived.n_4xx_english_pydantic	0
C07	menus_with_violation	112
C09	derived.n_menus_fitness_negative	0
C10	sodium.max	3205.9
C11	sodium.n_over_1500	5
C12	derived.n_hyp_menus	43
C13	derived.n_hyp_over_1500	0
C14	derived.n_swap_menus_with_fitness	62
C15	at_cap_menus	0
C16	absurd_menus	0
C17	structure_fail_menus	0
C18	slot0_staple_pct	100.0
C19	raw_menus	132
C19b	raw_display_menus	0
C20	no_prep_pct	0.0
C21	allergy.semantic_leak_runs	0
C22	derived.n_allergy_menus_400	14
C23	determinism.same_ids	True
C23b	determinism.same_portions	True
C24	swap.gap_first_last_delta	13.0
C24b	swap.gap_chain5_delta_signed	0.4
C25	latency_all.p95	27245.1
C26	derived.diabetes_warn	True
C27	matrix.ok	14
C28	cal_macro_mismatch_pct.max	0.3
C29	swap.n_swap_steps	62
C30	swap.n_chains	5
C31	swap.steps_with_cap	0
C32	swap.max_portion_overall	250.0
C33	sodium.mean	543.1
C34	clinical.hypertension.energy_violation	1
C35	clinical.hypertension.protein_violation	5
C36	inventory.n_foods_sampled	137
```

---
*Số liệu sinh tự động từ 250 request trong 806 giây; toàn bộ phần diễn giải đọc từ `summary.json` (xem §7), không có câu nào viết cứng. Đọc/ghi chỉ trong thư mục `experiments/` của đợt chạy; không đụng dữ liệu production.*
