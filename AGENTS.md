# AGENTS.md — Hướng dẫn cho AI Coding Agents

Tài liệu này là **nguồn hướng dẫn chính cho AI Coding Agents** làm việc trong repository `DBO_heathcare`.

Mục tiêu của tài liệu:

- mô tả kiến trúc và ranh giới module;
- bảo vệ các bất biến nghiệp vụ;
- phân biệt rõ tính năng đã triển khai với định hướng tương lai;
- bảo đảm thực nghiệm DBO/IDBO công bằng, tái lập và trung thực;
- ngăn agent sửa quá phạm vi hoặc tạo tuyên bố y tế không có bằng chứng.

> Khi nội dung trong tài liệu này mâu thuẫn với trạng thái code hoặc test thực tế, agent phải báo rõ mâu thuẫn và ưu tiên bằng chứng chạy được từ code/test. Không được giả định một tính năng đã hoàn thiện chỉ vì tính năng xuất hiện trong tài liệu thiết kế.

---

## 1. Tổng quan dự án

- **Mã đề tài:** CNTT-KLCN142, Trường Đại học Công Thương TP.HCM.
- **Mục tiêu:** Xây dựng hệ thống đề xuất thực đơn dinh dưỡng cá nhân hóa bằng Dung Beetle Optimizer (DBO) và Improved Dung Beetle Optimizer (IDBO).
- **Kiến trúc tối ưu:** Mixed-Integer Two-Tier Optimization.
  - **Outer tier, discrete:** chọn `food_ids` theo cấu trúc bữa ăn, sở thích và dị ứng.
  - **Inner tier, continuous:** tối ưu khẩu phần gram để bám mục tiêu năng lượng và dinh dưỡng.
- **Đầu ra hiện tại:** prototype hỗ trợ quyết định kỹ thuật, không phải thiết bị y tế và không thay thế tư vấn của chuyên gia dinh dưỡng hoặc nhân viên y tế.

---

## 2. Trạng thái yêu cầu

Mọi quy tắc nghiệp vụ phải được gắn một trong ba trạng thái:

- **ENFORCED:** đã có production code và test bảo vệ. Agent không được làm hỏng.
- **PARTIAL:** đã có một phần implementation hoặc test, nhưng chưa bao phủ toàn pipeline.
- **TARGET:** kiến trúc mục tiêu hoặc kế hoạch tương lai. Không được mô tả như tính năng đã hoàn thiện.

Agent phải kiểm tra code và test trước khi thay đổi trạng thái của một quy tắc.

---

## 3. Bản đồ kiến trúc

```text
src/
├── models/                  # Core domain, schema và ràng buộc
│   ├── food_schema.py       # Schema dữ liệu thực phẩm và validation
│   ├── dish_category.py     # Vai trò ẩm thực, nếu đã được triển khai
│   ├── meal_structure.py    # Culinary slots, nếu đã được triển khai
│   ├── user_profile.py      # Hồ sơ người dùng
│   ├── menu.py              # MenuItem, Meal, Menu
│   ├── constraints.py       # Ràng buộc năng lượng, dinh dưỡng, dị ứng
│   ├── objective.py         # Hàm mục tiêu domain
│   ├── food_sampler.py      # Lọc/lấy mẫu thực phẩm
│   └── food_selector.py     # Giải mã z sang food_ids
│
├── algorithms/              # Thuật toán tối ưu
│   ├── dbo.py
│   ├── idbo.py
│   ├── behaviors.py
│   ├── benchmarks.py
│   ├── menu_objective.py
│   └── two_tier_solver.py
│
├── utils/
│   ├── data_loader.py
│   ├── nutrition.py
│   └── portion_utils.py
│
data/
├── raw/
└── processed/
│
scripts/                     # Demo, experiment, plot và report builder
experiments/                 # Kết quả thực nghiệm có version
assets/                      # Tài nguyên trình bày nếu có
docs/                        # Báo cáo, slide và review notes
tests/                       # Unit, integration và regression tests
```

### Ranh giới module

- `src/models/` chứa logic nghiệp vụ, schema và validation.
- `src/algorithms/` chỉ chứa logic tối ưu tổng quát và adapter cần thiết.
- `src/utils/` không được chứa business rules quan trọng.
- `scripts/` điều phối pipeline, không được sao chép lại logic production.
- `tests/` phải gọi production code thật khi kiểm tra hành vi cốt lõi.
- Slide và báo cáo phải lấy dữ liệu từ CSV hoặc output có thể truy vết, không hard-code kết luận trái với dữ liệu.

---

## 4. Bất biến nghiệp vụ

### 4.1. Năng lượng và dinh dưỡng

