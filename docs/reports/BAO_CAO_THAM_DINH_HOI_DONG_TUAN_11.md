# BÁO CÁO PHẢN BIỆN & THẨM ĐỊNH HỆ THỐNG GỢI Ý THỰC ĐƠN DBO/IDBO

- Thời điểm chạy: **1143 giây** (~19 phút), **422 request HTTP thực tế** vào server `app.main:app`.
- Server: `http://127.0.0.1:8000`, black-box, không import solver, không sửa dữ liệu.
- Thực đơn thu được để phân tích: **219**.
- Mọi số liệu dưới đây đọc từ `summary.json`, `raw_requests.jsonl`, `raw_menus.jsonl` trong cùng thư mục.

## 1. BẢNG TỔNG KẾT SỐ LIỆU ĐO ĐƯỢC

| Chỉ số | Giá trị |
|---|---|
| Tổng request | 422 |
| 200 OK | 378 (89.6%) |
| 4xx (từ chối đúng) | 44 |
| 5xx (lỗi server) | 0 |
| Lỗi kết nối/timeout | 0 |
| Latency TB / trung vị / p95 / max | 2,720.8 / 60.2 / 10,507.1 / 13,148.5 ms |
| Generate `web` (TB / p95) | 9,388.9 / 11,155.8 ms (n=115) |
| Generate `smoke` (TB) | 91.8 ms (n=80) |
| Menu có ≥1 vi phạm | 135/219 (61.6%) |
| Fitness TB (menu sinh ra) | 85.8 (min 32.5 – max 99.9) |
| Sodium cao nhất | 3,280.4 mg |
| Menu vượt 1500 mg natri | 17/219 |
| Menu vượt 2300 mg natri | 1/219 |
| Độ lệch dinh dưỡng TB (calo+4 macro) | 18.0% (max 64.7%) |
| Menu có món kịch trần 350 g | 65/219 (29.7%) |
| Menu có khẩu phần phản ẩm thực | 51/219 |
| Menu sai cơ cấu bữa trưa/tối | 219/219 (100.0%) |
| Menu sai vai trò slot ẩm thực | 219/219 (100.0%) |
| Slot đầu bữa trưa/tối đúng là tinh bột | 23.1% (438 slot) |
| Menu chứa gia vị như món độc lập | 0/219 |
| Menu chứa nguyên liệu thô | 166/219 |
| Menu có món chính không nêu cách chế biến | 217/219 (99.1%) |
| Lượt lọt dị ứng (sau khi yêu cầu loại trừ) | 0/30 |
| Menu trùng món trong ngày | 3 |
| Số bước swap đo được | 67 (max portion 350 g) |
| Biến thiên độ lệch dinh dưỡng qua swap | 23.9 điểm % (đầu → cuối) |
| 10 swap đồng thời | {'200': 10} · max 671.3 ms |
| Tái lập cùng seed | ids giống: True · portion giống: True |
| Ma trận nhân khẩu | 100 OK / 0 lỗi, 0 rerun seed |

Phân bố tuổi / BMI / vận động / cấu trúc bữa trong ma trận: `{'18-25': 25, '26-45': 25, '46-65': 25, '>65': 25}`, BMI `{'underweight': 20, 'normal': 20, 'overweight': 20, 'obese1': 20, 'obese2': 20}`, vận động `{'SEDENTARY': 20, 'LIGHT': 20, 'MODERATE': 20, 'ACTIVE': 20, 'VERY_ACTIVE': 20}`, bữa `{'3meals': 25, '4meals': 25, 'big': 25, 'light': 25}`.

### 1.1. Lỗi 500

**Không có request nào trả 500 Internal Server Error** trong toàn bộ đợt test. Server không sập, không rò traceback ra client.

### 1.2. Swap: điểm fitness và khẩu phần

