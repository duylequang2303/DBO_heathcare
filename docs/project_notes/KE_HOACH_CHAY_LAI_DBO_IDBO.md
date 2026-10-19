# KẾ HOẠCH CHẠY LẠI DBO VÀ IDBO

## 0. Mục tiêu cuối cùng

Kế hoạch này chỉ nhằm trả lời bốn câu hỏi:

1. DBO và IDBO có thật sự chạy bằng hai implementation khác nhau không?
2. Cơ chế `perturbation` và `restart` của IDBO có kích hoạt trong Two-Tier Solver không?
3. Nếu không kích hoạt, nguyên nhân là do diversity, stagnation, truyền tham số hay logic activation?
4. Khi cơ chế kích hoạt đúng, IDBO có cải thiện fitness đủ rõ và có ý nghĩa so với DBO không?

Không được đổi tham số chỉ để ép IDBO thắng. Kết quả hòa hoặc IDBO kém hơn vẫn là kết quả hợp lệ.

---

# PHẦN A — QUY TẮC CHUNG

## A1. Những việc chưa được làm

Trước khi hoàn tất các gate bên dưới, không ai được:

- chạy full benchmark 10 seed;
- sửa công thức DBO hoặc IDBO;
- đổi candidate pool;
- đổi objective hoặc penalty;
- sửa slide kết luận nguyên nhân;
- tuyên bố IDBO tốt hơn DBO;
- tuyên bố diversity là nguyên nhân nếu chưa có telemetry trực tiếp;
- chạy lại toàn bộ tuần 8-9 chỉ để “xem thử”.

## A2. Phân công nhiệm vụ cụ thể cho 3 thành viên