**Trạng thái: ENFORCED hoặc PARTIAL tùy nutrient, phải kiểm tra test hiện tại.**

- Năng lượng ngày nằm trong biên độ `±10%` so với mục tiêu cấu hình.
- Protein và carbohydrate nằm trong `±15%`.
- Fat nằm trong `±20%`.
- Fiber nằm trong `±30%`.
- Không có nutrient âm, `NaN` hoặc vô hạn.
- Natri chỉ được gọi là ràng buộc khi production validation thực sự kiểm tra `sodium_mg`.
- Sau khi làm tròn khẩu phần, hệ thống phải tính lại nutrient và validation trên nghiệm đã làm tròn.

### 4.2. Nguồn dữ liệu đường

**Trạng thái: ENFORCED về minh bạch dữ liệu.**

- Dataset hiện tại không được giả định có `total sugar` nếu schema thực tế không chứa trường đó.
- Không được trình bày `carbs * 0.15` như dữ liệu đường đo thực tế.
- Nếu proxy còn được dùng để thử nghiệm, tên biến/field phải thể hiện rõ, ví dụ:

```python
sugar_g_estimated
sugar_proxy_g
sugar_is_estimated = True
```

- Proxy đường không được dùng để kết luận thực đơn “an toàn cho tiểu đường”.
- API, CSV, slide và báo cáo phải phân biệt dữ liệu đo được, dữ liệu suy ra và proxy.

### 4.3. Deterministic decoding

**Trạng thái: ENFORCED.**

- Cùng input, seed và candidate pools phải tạo cùng mapping từ `z` sang `food_ids`.
- Mọi thuật toán ngẫu nhiên phải nhận `seed`.
- Dùng RNG cục bộ:

```python
rng = np.random.default_rng(seed)
```

- Không dùng mutable global RNG hoặc state từ lần chạy trước.

### 4.4. Làm tròn khẩu phần

**Trạng thái: ENFORCED.**

Pipeline chuẩn:

```text
continuous solution
→ round portions to 5 g
→ decode rounded menu
→ recalculate nutrients
→ validate rounded menu
→ report final metrics
```

Không được báo fitness/nutrient của nghiệm liên tục nhưng hiển thị một thực đơn đã làm tròn khác.

### 4.5. Edibility và readiness

**Trạng thái: PARTIAL hoặc TARGET, phải kiểm tra production code và test.**

- Dữ liệu nguồn có thể chứa nguyên liệu thô.
- Candidate pool dùng để đề xuất trực tiếp cho người dùng chỉ được chứa món hoặc thực phẩm phù hợp với vai trò tiêu dùng được gán.
- Không đề xuất nguyên liệu thô, bột cô đặc, gia vị, shortening, dầu hoặc sản phẩm công nghiệp như một món độc lập.
- Nếu chưa có lớp `Recipe` hoặc `Preparation`, nguyên liệu không ăn trực tiếp phải bị loại khỏi user-facing candidate pool.
- Không tuyên bố đã chặn một nhóm nguyên liệu nếu demo hoặc test còn tạo được nhóm đó.

### 4.6. Culinary slots

**Trạng thái: PARTIAL hoặc TARGET.**

Cấu trúc mặc định của một bữa chính:

```text
Staple + Main Protein + Vegetable/Soup
```

Các role dự kiến:

```text
STAPLE
MAIN_PROTEIN
VEGETABLE
SOUP
FRUIT
SNACK
BEVERAGE
CONDIMENT
INGREDIENT
COMPOSITE_MEAL
UNKNOWN
```

Quy tắc:

- Không có hai món cùng role trong một bữa chính, trừ khi rule cụ thể cho phép.
- `COMPOSITE_MEAL` có thể thay thế nhiều slot nếu món đã đại diện cho một bữa hoàn chỉnh.
- `INGREDIENT`, `CONDIMENT` và `UNKNOWN` không được xuất hiện như món độc lập trong output người dùng.
- Không tự động áp cấu trúc món Việt Nam cho mọi chế độ ăn nếu profile hoặc dish type yêu cầu cấu trúc khác.

### 4.7. Realistic portion bounds

**Trạng thái: TARGET hoặc PARTIAL.**

Không dùng `[25, 350]` như giới hạn cuối cùng cho mọi role khi tạo output người dùng.

Khoảng tham chiếu ban đầu:

```text
STAPLE:          100-250 g
MAIN_PROTEIN:     60-180 g
VEGETABLE:       100-300 g
SOUP/BEVERAGE:   150-500 g hoặc ml tương đương
FRUIT/SNACK:      60-200 g
NUTS/NUT_BUTTER:  10-50 g
CONDIMENT/OIL:     5-30 g
COMPOSITE_MEAL:  200-500 g
```