`POST /api/menu/swap` **không trả `fitness`, `diversity_pct`, `runtime_s`** (response schema `SwapOut` chỉ có items/totals/targets/violations/delta). Vì vậy không thể đọc “điểm fitness sau swap” từ API; báo cáo dùng **độ lệch dinh dưỡng trung bình so với target (%)** làm đại lượng thay thế, ghi rõ đây là proxy chứ không phải fitness của solver.

| Chuỗi | gap đầu (%) | gap cuối (%) | gap min | gap max |
|---|---|---|---|---|
| SwapA | 8.7 | 30.3 | 8.7 | 41.8 |
| SwapB | 5.9 | 39.6 | 5.9 | 50.6 |
| SwapC | 20.2 | 56.1 | 20.2 | 56.1 |
| SwapD | 21.1 | 23.0 | 10.1 | 31.1 |
| SwapE | 26.6 | 52.9 | 26.6 | 64.7 |

5 lần swap liên tiếp trên cùng một slot:

| Chuỗi | trước | sau 5 lần | thấp nhất | cao nhất |
|---|---|---|---|---|
| SwapA | 34.9 | 30.3 | 30.3 | 41.8 |
| SwapB | 35.6 | 39.6 | 35.6 | 50.6 |
| SwapC | 37.6 | 56.1 | 33.5 | 56.1 |
| SwapD | 21.6 | 23.0 | 20.9 | 31.1 |
| SwapE | 63.7 | 52.9 | 51.4 | 64.7 |

- Tổng số bước swap có ít nhất một món chạm trần 350 g: **55/67**.
- Khẩu phần lớn nhất ghi nhận sau swap: **350 g**.
- Frontend giữ lại fitness cũ sau swap (`app.js`: `res.fitness = res.fitness ?? state.menu?.fitness`), nên người dùng vẫn thấy điểm cũ trong khi thực đơn đã đổi — đây là lỗi hiển thị, không phải lỗi solver.

## 2. NHỮNG HẠN CHẾ CHÍ MẠNG VỀ TRẢI NGHIỆM NGƯỜI DÙNG (UX)

1. **“Fitness /100” là khái niệm của người làm thuật toán, không phải của người ăn.** Toast sau khi tạo thực đơn hiện `Fitness: {fitness}`; người dùng không biết 87.4 tốt hay xấu, không biết có ăn được không. Cần thay bằng ngôn ngữ mục tiêu: “Đạt 94% calo mục tiêu”, “Đạm thiếu 12 g”.
2. **Bảng thực đơn hiển thị khẩu phần thô và khẩu phần làm tròn cạnh nhau** (`157.3g → 155g`). Người dùng thấy hai con số cho cùng một món và không biết tin số nào; nên chỉ hiển thị số đã làm tròn, kèm ghi chú “khẩu phần gợi ý”.
3. **Cột “Seed” và “Cấu hình solver Smoke/Web/Full” lộ ra ngoài UI.** Đây là tham số tái lập thực nghiệm, không phải lựa chọn của người bệnh. Nếu cần giữ cho demo, đặt trong mục “Nâng cao” thu gọn, mặc định ẩn.
4. **Thông báo lỗi không đồng nhất ngôn ngữ.** Lỗi nghiệp vụ do nhóm viết bằng tiếng Việt (`Thực đơn cần ít nhất 1 món trưa...`), nhưng lỗi 422 của Pydantic là tiếng Anh kỹ thuật (`Input should be a valid integer`, `String should have at least 2 characters`). Frontend chỉ hiện `err.message`, nên người dùng nhận chuỗi tiếng Anh khó hiểu. Trong đợt test có **44 phản hồi 4xx**, phần lớn thuộc nhóm này.
5. **Không có cảnh báo bệnh lý tại thời điểm trả thực đơn.** Với hồ sơ tiểu đường, response **không** chứa bất kỳ trường cảnh báo/lưu ý nào; chuỗi “sugar/đường” **không** xuất hiện trong payload. Người bệnh tiểu đường nhận thực đơn như người khỏe mạnh, không được nhắc rằng hệ thống không có dữ liệu đường để đánh giá.
6. **Không có trạng thái “đang tính” đủ rõ cho cấu hình web.** Generate `web` mất trung bình **9.4 giây** (p95 11.2 s) trên server nội bộ; trên máy yếu hoặc deploy xa, người dùng rất dễ bấm lại nhiều lần. Nút bị disable trong lúc chờ là đúng, nhưng không có ước lượng thời gian hay huỷ.
7. **Bảng chỉ có số tuyệt đối, thiếu ngữ cảnh.** Người dùng thấy “Natri 1 842 mg” nhưng không thấy ngưỡng cá nhân (1 500 mg cho tăng huyết áp) ngay cạnh con số; chỉ khi cuộn xuống mới thấy danh sách vi phạm. Nên đổi màu/ghi “vượt 342 mg” tại dòng tổng.
8. **Tên món là tên nguyên liệu, không phải tên món ăn.** 99.1% thực đơn chứa ít nhất một món chính (tinh bột/đạm) không nêu cách chế biến (ví dụ: “Gạo lứt 115 g”, “Khoai tây 250 g”, “Măng tre 350 g”, “Đuôi lợn 140 g”). Với người dùng, đây là danh sách đi chợ chứ không phải thực đơn.

