# Báo Cáo Quy Trình Làm Sạch và Chuẩn Hóa Dữ Liệu Thực Phẩm (Phase 1)

> **Mục tiêu**: Loại bỏ triệt để các mục dữ liệu phi thực tế, ngoại lai (outliers), 
> vi phạm định luật bảo toàn khối lượng, thịt sống chưa chế biến và gia vị đóng hộp khỏi tập đề xuất.

## 1. Tổng Quan Quy Trình Lọc (Filter Funnel)

- **Tổng số thực phẩm ban đầu**: `15,929` món (USDA: `15,403`, VN: `526`)
- **Tổng số thực phẩm bị loại**: `2,220` món (`13.9%`)
- **Số thực phẩm sạch sau chuẩn hóa**: `13,709` món (USDA: `13,224`, VN: `485`)

| Bước lọc | Lý do loại bỏ | Ngưỡng / Tiêu chí | Số lượng loại | Ví dụ điển hình |
|---|---|---|---|---|
| 1 | Natri phi vật lý / lỗi đơn vị nhập liệu | `sodium_mg > 3000 mg/100g` | **67** | ANCHOVIES IN OLIVE OIL (4.690.000 mg), BASTONCINI (1.000.000 mg) |
| 2 | Calo vượt giới hạn vật lý per 100g | `calories > 900 kcal hoặc < 0` | **1** | Món calo > 900 (vượt trần lipid thuần) |
| 3 | Vi phạm bảo toàn khối lượng | `Macro riêng lẻ > 100g hoặc Tổng Protein+Carbs+Fat > 105g/100g` | **14** | Noodles ghi nhận Protein 131g/100g, Bánh ghi nhận Carbs 250g/100g |
| 4 | Thiếu toàn bộ macronutrients | `Protein, Carbs, Fat đồng thời NaN` | **10** | Các mục chỉ ghi calo mà không có thành phần đa lượng |
| 5 | Nhóm thực phẩm không phù hợp | `American Indian/Alaska Native Foods & Gia vị` | **183** | Thịt cú sống, mắt tuần lộc, gan hải mã, nước mắm cá |
| 6 | Thịt động vật / gia cầm sống | `Regex (raw meat/poultry/game/quail/seafood/organs)` | **1,050** | Quail meat raw (chim cút sống), Chicken breast raw, Tiết lợn sống |
| 7 | Bột công nghiệp / men nở / hỗn hợp pha | `Regex (flour, starch, baking powder, tahini, drink mix)` | **242** | Bột mì đa dụng, A NON-ALCOHOLIC DRINK MIX (160g), Tahini bơ mè |
| 8 | Gia vị / nước chấm / hạt nêm | `Regex (salt/muối, soy sauce, bouillon, broth base)` | **653** | Muối ăn, bột canh, nước hầm cô đặc, xì dầu |

---

## 2. Giải Trình Trực Tiếp 3 Nhận Xét Của Hội Đồng

### 2.1. Vấn đề 1: Vi phạm Natri (Ngày 1: 343%, Ngày 6: 260%)
- **Bằng chứng gốc**: Trong dataset cũ, tồn tại các mục lỗi đơn vị nghiêm trọng:
  - `USDA_704`: ANCHOVIES IN OLIVE OIL ghi nhận **4.690.000 mg/100g** (sai số 1.000 lần so với thực tế).
  - `USDA_272`: BASTONCINI ghi nhận **1.000.000 mg/100g**.
  - `USDA_13413`: ARGENTINIAN BRAND SAUSAGE ghi nhận **678.000 mg/100g**.
  - `USDA_3580`: BBQ PORK RIBS ghi nhận **179.000 mg/100g**.
- **Hành động khắc phục**: Thiết lập trần natri tối đa `3.000 mg/100g` cho toàn bộ candidate pool. Mọi mục gia vị cô đặc, muối thô và lỗi nhập liệu đều bị loại bỏ trước khi chuyển cho thuật toán DBO/IDBO.