- Đây là bounds kỹ thuật ban đầu, không phải tuyên bố lâm sàng.
- Nếu role chưa đáng tin cậy, ghi `UNKNOWN` và loại khỏi output hoặc dùng fallback có log rõ ràng.
- Mọi thay đổi bounds phải có test và benchmark hồi quy.

---

## 5. Giới hạn tuyên bố y tế

- Dự án là prototype kỹ thuật hỗ trợ quyết định.
- Không được viết “an toàn tuyệt đối”, “điều trị”, “chữa”, “đạt chuẩn lâm sàng” hoặc “đạt AHA” khi chưa có quy trình thẩm định tương ứng.
- Cách diễn đạt mặc định:

> Đáp ứng hoặc không đáp ứng ngưỡng dinh dưỡng được cấu hình trong thử nghiệm.

- P1/P2/P3 là hồ sơ mô phỏng phục vụ benchmark kỹ thuật.
- Không dùng proxy nutrient để đưa ra kết luận y tế.
- Nếu thiếu dữ liệu, phải nói rõ giới hạn thay vì suy diễn.

---

## 6. Quy tắc triển khai thuật toán

### 6.1. State và RNG

- Không dùng mutable global state trong `src/algorithms/`.
- Mỗi lần `optimize()` độc lập với lần chạy trước.
- Population, best solution, histories và counters không được rò sang run tiếp theo.
- Telemetry phải được trả về qua result object.

### 6.2. DBO và IDBO dispatch

- `two_tier_solver.py` phải dispatch đúng class cho outer và inner solver.
- Không được silently fallback từ IDBO sang DBO.
- Algorithm name không hợp lệ phải gây lỗi rõ ràng, không tự chuyển qua IDBO hoặc DBO.

### 6.3. IDBO telemetry

Kết quả IDBO nên cung cấp tối thiểu:

```text
n_perturbations
n_restarts
stagnation_events hoặc thông tin tương đương
```

Two-tier result nên tách:

```text
outer_perturbations
outer_restarts
final_inner_perturbations
final_inner_restarts
```

Không kết luận cơ chế IDBO hiệu quả nếu telemetry cho thấy cơ chế chưa kích hoạt.

---

## 7. Quy tắc benchmark DBO và IDBO

### 7.1. Fair comparison

- So sánh paired trên cùng seed.
- Dùng cùng objective, bounds, population size và dữ liệu.
- Ưu tiên cùng số lần đánh giá objective thay vì chỉ cùng iteration count.
- Không thay tham số sau khi xem kết quả chỉ để làm IDBO thắng.
- Cấu hình kiểm tra activation phải được gọi là `diagnostic`, không đánh tráo thành benchmark hiệu năng chính.

### 7.2. Metrics bắt buộc

```text
best fitness
mean fitness
median fitness
std
worst fitness
runtime
n_evaluations
perturbations
restarts
paired difference: IDBO - DBO
IDBO wins / ties / losses
```

Nếu phù hợp, dùng paired statistical test như Wilcoxon signed-rank.

Nếu mọi paired differences bằng 0:

- ghi rõ mọi cặp bằng nhau;
- không ép chạy kiểm định vô nghĩa;
- kết luận “tương đương trong phạm vi thử nghiệm”, không nói hai thuật toán tương đương về bản chất.

### 7.3. Diễn giải kết quả

- Nếu cơ chế IDBO không kích hoạt: kết luận cấu hình chưa cho phép đánh giá cải tiến.
- Nếu cơ chế kích hoạt nhưng fitness không khác: IDBO có hành vi tìm kiếm khác nhưng chưa cải thiện có ý nghĩa.
- Nếu IDBO tốt hơn: chỉ kết luận tốt hơn trong phạm vi instance/cấu hình đã thử và phải báo paired evidence.
- Nếu IDBO kém hơn: báo trung thực runtime, variance và khả năng perturbation phá nghiệm tốt.

---

## 8. Data và experiment provenance

- Không chỉnh tay `data/processed/` nếu không có script tái tạo.
- Không ghi đè benchmark lịch sử khi chỉ sửa code.
- Kết quả mới phải vào thư mục riêng, ví dụ:

```text
experiments/ablation_dbo_idbo/
experiments/week9_rerun_2026_10_16/
```

- Mỗi thư mục experiment nên có:

```text
README.md
config.json hoặc metadata tương đương
raw/paired runs CSV
summary CSV
figures
```

- Slide phải đọc từ output mới nhất được chỉ định rõ, không tự dùng PNG cũ khi CSV đã thay đổi.
- Nếu CSV mới hơn figure, pipeline nên dựng lại figure hoặc báo lỗi.