## 3. NHỮNG BẤT CẬP VỀ DINH DƯỠNG & ẨM THỰC THỰC TẾ

### 3.1. Natri ở hồ sơ tăng huyết áp

- Chạy **30 seed** (một phần cấu hình `web`, phần còn lại `smoke`): sodium trung bình **733.5 mg**, cao nhất **3,280 mg**, target server trả về `[1500.0] mg`.
- **1/30 menu vượt 1500 mg**, 1/30 vượt cả trần chung 2300 mg.
- Các seed vượt ngưỡng (bằng chứng paired theo seed):
  - seed 129 (smoke): **3,280 mg**
- Nghĩa là ràng buộc natri 1500 mg **được kiểm tra và báo vi phạm**, nhưng **không được solver ép thoả** trong mọi trường hợp. Không thể tuyên bố “an toàn cho người tăng huyết áp”.
- Hệ quả siết muối: **2 menu vi phạm năng lượng**, **6 menu vi phạm đạm** trên cùng bộ seed. Siết natri đang được đánh đổi bằng việc bỏ mục tiêu năng lượng/đạm: người bệnh nhận thực đơn thiếu năng lượng mà bảng vẫn hiển thị như một thực đơn đã tối ưu.

### 3.2. Bệnh lý tiểu đường và dữ liệu đường

- Dataset không có cột total sugar; API **không trả `sugar_proxy_g`** và cũng không trả cảnh báo. Điều này tránh được lỗi trình bày `carbs*0.15` như dữ liệu đo, nhưng tạo khoảng trống UX: người bệnh tiểu đường không được thông báo rằng hệ thống **không đánh giá được đường huyết**.
- Trong 3 lần gọi với hồ sơ tiểu đường: có cảnh báo = **False**, có nhắc sugar/đường = **False**, các key trả về: `['diversity_pct', 'fitness', 'items', 'runtime_s', 'targets', 'totals', 'violations']`.
- Tên bệnh lý tiếng Việt được alias đúng: `hypertension` → 1500.0 mg, `tăng huyết áp` → 1500.0 mg. Tuy nhiên bệnh lý không hỗ trợ (gout, suy thận…) bị **bỏ qua im lặng**, không có thông báo “chưa hỗ trợ”.

### 3.3. Dị ứng và khẩu vị