Để đảm bảo tính khách quan khoa học, tránh thiên vị và ngăn ngừa sai sót kỹ thuật, khối lượng công việc được phân công độc lập cho 3 sinh viên thực hiện đề tài (ĐH Công Thương TP.HCM — Mã đề tài: CNTT-KLCN142):

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MA TRẬN PHÂN CÔNG TRÁCH NHIỆM                         │
├────────────────────────┬─────────────────────────┬──────────────────────────┤
│ Lê Quang Duy (2001230123)│ Hồ Trung Cương (2001230070)│ Đặng N. Minh Đăng (2001230175)│
│ Nhóm trưởng / Tích hợp │ Telemetry & Đo lường    │ Controlled Activation    │
│ Gate 1, 4, F, J, K     │ Gate 2, C, Sanity Check │ Gate 3, D, G, I          │
└────────────────────────┴─────────────────────────┴──────────────────────────┘
```

---

### Thành viên 1: Lê Quang Duy (2001230123) — Nhóm trưởng & Người tích hợp (Integration Lead)

**Trách nhiệm chính:** Quản trị kiến trúc, tích hợp mã nguồn, khóa cấu hình đối chuẩn và tổng hợp báo cáo slide.

* **Phụ trách các giai đoạn:** Gate 1 (Kiểm tra Code tĩnh), Gate 4 (Khóa cấu hình & Smoke Benchmark), Phần F (Quyết định Gatekeeper), Phần J (Slide Báo cáo), Phần K (Kiểm tra trước khi Merge).
* **Nhiệm vụ chi tiết:**
  1. Kiểm tra dispatch và truyền tham số trong `two_tier_solver.py` (loại bỏ fallback ngầm, bắt lỗi `ValueError` nếu sai tên thuật toán).
  2. Quản lý nhánh Git `experiment/dbo-idbo-ablation`, review và ghép các bản vá từ Cương và Đăng.
  3. Khóa cấu hình benchmark chính thức (`config_locked.json`), thiết lập cờ `--resume` và lưu kết quả theo từng run.
  4. Trực tiếp biên soạn Slide Tuần 8–9 ([Slide_Bao_Cao_Tuan_8_9_DBO_IDBO.pptx](file:///home/duyle/coding/DBO_heathcare/docs/slides/Slide_Bao_Cao_Tuan_8_9_DBO_IDBO.pptx)), chuyển đổi toàn bộ số liệu đo được thành biểu đồ trực quan, loại bỏ các chi tiết kỹ thuật/file path không phù hợp cho buổi báo cáo.
  5. Đảm bảo toàn bộ 205/205 unit tests luôn PASS trước và sau khi tích hợp.
* **Đầu ra bắt buộc:**
  * `src/algorithms/two_tier_solver.py` (tích hợp hoàn chỉnh).
  * `scripts/build_pptx_week8_9.py`, `docs/slides/Slide_Bao_Cao_Tuan_8_9_DBO_IDBO.pptx` & `.pdf`.
  * `PROJECT_STATE.md` và `patches/` (patch bundle tổng hợp).

---

### Thành viên 2: Hồ Trung Cương (2001230070) — Phụ trách Telemetry & Đo lường nội tại (Telemetry Specialist)

**Trách nhiệm chính:** Xây dựng hệ thống đo lường khách quan trong IDBO, chứng minh thực nghiệm nguyên nhân không kích hoạt.

* **Phụ trách các giai đoạn:** Gate 2 (Đo lường trực tiếp Telemetry), Phần C (Yêu cầu & Sanity Check Telemetry), Phân tích độ đa dạng quần thể (Phần H1, H2).
* **Nhiệm vụ chi tiết:**
  1. Bổ sung các chỉ số đo lường trực tiếp vào `IDBO` trong `src/algorithms/idbo.py` mà không làm thay đổi hành vi giải thuật:
     * `min_diversity`, `mean_diversity`, `final_diversity`
     * `max_stagnation`, `n_diversity_collapse_events`, `n_stagnation_events`
     * `n_perturbations`, `n_restarts`
  2. Ánh xạ các trường đo lường này lên `TwoTierResult` trong `two_tier_solver.py` (tách rõ outer và inner).
  3. Thiết lập sanity checks: $0 \le \text{min\_diversity} \le \text{mean\_diversity}$, các bộ đếm sự kiện là số nguyên không âm.
  4. Viết unit test mục tiêu trong `tests/test_two_tier_solver.py` chứng minh các trường telemetry được ghi nhận chính xác.
  5. Đo đạc thực tế trên 10 paired seeds và lập bảng phân bố độ đa dạng (chứng minh $\text{min\_diversity} \approx 0.246 > \text{threshold}$).
* **Đầu ra bắt buộc:**
  * `patch_telemetry.patch` (hoặc commit tương ứng trên nhánh).
  * Bộ trường telemetry đầy đủ trong `paired_runs.csv` và `summary.csv`.
  * `pytest_telemetry.log` (xác thực test telemetry PASS 100%).

---

### Thành viên 3: Đặng Nguyễn Minh Đăng (2001230175) — Phụ trách Controlled Activation & Thực nghiệm (Activation & Benchmark Specialist)

**Trách nhiệm chính:** Xác minh đường dây kích hoạt giải thuật (wiring check) và giải trình hiện tượng suy giảm fitness khi tăng vòng lặp.

* **Phụ trách các giai đoạn:** Gate 3 (Controlled Activation Sanity Check), Phần D (Ma trận kết luận kích hoạt), Phần G (Theo dõi dữ liệu Full Benchmark), Phần I (Phân tích hiện tượng nhiễu hội tụ ở 150 vòng).
* **Nhiệm vụ chi tiết:**
  1. Xây dựng kịch bản kiểm chứng kích hoạt cưỡng bức `controlled_activation`:
     * Thiết lập cấu hình nhạy: `stagnation_window = 2`, `diversity_threshold = 0.50`, `perturbation_rate = 1.0`, `restart_rate = 1.0`.
     * Chạy trên các seed thử nghiệm [8001, 8002, 8003] để chứng minh khi điều kiện thỏa mãn, IDBO lập tức thực thi restart và perturbation.
  2. Xác minh và ghi nhận số lần kích hoạt thực tế: Outer kích hoạt $\ge 30$ lần, Inner kích hoạt $\ge 8.000$ lần $\rightarrow$ Phán quyết: Đường dây kết nối IDBO hoàn toàn thông suốt, không có lỗi code.
  3. Phân tích hiện tượng suy giảm Mean Fitness khi tăng lên 150 vòng (Phần I): Chứng minh do hàm mục tiêu tầng ngoài bị nhiễu stochastic bởi tầng trong (inner optimizer 25 vòng), dẫn đến hiện tượng overfit nghiệm giả khi không lọc nhiễu.
  4. Hỗ trợ đối chuẩn paired data, tính toán các chỉ số thống kê (Mean, Std, Median, Best, Worst, Wilcoxon Signed-Rank test).
* **Đầu ra bắt buộc:**
  * `controlled_activation.csv` (lưu trữ kết quả kích hoạt có kiểm soát).
  * Mục giải trình nguyên nhân nhiễu đánh giá trong `experiments/ablation_dbo_idbo/README.md`.
  * Biểu đồ trực quan hóa đối chuẩn [fig_ablation_dbo_idbo.png](file:///home/duyle/coding/DBO_heathcare/experiments/ablation_dbo_idbo/fig_ablation_dbo_idbo.png).

---

### Quy tắc cộng tác giữa 3 thành viên:
1. Mỗi thành viên chỉ chỉnh sửa trong phạm vi module được giao; không tự ý thay đổi thuật toán cốt lõi.
2. Mọi thay đổi đều phải kèm test kiểm chứng độc lập trước khi gửi cho Lê Quang Duy tích hợp.
3. Không ai ngoài nhóm trưởng (Lê Quang Duy) được phép cập nhật kết luận trên Slide báo cáo và README chính thức.
4. Mọi kết luận khoa học phải dựa trên dữ liệu đo lường trực tiếp, không đưa ra tuyên bố thiếu căn cứ.

---

# PHẦN B — GATE 1: KIỂM TRA CODE TĨNH

Không chạy benchmark dài ở bước này.

## B1. Kiểm tra dispatch

Xác nhận trong `two_tier_solver.py`:

```text
outer_algo="dbo"  -> DBO
outer_algo="idbo" -> IDBO
inner_algo="dbo"  -> DBO
inner_algo="idbo" -> IDBO
```

Tên thuật toán sai phải gây `ValueError`.

## B2. Kiểm tra truyền tham số

Xác nhận các tham số sau được truyền cho IDBO ở cả outer, inner và final-inner:

```text
diversity_threshold
stagnation_window
perturbation_rate
perturbation_scale
restart_rate
n_elite
```

## B3. Kiểm tra RNG

Mỗi run phải nhận seed rõ ràng và dùng RNG cục bộ.

Không được có:

```text
np.random.seed(...)
mutable global RNG
state còn lại từ run trước
```

## B4. Kiểm tra điều kiện activation

Viết lại điều kiện dưới dạng câu đơn giản trong review note:

```text
Perturbation xảy ra khi nào?
Restart xảy ra khi nào?
Diversity được tính tại thời điểm nào?
Stagnation counter tăng khi nào?
Stagnation counter reset khi nào?
```

## B5. Điều kiện qua Gate 1

Chỉ qua Gate 1 khi:

- dispatch đúng;
- tham số được truyền đúng;
- seed được kiểm soát;
- điều kiện activation được mô tả rõ;
- unit tests mục tiêu pass.

Lệnh:

```bash
python -m pytest tests/test_idbo.py tests/test_two_tier_solver.py -q
```

Nếu Gate 1 fail: dừng, sửa code, không chạy benchmark.

---

# PHẦN C — GATE 2: TELEMETRY

## C1. Yêu cầu telemetry

Telemetry phải được tạo ngay trong IDBO thật, không suy ra bên ngoài.

Mỗi run phải trả về tối thiểu:

```text
min_diversity
mean_diversity
final_diversity
max_stagnation
n_diversity_collapse_events
n_stagnation_events
n_perturbations
n_restarts
```

Two-Tier phải tách được:

```text
outer_min_diversity
outer_mean_diversity
outer_final_diversity
outer_max_stagnation
outer_perturbations
outer_restarts
inner_perturbations_total
inner_restarts_total
final_inner_perturbations
final_inner_restarts
```

## C2. Sanity checks

Telemetry phải thỏa:

```text
0 <= min_diversity <= mean_diversity
0 <= final_diversity
max_stagnation >= 0
all event counters are integers >= 0
```

Nếu diversity có range chuẩn hóa, phải ghi rõ range.

## C3. Smoke run telemetry

Chỉ chạy một seed:

```text
seed = 8001
baseline 25 iterations
DBO và IDBO
```

DBO có thể để telemetry IDBO bằng 0 hoặc `not_applicable`, nhưng không được giả thành số đo IDBO.

## C4. Điều kiện qua Gate 2

- CSV có telemetry thật;
- không có NaN;
- min/mean/final hợp lệ;
- cùng seed chạy lại cho cùng kết quả;
- test suite mục tiêu pass.

Nếu Gate 2 fail: dừng, không chạy full benchmark.

---

# PHẦN D — GATE 3: CONTROLLED ACTIVATION

## D1. Mục tiêu

Chứng minh Two-Tier Solver thật sự có thể kích hoạt IDBO khi điều kiện được tạo có chủ đích.

Không dùng kết quả này để chứng minh IDBO tốt hơn.

## D2. Cấu hình khóa

```json
{
  "name": "controlled_activation",
  "seeds": [8001, 8002],
  "outer_iterations": 30,
  "inner_iterations": 10,
  "outer_agents": 10,
  "inner_agents": 10,
  "stagnation_window": 2,
  "diversity_threshold": 0.5,
  "perturbation_rate": 1.0,
  "restart_rate": 1.0
}
```

Nếu diversity range không phải `[0, 1]`, người phụ trách phải hiệu chỉnh threshold dựa trên phép đo telemetry, đồng thời ghi rõ lý do.

## D3. Tiêu chí thành công

Ít nhất một chỉ số phải lớn hơn 0:

```text
outer_perturbations
outer_restarts
inner_perturbations_total
inner_restarts_total
```

## D4. Ma trận kết luận Gate 3

### Trường hợp 1 — Tất cả vẫn bằng 0

Kết luận:

```text
Controlled activation thất bại.
Có khả năng còn lỗi wiring, propagation hoặc điều kiện activation.
```

Hành động:

- dừng toàn bộ benchmark;
- không sửa slide theo hướng “do threshold”;
- debug code trước.

### Trường hợp 2 — Activation > 0

Kết luận:

```text
Wiring Two-Tier -> IDBO hoạt động.
Có thể tiếp tục chẩn đoán vì sao cấu hình benchmark chính không kích hoạt.
```

Sau đó mới được qua Gate 4.

---

# PHẦN E — GATE 4: SMOKE BENCHMARK TRƯỚC KHI CHẠY FULL

## E1. Khóa cấu hình

Lưu vào:

```text
experiments/ablation_dbo_idbo/config_locked.json
```

Cấu hình đề xuất:

```json
{
  "seeds": [8001, 8002],
  "outer_agents": 10,
  "inner_agents": 10,
  "inner_iterations": 25,
  "configs": {
    "baseline_short": {
      "outer_iterations": 25,
      "stagnation_window": 25,
      "diversity_threshold": 0.001
    },
    "diagnostic_balanced": {
      "outer_iterations": 100,
      "stagnation_window": 10,
      "diversity_threshold": 0.01
    },
    "diagnostic_long_run": {
      "outer_iterations": 150,
      "stagnation_window": 5,
      "diversity_threshold": 0.05
    }
  }
}
```

Không gọi cấu hình 150 vòng là `diagnostic_activation` nếu activation vẫn bằng 0.

## E2. Chỉ chạy hai seed

Tổng smoke:

```text
3 configs x 2 algorithms x 2 seeds = 12 runs
```

## E3. Mỗi run phải lưu ngay

Không đợi toàn bộ experiment kết thúc.

CSV phải được flush sau từng run.

Khóa chính:

```text
config_name + algorithm + seed + git_commit + config_hash
```

## E4. Script phải hỗ trợ resume

Nếu dòng đã tồn tại và fingerprint khớp, bỏ qua run đó.

Lệnh mong muốn:

```bash
python scripts/experiment_dbo_idbo_ablation.py \
  --config experiments/ablation_dbo_idbo/config_locked.json \
  --resume \
  --seeds 8001 8002