---

## 9. Quy ước lập trình

- Python 3.12.
- Mọi hàm mới có type hints.
- Ưu tiên `dataclasses` cho result/config objects.
- Không thêm dependency nặng khi chưa cần thiết.
- Không duplicate domain logic trong scripts.
- Không nuốt exception bằng `except Exception: pass`.
- Error message phải đủ thông tin để chẩn đoán.
- Comment giải thích “vì sao”, không lặp lại “code đang làm gì”.
- Giữ backward compatibility nếu nhiệm vụ không cho phép breaking change.

---

## 10. Change-Scope Policy

- Chỉ sửa file cần cho nhiệm vụ.
- Không tự refactor toàn codebase khi người dùng chỉ yêu cầu benchmark hoặc slide.
- Không sửa dữ liệu, thuật toán và slide trong một commit duy nhất.
- Không đưa `.venv`, cache, temporary files, secrets hoặc credentials vào Git.
- Không merge trực tiếp vào `main` cho nhiệm vụ thử nghiệm.
- Trước thay đổi lớn, tạo branch riêng.
- Nếu thay đổi làm số liệu cũ không còn đại diện cho code mới, phải đánh dấu output cũ là historical và chạy lại trước khi cập nhật kết luận.

---

## 11. Git và commit policy

Commit nên tách theo mục đích:

```text
test: reproduce or protect behavior
fix: correct production behavior
experiment: add benchmark or analysis pipeline
docs: update report or slides from verified results
```

Không dùng commit message chung chung như:

```text
update
fix stuff
final
```

Không force push nếu không được yêu cầu rõ ràng.

---

## 12. Verification bắt buộc

Dùng Python interpreter của environment đang active.

### Toàn bộ test

```bash
python -m pytest -q
```

### Test solver

```bash
python -m pytest tests/test_two_tier_solver.py -v
```

### Test constraints/menu

```bash
python -m pytest tests/test_constraints.py tests/test_menu.py -v
```

### Test dữ liệu và realism, nếu tồn tại

```bash
python -m pytest tests/test_data_integrity.py tests/test_culinary_realism.py -v
```

### Demo smoke test

```bash
python scripts/demo_week8.py \
  --outer-iter 5 \
  --outer-agents 6 \
  --inner-iter 5 \
  --inner-agents 6 \
  --seed 42
```

Agent phải kiểm tra output, không chỉ exit code:

- không có nutrient âm hoặc `NaN`;
- menu sau làm tròn vẫn được validate;
- không có ingredient/raw item như món độc lập;
- không có phần ăn vượt role bounds nếu feature đã ENFORCED;
- không dùng proxy sugar như dữ liệu đo;
- DBO và IDBO report đúng telemetry;
- output tái lập với cùng seed.

---

## 13. Slide và báo cáo

- Không hard-code kết luận trái với CSV.
- Không gọi kết quả “an toàn y tế”.
- Không nói IDBO tốt hơn nếu DBO và IDBO bằng nhau hoặc không có kiểm định.
- Nếu DBO và IDBO bằng nhau, ghi:

> Trong cấu hình thử nghiệm hiện tại, chưa ghi nhận IDBO vượt trội hơn DBO. Telemetry cần được dùng để xác định cơ chế cải tiến có thực sự kích hoạt hay không.

- Tổng số tests trên slide phải lấy từ kết quả pytest thực tế.
- Sau khi sửa script tạo slide, phải dựng lại PowerPoint và kiểm tra không có text overflow, hình cũ hoặc số liệu cũ.

---

## 14. Thứ tự ưu tiên khi có xung đột

1. Không làm mất dữ liệu, không lộ secret và không phá repository.
2. Quy tắc `ENFORCED` và test hiện có.
3. Tính tái lập và provenance của thực nghiệm.
4. Phạm vi nhiệm vụ người dùng giao.
5. Ranh giới kiến trúc và coding conventions.
6. Quy tắc `PARTIAL`.
7. Quy tắc `TARGET` chỉ là định hướng, không được giả vờ đã hoàn thiện.

---

## 15. Checklist trước khi kết thúc nhiệm vụ

Agent phải báo rõ:

- các file đã đọc;
- các file đã sửa/tạo;
- test nào đã chạy và kết quả chính xác;
- demo/experiment nào đã chạy;
- cấu hình và seed;
- output mới nằm ở đâu;
- giới hạn chưa xử lý;
- behavior nào thay đổi;
- có cần chạy lại benchmark/slide hay không;
- commit hash nếu đã commit.

Không được dùng câu “đã hoàn tất” nếu chưa chạy các bước xác minh bắt buộc.