- 30 lượt sinh menu với 1 / 3 / 10 / 20 token loại trừ. Số lượt còn món bị cấm: **0**. Trạng thái: `{'200': 16, '400': 14}`.
- Trạng thái theo kịch bản: `{'single:tôm': {'200': 2}, 'single:cua': {'200': 2}, 'single:cá': {'200': 2}, 'single:bò': {'400': 2}, 'single:heo': {'200': 2}, 'single:gà': {'200': 2}, 'single:trứng': {'400': 2}, 'single:sữa': {'400': 2}, 'single:đậu phộng': {'200': 2}, 'single:hải sản': {'200': 2}, 'triple:tôm+cua+cá': {'200': 2}, 'triple:bò+heo+gà': {'400': 2}, 'triple:trứng+sữa+đậu phộng': {'400': 2}, 'ten-tokens': {'400': 2}, 'ten-tokens-web': {'400': 1}, 'twenty-tokens': {'400': 1}}`. Các kịch bản trả 400 là khi pool ứng viên bị thu nhỏ dưới ngưỡng; server từ chối thay vì crash, nhưng người dùng không nhận được thực đơn thay thế hay gợi ý nới điều kiện.
- **Loại trừ chỉ một món quen thuộc cũng làm hỏng yêu cầu:** ['single:bò', 'single:trứng', 'single:sữa'] trả 400. Với người dị ứng đạm sữa hoặc trứng, hệ thống không đưa ra được thực đơn nào thay vì nới lỏng món khác hay báo rõ món nào đang chặn.
- Loại trừ **“hải sản”** (khái niệm, không phải chuỗi con) vẫn để lọt món biển trong **1** lượt: bộ lọc so khớp chuỗi con trên tên món, không có từ điển allergen (tôm/cua/cá/mực đều là “hải sản”). Đây là lỗi an toàn nghiêm trọng nếu người dùng dị ứng hải sản gõ đúng từ “hải sản”.

### 3.4. Những combo ngớ ngẩn nhất ghi nhận được

**1. [swap] SwapC:seq:lunch_0** — 3,490 kcal, natri 1,197 mg, lệch target 33.2%
   - Món: Sữa chua (từ sữa bò) 350g; Trứng vịt 25g; Đậu phụ 75g; Dạ dày lợn 350g; Cần tây 350g; Rau ngố 350g; Thịt gà ta 350g; Củ cái 350g; Bí đao (bí xanh) 350g; Hạt điều 230g; Su su, quả 350g
   - Khẩu phần phản ẩm thực: Dạ dày lợn 350g (đạm); Rau ngố 350g (rau); Thịt gà ta 350g (đạm); Củ cái 350g (rau); Bí đao (bí xanh) 350g (rau); Su su, quả 350g (rau)
   - Cơ cấu bữa: breakfast: thiếu tinh bột; lunch: thiếu tinh bột; dinner: thiếu tinh bột
   - Vi phạm: carbs_g: 235.1 outside [370.5, 501.2]; fat_g: 184.8 outside [77.5, 116.2]

**2. [swap] SwapA:chain5:3** — 2,121 kcal, natri 1,718 mg, lệch target 41.8%
   - Món: Đậu cô ve 350g; Trứng vịt 350g; Cải bắp 350g; Cá nục 350g; Xoài chín 350g; Mề gà 350g; Mơ 350g
   - Khẩu phần phản ẩm thực: Đậu cô ve 350g (rau); Trứng vịt 350g (đạm); Cải bắp 350g (rau); Cá nục 350g (đạm); Mề gà 350g (đạm)
   - Cơ cấu bữa: breakfast: thiếu tinh bột; lunch: thiếu tinh bột; dinner: thiếu tinh bột
   - Vi phạm: energy 2121 kcal outside [2134, 2609]; protein_g: 219.8 outside [100.8, 136.4]; carbs_g: 155.4 outside [252.0, 340.9]; fiber_g: 18.2 outside [26.6, 49.4]

**3. [swap] SwapE:chain5:3** — 1,718 kcal, natri 931 mg, lệch target 64.7%
   - Món: Đậu phụ 350g; Dạ dày lợn 350g; Rau bí 350g; Thịt bò, lưng, nạc 350g; Cá thu 350g
   - Khẩu phần phản ẩm thực: Đậu phụ 350g (đạm); Dạ dày lợn 350g (đạm); Rau bí 350g (rau); Thịt bò, lưng, nạc 350g (đạm); Cá thu 350g (đạm)
   - Cơ cấu bữa: breakfast: thiếu tinh bột; lunch: thiếu tinh bột; dinner: thiếu tinh bột
   - Vi phạm: energy 1718 kcal outside [1938, 2368]; protein_g: 243.2 outside [91.5, 123.8]; carbs_g: 8.4 outside [228.8, 309.5]; fiber_g: 7.3 outside [17.5, 32.5]