```

## E5. Tiêu chí qua Gate 4

- không crash;
- paired seeds đầy đủ;
- DBO và IDBO cùng config hash;
- telemetry có giá trị;
- output được lưu incremental;
- chạy lại `--resume` không chạy lại các dòng cũ;
- không có regression test.

Nếu Gate 4 fail: dừng, không chạy 10 seed.

---

# PHẦN F — QUYẾT ĐỊNH CÓ CHẠY FULL HAY KHÔNG

Chỉ được chạy full nếu tất cả đều đúng:

- [ ] Gate 1 pass.
- [ ] Gate 2 pass.
- [ ] Gate 3 có activation > 0.
- [ ] Gate 4 pass đầy đủ.
- [ ] Config đã được review và khóa.
- [ ] Script có `--resume`.
- [ ] CSV lưu sau từng run.
- [ ] Git commit và config hash được ghi.
- [ ] Không ai còn sửa code benchmark.
- [ ] README chưa kết luận nguyên nhân trước dữ liệu.

Nếu thiếu một ô: không chạy full.

---

# PHẦN G — FULL BENCHMARK

## G1. Seeds cố định

```text
8001
8002
8003
8004
8005
8006
8007
8008
8009
8010
```

## G2. Không chạy đồng thời quá mức

Mặc định:

```text
max_workers = 1 hoặc 2
```

Lý do:

- tránh tranh CPU;
- runtime dễ so sánh hơn;
- giảm nhiễu;
- hạn chế lỗi bộ nhớ.

Nếu đo runtime để so sánh, nên chạy tuần tự.

## G3. Metrics bắt buộc

```text
config_name
algorithm
seed
git_commit
config_hash
best_fitness
final_fitness
runtime_s
n_evaluations
calories
n_violations
min_diversity
mean_diversity
final_diversity
max_stagnation
n_diversity_collapse_events
n_stagnation_events
outer_perturbations
outer_restarts
inner_perturbations_total
inner_restarts_total
final_inner_perturbations
final_inner_restarts
```

## G4. Summary bắt buộc

Theo từng config và algorithm:

```text
runs
best
mean
median
std
worst
mean runtime
mean evaluations
total perturbations
total restarts
IDBO wins
IDBO ties
IDBO losses
mean paired difference
```

## G5. Kiểm định

- Nếu mọi paired differences bằng 0: ghi rõ mọi cặp hòa, không chạy Wilcoxon vô nghĩa.
- Nếu có differences: dùng Wilcoxon paired nếu phù hợp.
- Báo cả effect size hoặc ít nhất median paired difference.
- Không kết luận từ một seed duy nhất.

---

# PHẦN H — CÁCH DIỄN GIẢI KẾT QUẢ

## H1. Activation bằng 0 và min diversity luôn lớn hơn threshold

Có thể kết luận:

```text
Trong các cấu hình đã thử, điều kiện diversity collapse không xảy ra.
Ngưỡng hoặc metric diversity hiện chưa phù hợp với representation của bài toán.
```

Không được nói IDBO sai hoàn toàn.

## H2. Activation bằng 0 nhưng stagnation chưa đạt window

Kết luận:

```text
Cấu hình chưa tạo đủ trì trệ để đánh giá restart.
```

## H3. Điều kiện diversity và stagnation đều đạt nhưng activation vẫn bằng 0

Kết luận:

```text
Có lỗi logic hoặc wiring cần sửa.
```

## H4. Activation > 0 nhưng fitness bằng nhau

Kết luận:

```text
IDBO có hành vi tìm kiếm khác nhưng chưa cải thiện chất lượng nghiệm trên instance hiện tại.
```

## H5. IDBO tốt hơn

Chỉ dùng nếu:

- nhiều paired seeds tốt hơn;
- chênh lệch không chỉ do một outlier;
- paired statistics hỗ trợ;
- runtime overhead được báo;
- test và constraints đều pass.

## H6. IDBO kém hơn

Báo trung thực. Kiểm tra:

- perturbation phá nghiệm tốt;
- restart quá mạnh;
- runtime tăng;
- variance tăng;
- final result có thật sự dùng global best-so-far hay không.

---

# PHẦN I — KIỂM TRA BẤT THƯỜNG KHI TĂNG SỐ VÒNG

Nếu mean fitness giảm khi tăng số vòng, phải kiểm tra:

- [ ] `best_fitness` có phải global best-so-far không?
- [ ] `final_fitness` có khác `best_fitness` không?
- [ ] history best-so-far có đơn điệu không?
- [ ] inner seeds có phụ thuộc số lần outer objective được gọi không?
- [ ] benchmark 25 và 100 vòng có thật sự là cùng trajectory prefix không?
- [ ] objective outer có nhiễu do inner stochastic optimization không?

Không giải thích được mục này thì không dùng cấu hình 150 vòng làm bằng chứng hiệu năng chính.

---

# PHẦN J — CẬP NHẬT SLIDE

Chỉ cập nhật slide sau khi full benchmark hoàn tất và được review.

## J1. Slide chỉ hiển thị

```text
Baseline 25 vòng
Một cấu hình chẩn đoán đại diện
Perturbations / Restarts
Wins / Ties / Losses
Một câu kết luận
```

Chi tiết để trong README.

## J2. Câu dùng khi chưa chứng minh IDBO tốt hơn

```text
Trong phạm vi thử nghiệm hiện tại, chưa ghi nhận IDBO vượt trội hơn DBO.
Telemetry cho thấy cơ chế cải tiến không hoặc ít kích hoạt; nguyên nhân được
xác định dựa trên diversity và stagnation telemetry, không dựa trên suy đoán.
```

## J3. Không được viết

```text
IDBO vượt trội
IDBO tối ưu hơn
Cơ chế không kích hoạt chắc chắn do diversity
```

trừ khi dữ liệu trực tiếp chứng minh.

## J4. Kiểm tra slide

- [ ] số test lấy từ pytest thật;
- [ ] số fitness khớp CSV;
- [ ] perturbation/restart khớp CSV;
- [ ] không overflow;
- [ ] không dùng ảnh cũ;
- [ ] không hard-code kết luận trái README;
- [ ] PowerPoint và PDF đều được build lại.

---

# PHẦN K — CHECKLIST TRƯỚC KHI MERGE

## Code

- [ ] Dispatch đúng.
- [ ] IDBO parameters truyền đúng.
- [ ] Telemetry trực tiếp, không suy diễn.
- [ ] Controlled activation hoạt động.
- [ ] Tests kiểm tra hành vi thật, không chỉ kiểm tra kiểu dữ liệu.
- [ ] Script hỗ trợ resume.
- [ ] Script lưu sau từng run.
- [ ] Config hash và git commit được ghi.

## Kết quả

- [ ] Paired seeds đầy đủ.
- [ ] Không trộn run từ commit khác.
- [ ] Không có NaN.
- [ ] Wins/ties/losses tính đúng.
- [ ] Summary khớp raw CSV.
- [ ] README chỉ kết luận theo dữ liệu.

## Test

- [ ] Full pytest pass.
- [ ] Log pytest được lưu.
- [ ] Số test trên slide khớp log.

## Slide

- [ ] Build thành công.
- [ ] Không overflow.
- [ ] Không tuyên bố quá mức.
- [ ] DBO/IDBO được diễn giải đúng.

## Handoff

- [ ] `PROJECT_STATE.md` cập nhật.
- [ ] `CHANGELOG_AI.md` cập nhật.
- [ ] `latest_changes.patch` được tạo.
- [ ] checksum được tạo.
- [ ] manifest file thay đổi được tạo.
- [ ] bundle được tạo nếu có binary.

---

# PHẦN L — CÂU TRẢ LỜI CHO GIÁO VIÊN

## Nếu chưa có khác biệt

> Nhóm đã chạy paired ablation trên cùng seed và ghi trực tiếp telemetry của IDBO. Trong cấu hình hiện tại, DBO và IDBO cho chất lượng nghiệm tương đương. Cơ chế perturbation/restart không hoặc ít kích hoạt trong Two-Tier, nên nhóm chưa có bằng chứng để kết luận IDBO tốt hơn. Nhóm đang điều chỉnh metric và điều kiện activation cho representation rời rạc, đồng thời vẫn giữ Web tách khỏi implementation thuật toán bằng một interface cấu hình được.

## Nếu controlled activation hoạt động nhưng benchmark chính không hoạt động

> Nhóm đã xác minh wiring Two-Tier và IDBO hoạt động qua controlled activation. Tuy nhiên, ở benchmark chính, điều kiện activation không đạt theo telemetry diversity/stagnation. Vì vậy nguyên nhân nằm ở sự phù hợp của metric hoặc threshold với bài toán, không phải do hệ thống gọi nhầm DBO.

---

# PHẦN M — NGUYÊN TẮC TIẾT KIỆM THỜI GIAN

1. Không chạy full trước khi bốn gate pass.
2. Mỗi người chỉ làm một nhiệm vụ hẹp.
3. Không ai ngoài người tích hợp được sửa slide kết luận.
4. Smoke trước, full sau.
5. CSV phải lưu incremental.
6. Script phải resume được.
7. Cấu hình phải có hash.
8. Khi code thay đổi, kết quả cũ phải được xem là historical.
9. Không chạy lại chỉ vì thay đổi giao diện Web.
10. Nhánh Web và nhánh nghiên cứu IDBO phải tách riêng.