### 2.2. Vấn đề 2: Đề xuất món ăn phi thực tế (Chim cút sống, Đùi gà 25g, Tahini 85g, Pha đồ uống 160g)
- **Thịt chim cút sống (`Quail, breast, meat only, raw`)**: Xuất phát từ mã `USDA_172829`. Bộ lọc Phase 1 đã bổ sung quy tắc regex chặn toàn bộ thịt/gia cầm có nhãn `raw`, `uncooked`, `sống`.
- **Bột pha đồ uống 160g (`A NON-ALCOHOLIC DRINK MIX`)**: Xuất phát từ mã `USDA_1916338`. Bộ lọc đã chặn từ khóa `drink mix`, `flavoring`, `powder` dạng công nghiệp.
- **Tahini 85g**: Xuất phát từ nhóm bơ hạt cô đặc (`Seeds, sesame butter, tahini`). Đã loại bỏ khỏi vai trò snack bữa phụ độc lập.
- **Đùi gà 25g**: Được xử lý bằng cách đồng bộ hóa ràng buộc `PORTION_RANGE` trong `constraints.py` với `ROLE_PORTION_BOUNDS` trong `dish_category.py` (Main Protein tối thiểu 60g, không còn tình trạng 25g).

### 2.3. Vấn đề 3: Minh chứng quy trình chuẩn hóa và xử lý dữ liệu
- Toàn bộ quy trình được tự động hóa qua script độc lập `scripts/clean_dataset.py`.
- Bảng so sánh chất lượng dữ liệu trước và sau làm sạch:

| Chỉ số dinh dưỡng | Trước làm sạch (Min - Max) | Sau làm sạch (Min - Max) | Trạng thái |
|---|---|---|---|
| Năng lượng (kcal/100g) | 0.0 - 901.1 | **0.0 - 900.0** | Chuẩn hóa hoàn tất |
| Đạm (g/100g) | 0.0 - 167.0 | **0.0 - 88.3** | Chuẩn hóa hoàn tất |
| Tinh bột (g/100g) | -0.7 - 250.0 | **0.0 - 100.0** | Chuẩn hóa hoàn tất |
| Chất béo (g/100g) | 0.0 - 100.0 | **0.0 - 100.0** | Chuẩn hóa hoàn tất |
| Chất xơ (g/100g) | 0.0 - 100.0 | **0.0 - 79.0** | Chuẩn hóa hoàn tất |
| Natri (mg/100g) | 0.0 - 4,690,000.0 | **0.0 - 3,000.0** | Chuẩn hóa hoàn tất |

## 3. Danh Sách Mẫu Top 10 Ngoại Lai Natri Bị Loại Bỏ

| STT | Food ID | Tên thực phẩm | Natri (mg/100g) | Nguồn | Phân tích lỗi |
|---|---|---|---|---|---|
| 1 | `USDA_2110512` | ANCHOVIES IN OLIVE OIL | **4,690,000** | usda | Sai đơn vị / gia vị cô đặc |
| 2 | `USDA_2057182` | BASTONCINI, ORIGINAL | **1,000,000** | usda | Sai đơn vị / gia vị cô đặc |
| 3 | `USDA_2149900` | ARGENTINIAN BRAND SAUSAGE | **678,000** | usda | Sai đơn vị / gia vị cô đặc |
| 4 | `USDA_1980220` | 4 QUESOS MEXICAN BLEND SHREDDED MONTEREY JACK, CHEDDAR, ASADERO & QUESADILLA NATURAL CHEESE, 4 QUESOS MEXICAN BLEND | **607,000** | usda | Sai đơn vị / gia vị cô đặc |
| 5 | `USDA_2097472` | ANDOUILLE SMOKED SAUSAGE, HOT | **589,000** | usda | Sai đơn vị / gia vị cô đặc |
| 6 | `USDA_2450293` | BAKED POTATO CASSEROLE, BAKED POTATO | **471,000** | usda | Sai đơn vị / gia vị cô đặc |
| 7 | `USDA_2150491` | BAKED BRIE EN CROUTE | **440,000** | usda | Sai đơn vị / gia vị cô đặc |
| 8 | `USDA_1896478` | BBQ BAKED BEANS | **385,000** | usda | Sai đơn vị / gia vị cô đặc |
| 9 | `USDA_2254902` | BALSAMIC CHICKEN, CHICKEN | **371,000** | usda | Sai đơn vị / gia vị cô đặc |
| 10 | `USDA_2502126` | BBQ SEASONED COOKED BONELESS PORK RIBS WITH SAUCE, BBQ | **179,000** | usda | Sai đơn vị / gia vị cô đặc |