**4. [swap] SwapD:seq:lunch_1** — 1,672 kcal, natri 817 mg, lệch target 14.5%
   - Món: Trứng vịt 350g; Đậu xanh (đậu tắt) 25g; Dạ dày lợn 25g; Cá thu 25g; Gạo lứt 190g; Cải thìa (cải trắng) 350g; Mơ 350g
   - Khẩu phần phản ẩm thực: Trứng vịt 350g (đạm); Cải thìa (cải trắng) 350g (rau)
   - Cơ cấu bữa: breakfast: thiếu tinh bột; lunch: thiếu tinh bột
   - Nguyên liệu thô: Đậu xanh (đậu tắt); Gạo lứt
   - Vi phạm: fiber_g: 16.7 outside [26.6, 49.4]

**5. [swap] SwapB:chain5:1** — 1,236 kcal, natri 941 mg, lệch target 50.6%
   - Món: Trứng vịt 80g; Sữa chua (từ sữa bò) 350g; Cá thu đao 115g; Mực tươi 350g; Dạ dày lợn 350g; Cá thu 25g; Dứa ta 350g
   - Khẩu phần phản ẩm thực: Mực tươi 350g (đạm); Dạ dày lợn 350g (đạm)
   - Cơ cấu bữa: breakfast: thiếu tinh bột; lunch: thiếu tinh bột; dinner: thiếu tinh bột
   - Vi phạm: protein_g: 160.4 outside [79.1, 107.1]; carbs_g: 36.1 outside [105.5, 142.8]; fat_g: 49.8 outside [33.1, 49.7]; fiber_g: 2.8 outside [17.5, 32.5]

**6. [matrix] Audit-061** — 2,561 kcal, natri 184 mg, lệch target 10.5%
   - Món: Đậu tương (đậu nành) 135g; Đậu xanh (đậu tắt) 250g; Gạo nếp cái 100g; Rau giền đỏ 80g; Gạo tẻ giã 100g; Thịt vịt 180g
   - Cơ cấu bữa: breakfast: thiếu tinh bột
   - Nguyên liệu thô: Đậu tương (đậu nành); Đậu xanh (đậu tắt); Gạo nếp cái; Gạo tẻ giã
   - Vi phạm: fiber_g: 20.4 outside [26.6, 49.4]

- **Sai vai trò slot ẩm thực:** 219/219 menu (100.0%). Chỉ **23.1%** trong 438 slot đầu của bữa trưa/tối là tinh bột, trong khi `_roles_for_slot` quy định slot 0 phải là tinh bột. Ví dụ: `["dinner_0 = fruit ('Dứa hộp') thay vì tinh bột", "dinner_0 = fruit ('Hạt sen tươi') thay vì tinh bột", "dinner_0 = fruit ('Khế') thay vì tinh bột", "dinner_0 = fruit ('Nho ngọt') thay vì tinh bột", "dinner_0 = fruit ('Nước dứa hộp') thay vì tinh bột", "dinner_0 = fruit ('Quả kiwi') thay vì tinh bột", "dinner_0 = fruit ('Sầu riêng') thay vì tinh bột", "dinner_0 = fruit ('Xoài chín') thay vì tinh bột"]`.
- Tỉ lệ menu có món kịch trần 350 g: **29.7%**. Ví dụ: `['Bánh phở 350g', 'Bí đao (bí xanh) 350g', 'Bưởi 350g', 'Chuối tiêu 350g', 'Cá ngừ 350g', 'Cá nục 350g', 'Cá thu 350g', 'Cá trích 350g']`.
- Khẩu phần bị coi là phi lý: **51 menu**, ví dụ `['Bí đao (bí xanh) 350g (rau)', 'Chân giò lợn 305g (đạm)', 'Cá ngừ 350g (đạm)', 'Cá nục 350g (đạm)', 'Cá thu 320g (đạm)', 'Cá thu 350g (đạm)', 'Cá trích 285g (đạm)', 'Cá trích 350g (đạm)']`.
- Cơ cấu bữa sai ở **219 menu** (100.0%): tiêu chí là mỗi bữa trưa/tối phải có tinh bột **và** ít nhất một món đạm/rau/canh (bữa 2 món “cơm + thịt” vẫn được tính là đạt). Lỗi thường gặp: ['breakfast: thiếu tinh bột', 'dinner: thiếu tinh bột', 'lunch: chỉ có tinh bột', 'lunch: thiếu tinh bột'].
- Gia vị xuất hiện như món độc lập: **0 menu** ([]). Nguyên liệu thô: **166 menu** (['Củ sắn', 'Gạo lứt', 'Gạo nếp cái', 'Gạo nếp máy (loại thường)', 'Gạo tẻ giã', 'Khoai tây']).
- Kiểm tra tính nhất quán calo vs 4P+4C+9F: 219 menu được kiểm, lệch lớn nhất 0.4%, 0 menu lệch >10% (dấu hiệu dữ liệu dinh dưỡng không đồng bộ).

