# PROJECT_STATE.md — Trạng thái hiện tại của DBO_heathcare

> File này là bản tóm tắt trạng thái có thể kiểm chứng của dự án. AI Coding Agent phải đọc `AGENTS.md`, sau đó đọc file này trước khi sửa code. Trước khi kết thúc mỗi nhiệm vụ, AI phải cập nhật file này bằng kết quả thật đã chạy.

## 1. Repository snapshot

- Project: `DBO_heathcare`
- Main language: Python 3.12
- Current branch: `experiment/dbo-idbo-ablation`
- Last verified commit: `651f674` (hoàn thiện loại bỏ đường dẫn codebase trên slide và trình bày số liệu thực nghiệm trực tiếp)
- Last verified date: `2026-10-16`
- Current milestone: Hoàn thành chẩn đoán Ablation DBO/IDBO và đồng bộ Slide Tuần 8–9

## 2. Verified status

Các mục dưới đây đã được xác minh thực tế trên codebase hiện tại:

- Test suite gần nhất: **`205 passed in 7.47s`**
- Lệnh xác minh và file log lưu trữ:

```bash
python -m pytest -v > experiments/ablation_dbo_idbo/pytest.log
```

- Slide tuần 8-9 đã được sinh từ:

```text
scripts/build_pptx_week8_9.py
```

- PowerPoint đầu ra:

```text
docs/slides/Slide_Bao_Cao_Tuan_8_9_DBO_IDBO.pptx
docs/slides/Slide_Bao_Cao_Tuan_8_9_DBO_IDBO.pdf
```

- Slide đã được kiểm tra bố cục không có text overflow hoặc chồng lấn canvas.
- Slide 5 có khối đối chứng chẩn đoán "KIỂM TRA KÍCH HOẠT CƠ CHẾ IDBO (ABLATION DIAGNOSTIC)".
- IDBO telemetry có các trường đo lường trực tiếp:
  * `outer_min_diversity`, `outer_mean_diversity`, `outer_final_diversity`
  * `outer_max_stagnation`, `outer_collapse_events`
  * `outer_perturbations`, `outer_restarts`
  * `inner_perturbations_total`, `inner_restarts_total`
- Controlled activation test (`diversity_threshold=0.50`, `stagnation_window=2`) chứng minh pipeline Two-Tier IDBO kích hoạt bình thường khi điều kiện thỏa mãn.
- Validation natri cho profile tăng huyết áp đã được bổ sung.
- Khẩu phần 5g được dùng để decode, tính lại dinh dưỡng và validation.
- Dataset hiện chưa có trường total sugar đáng tin cậy.
- Giá trị `carbs * 0.15`, nếu còn tồn tại, chỉ là proxy kỹ thuật và không được dùng để kết luận y tế.

> Nếu bất kỳ mục nào không còn đúng sau thay đổi, AI phải sửa mục đó ngay. Không được giữ số test, đường dẫn hoặc kết luận cũ chỉ vì chúng từng đúng.

## 3. Current findings

### DBO và IDBO

- Benchmark 10 paired seeds (8001–8010) qua 3 cấu hình (`baseline_short`, `diagnostic_balanced`, `diagnostic_aggressive_150`) cho DBO và IDBO kết quả đồng nhất 100% (10/10 hòa, hiệu số $\Delta = 0.0000$).
- Bằng chứng telemetry trực tiếp: `outer_min_diversity` thấp nhất quan sát được là 0.2422 > các ngưỡng `diversity_threshold` (0.001, 0.01, 0.05), do đó điều kiện collapse không xảy ra (0 perturbations, 0 restarts).
- Controlled activation test khẳng định Two-Tier IDBO wiring hoạt động hoàn hảo khi thiết lập ngưỡng thích hợp ($0.50$).
- Kết quả hiện tại chưa chứng minh IDBO vượt trội hơn DBO trên bài toán tối ưu thực đơn 2 tầng. Nhóm báo cáo trung thực, không suy diễn vượt quá dữ liệu đo được.