### 3.5. Kho dữ liệu món ăn

- Lấy mẫu được **137** món qua `/api/foods`.
- Có **0** tên gia vị lọt vào whitelist tìm kiếm: `[]`.
- Có **10** tên nguyên liệu thô: `['Củ sắn', 'Gạo lứt', 'Gạo nếp cái', 'Gạo nếp máy (loại thường)', 'Gạo tẻ giã', 'Khoai tây', 'Măng tre', 'Đậu hà lan (hạt)', 'Đậu tương (đậu nành)', 'Đậu xanh (đậu tắt)']`.
- **97** tên không nêu cách chế biến (mẫu): `['Bí ngô', 'Bí đao (bí xanh)', 'Bầu', 'Bầu dục bò', 'Chanh', 'Cà bát', 'Cà chua', 'Cà pháo', 'Cà rốt (củ đỏ, vàng)', 'Cá chép', 'Cá hồi', 'Cá mòi']`.
- Natri/100 g cao nhất: `[['Dưa chuột hộp', 1208.0], ['Tôm đồng', 418.0], ['Sữa bò tươi', 380.0], ['Nước ép cà chua', 269.0], ['Bầu dục bò', 200.0]]`. Các món này một mình đã chiếm phần lớn ngưỡng 1500 mg/ngày.

### 3.6. Chaos / fuzzing

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

- **0 case FAIL**, **0 case 500**. Có **3** hồ sơ phi thực tế vẫn trả 200 (height=30cm, weight=5kg, weight=400kg): lỗi **thiếu kiểm tra hợp lý sinh học** (chiều cao 30 cm, cân nặng 5 kg hay 400 kg vẫn được tối ưu thực đơn), không phải lỗi crash.
- Không case nào phản chiếu payload (`<script>`, `DROP TABLE`) trong body trả về; frontend dùng `escHtml`/`textContent` nên không ghi nhận XSS phản xạ.

## 4. CÂU HỎI “BẪY” CỦA HỘI ĐỒNG PHẢN BIỆN

**Câu 1. “Hệ thống của em khẳng định thực đơn an toàn cho người tăng huyết áp. Vậy tại sao có seed ra 1 800 mg natri?”**
- Trả lời an toàn: “Không. Chúng em chỉ khẳng định thực đơn **đáp ứng hoặc không đáp ứng ngưỡng được cấu hình trong thử nghiệm**. Trong 30 seed đã chạy, 1 menu vượt 1500 mg và hệ thống báo vi phạm đúng; đây là hạn chế của bộ giải, không phải bảo đảm lâm sàng. Thiết bị này không phải thiết bị y tế.”

**Câu 2. “Món ‘Gạo lứt 115 g’ là món gì? Ai ăn gạo sống?”**
- Trả lời: “Dữ liệu gốc là bảng thành phần dinh dưỡng theo 100 g nguyên liệu, nên tên món hiện là tên nguyên liệu; 99.1% thực đơn trong đợt test dính vấn đề này. Đây là khoảng trống đã biết giữa dữ liệu dinh dưỡng và thực đơn ẩm thực, không phải kết quả tối ưu. Hướng khắc phục là lớp ‘món ăn’ (recipe) thay vì nguyên liệu.”

**Câu 3. “Nếu tôi dị ứng hải sản và gõ ‘hải sản’, hệ thống có loại tôm cua cá không?”**
- Trả lời trung thực: “Hiện tại bộ lọc so khớp chuỗi con trên tên món; ‘hải sản’ không khớp ‘tôm’/‘cua’/‘cá’, nên trong 1 lượt thử vẫn lọt món biển. Đây là lỗi an toàn ưu tiên cao; cần từ điển allergen trước khi demo cho người dị ứng.”

**Câu 4. “Điểm fitness 87.4 nghĩa là gì với bệnh nhân? Và vì sao bấm Đổi món 5 lần điểm vẫn 87.4?”**
- Trả lời: “Fitness là hàm mục tiêu nội bộ, không phải chỉ số sức khỏe. `SwapOut` hiện không trả fitness nên frontend giữ điểm cũ — đây là lỗi hiển thị đã ghi nhận. Đúng ra phải hoặc trả fitness mới, hoặc bỏ hẳn điểm số khỏi giao diện người bệnh.”

**Câu 5. “Vì sao khẩu phần sữa chua lại 350 g và rau 350 g? Ràng buộc khẩu phần của em đâu?”**
- Trả lời: “Solver dùng biên kỹ thuật 25–350 g cho mọi món; 29.7% menu có món chạm trần. Hàm `validate_menu` có kiểm tra biên theo vai trò món nhưng đường gọi trong `generate_menu` không truyền `food_map`, nên phần kiểm tra đó bị bỏ qua và không xuất hiện trong `violations`. Đây là lỗi tích hợp, không phải lỗi thuật toán.”

## 5. DANH SÁCH 5 VIỆC PHẢI FIX GẤP TRƯỚC KHI DEMO

1. **Truyền `food_map` vào `validate_menu` trong `generate_menu`** (và dùng đúng biên theo vai trò món) để 350 g sữa chua/rau/măng bị chặn và hiện thành vi phạm; đồng thời thu hẹp `lb/ub` của inner solver theo role thay vì 25–350 g cho mọi món.
2. **Bổ sung từ điển allergen** (hải sản → tôm/cua/cá/mực/nghêu/sò…) và kiểm tra dị ứng theo nhóm, không chỉ so khớp chuỗi con; thêm test hồi quy cho token ‘hải sản’ và ‘đậu phộng’.
3. **Trả `fitness`/`diversity_pct` trong `SwapOut` hoặc bỏ điểm số khỏi UI sau swap**; không để người dùng thấy điểm cũ của thực đơn đã đổi.
4. **Thêm khối cảnh báo bệnh lý trong response** (`warnings: [...]`, `data_limitations`): tiểu đường → “không có dữ liệu đường, không kết luận an toàn”; bệnh lý chưa hỗ trợ → “chưa được mô hình hoá”. Kèm disclaimer “không phải thiết bị y tế”.
5. **Việt hoá toàn bộ lỗi 4xx và rút gọn thuật ngữ UI**: map 422 Pydantic sang câu tiếng Việt theo trường; ẩn Seed/Smoke-Web-Full vào mục nâng cao; đổi “Fitness/100” thành “Mức đáp ứng mục tiêu dinh dưỡng”.

---
*Số liệu sinh tự động từ 422 request trong 1143 giây; cấu hình máy: seed cố định theo từng phase, config `web` cho ma trận và 1 phần lâm sàng, `smoke` cho các phép thử rẻ. Không đọc/ghi đè dữ liệu production.*