### Nutrition and medical claims

- Natri có dữ liệu trực tiếp và có thể được kiểm tra nếu production validation thực sự dùng `sodium_mg`.
- Total sugar chưa có dữ liệu trực tiếp.
- P1/P2/P3 là profile mô phỏng phục vụ benchmark kỹ thuật.
- Không dùng “an toàn y tế”, “đạt AHA”, “điều trị” hoặc kết luận lâm sàng trong code, CSV, slide hay báo cáo.

### Culinary realism

- Culinary roles, ingredient filtering và realistic portion bounds phải được đánh dấu đúng trạng thái `ENFORCED`, `PARTIAL` hoặc `TARGET` theo `AGENTS.md`.
- Không được tuyên bố đã loại bỏ hoàn toàn nguyên liệu thô nếu demo hoặc test vẫn sinh ra được nguyên liệu như món độc lập.

## 4. Active work

### Current task

Chạy ablation DBO/IDBO để xác định:

1. dispatch có đúng DBO/IDBO không;
2. tham số IDBO có được truyền đúng không;
3. perturbation/restart có kích hoạt không;
4. IDBO thắng, hòa hoặc thua trên bao nhiêu paired seeds;
5. khác biệt có ý nghĩa thống kê hay không;
6. slide tuần 8-9 cần cập nhật kết luận nào.

### Expected branch

```text
experiment/dbo-idbo-ablation
```

### Expected outputs

```text
scripts/experiment_dbo_idbo_ablation.py
experiments/ablation_dbo_idbo/paired_runs.csv
experiments/ablation_dbo_idbo/summary.csv
experiments/ablation_dbo_idbo/paired_differences.csv
experiments/ablation_dbo_idbo/fig_ablation_dbo_idbo.png
experiments/ablation_dbo_idbo/README.md
```

## 5. Pending tasks

1. Chạy smoke benchmark ablation trên 2 paired seeds.
2. Chạy đủ 10 paired seeds nếu smoke test ổn định.
3. Kiểm tra telemetry IDBO bằng objective gây stagnation có chủ đích.
4. Cập nhật slide 5 hoặc 6 bằng kết quả ablation thật.
5. Sinh lại PowerPoint và kiểm tra overflow.
6. Cập nhật tổng số test theo output pytest thật.
7. Tiếp tục hoàn thiện DishRole, Culinary Slots và realistic portion bounds theo trạng thái trong `AGENTS.md`.
8. Bổ sung nguồn dữ liệu total sugar đáng tin cậy trước khi áp ràng buộc đường thật.

## 6. Known limitations

- Không có total sugar đáng tin cậy trong dataset hiện tại.
- Benchmark lịch sử có thể không còn đại diện nếu validation hoặc portion pipeline thay đổi.
- DBO và IDBO chưa được phân biệt rõ về hiệu năng ở cấu hình ngắn hiện tại.
- Candidate filtering và serving bounds cần được xác minh bằng demo thực tế, không chỉ unit tests.
- Runtime hiện tại chưa được xem là bằng chứng đạt mục tiêu Web/API dưới 1.5 giây/ngày.

## 7. Mandatory verification before completion

AI phải chạy các lệnh phù hợp với phạm vi thay đổi:

```bash
python -m pytest -q
python -m pytest tests/test_two_tier_solver.py -v
python -m pytest tests/test_constraints.py tests/test_menu.py -v
```

Nếu có các file test realism:

```bash
python -m pytest tests/test_data_integrity.py tests/test_culinary_realism.py -v
```

Nếu sửa slide:

```bash
python scripts/build_pptx_week8_9.py
```

AI phải báo chính xác:

- số test passed/failed;
- seed và cấu hình experiment;
- file output;
- commit hash;
- giới hạn chưa xử lý.

## 8. Handoff protocol for future AI sessions

Khi bắt đầu phiên mới, cung cấp tối thiểu:

```text
AGENTS.md
PROJECT_STATE.md
CHANGELOG_AI.md
latest_changes.patch
```

Nếu patch quá lớn hoặc chứa binary, cung cấp thêm incremental bundle hoặc các binary artifact riêng.

AI mới phải:

1. đọc `AGENTS.md`;
2. đọc `PROJECT_STATE.md`;
3. đọc các entry mới nhất trong `CHANGELOG_AI.md`;
4. chạy `git status --short --branch`;
5. xác minh base commit của patch;
6. không giả định patch đã được áp dụng nếu chưa kiểm tra Git history hoặc working tree.

## 9. Bắt buộc tạo patch sau mỗi phiên AI

Trước khi chỉnh sửa, AI phải lưu base commit:

```bash
BASE_COMMIT=$(git rev-parse HEAD)
printf '%s\n' "$BASE_COMMIT" > .ai_base_commit
```

Sau khi sửa, test và commit xong, AI phải tạo patch chứa toàn bộ commit mới kể từ base:

```bash
git format-patch \
  --stdout \
  "$(cat .ai_base_commit)"..HEAD \
  > latest_changes.patch
```

Nếu thay đổi chưa commit, tạo thêm working-tree patch:

```bash
git diff --binary > latest_worktree.patch
git diff --cached --binary > latest_staged.patch
```

Kiểm tra patch commit có thể áp dụng:

```bash
git apply --check latest_changes.patch
```

> `git apply --check` không phải lúc nào phù hợp với mail patch từ `git format-patch`. Khi cần giữ commit history, kiểm tra trong clone tạm bằng `git am --3way latest_changes.patch`.

Cách kiểm tra an toàn trong clone tạm:

```bash
TMP_DIR=$(mktemp -d)
git clone . "$TMP_DIR/repo"
cd "$TMP_DIR/repo"
git reset --hard "$(cat /path/to/original/repo/.ai_base_commit)"
git am --3way /path/to/original/repo/latest_changes.patch
python -m pytest -q
```

Sau khi tạo patch, AI phải cập nhật các trường sau trong file này:

```text
Last verified commit
Last verified date
Test result
Current branch
Current milestone
Active work
Pending tasks
Known limitations
```

AI phải thêm entry tương ứng vào `CHANGELOG_AI.md`.

## 10. Patch delivery rules

- `latest_changes.patch` chỉ chứa thay đổi text và commit metadata phù hợp.
- Binary lớn như PPTX, PNG hoặc dataset nên được cung cấp riêng hoặc qua incremental Git bundle.
- Nếu patch có binary nhỏ và thực sự cần thiết, dùng `git diff --binary`.
- Không đưa secret, `.env`, token, `.venv`, cache hoặc temporary files vào patch.
- Ghi SHA-256 để phát hiện file truyền lỗi:

```bash
sha256sum latest_changes.patch > latest_changes.patch.sha256
```

- AI phải liệt kê các file được patch bao phủ:

```bash
git diff --name-status "$(cat .ai_base_commit)"..HEAD \
  > latest_changes.files.txt
```

## 11. End-of-session output contract

Trước khi kết thúc, AI phải để lại:

```text
PROJECT_STATE.md                # trạng thái mới nhất
CHANGELOG_AI.md                 # entry của phiên vừa làm
latest_changes.patch            # commit patch từ base đến HEAD
latest_changes.patch.sha256     # checksum
latest_changes.files.txt        # danh sách file thay đổi
```

Nếu có binary hoặc lịch sử Git phức tạp, tạo thêm:

```text
latest_changes.bundle
```

Bằng lệnh:

```bash
git bundle create latest_changes.bundle \
  "$(cat .ai_base_commit)"..HEAD
```

AI không được kết luận “đã hoàn tất” nếu chưa cập nhật handoff files hoặc chưa giải thích rõ vì sao không thể tạo chúng.
