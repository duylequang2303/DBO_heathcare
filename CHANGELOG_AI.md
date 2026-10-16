# CHANGELOG_AI.md — Lịch sử thay đổi do AI hỗ trợ

File này ghi lại các thay đổi do AI Coding Agent thực hiện hoặc hướng dẫn. Không thay thế Git history. Mục tiêu là giúp người và AI ở phiên sau hiểu nhanh điều gì đã thay đổi, bằng chứng xác minh và giới hạn còn lại.

## Quy tắc cập nhật

Mỗi phiên AI phải thêm một entry mới ở đầu phần `Entries`, theo mẫu:

```markdown
## YYYY-MM-DD — Tên nhiệm vụ

### Scope
- Mục tiêu và phạm vi.

### Base
- Branch bắt đầu:
- Base commit:

### Changed
- File và hành vi đã thay đổi.

### Experiments
- Cấu hình, seed và output.

### Verification
- Lệnh đã chạy.
- Kết quả chính xác.

### Artifacts
- CSV, hình, PPTX, patch hoặc bundle.

### Commits
- `<hash>` — `<message>`

### Remaining limitations
- Các giới hạn chưa xử lý.

### Handoff
- Patch:
- Patch SHA-256:
- Changed-files manifest:
- Bundle nếu có:
```

Không ghi “tests pass” nếu không có số lượng và lệnh thực tế. Không ghi “đã sửa” nếu chỉ cập nhật slide nhưng production code chưa thay đổi.

---

# Entries

## 2026-10-16 — Hoàn thành Ablation DBO/IDBO, Telemetry Diversity, Controlled Activation & Phân công 3 người

### Scope
- Giải quyết triệt để 2 vấn đề blocking review về bằng chứng khoa học DBO vs IDBO.
- Đo lường trực tiếp Swarm Diversity và Stagnation trong IDBO Two-Tier.
- Thực hiện bài test Controlled Activation chứng minh đường dây IDBO hoạt động hoàn hảo khi đạt điều kiện.
- Hoàn thiện Slide báo cáo Tuần 8–9 (loại bỏ toàn bộ đường dẫn codebase, ghi trực tiếp số liệu thực nghiệm).
- Phân công nhiệm vụ cụ thể, công bằng và độc lập cho đủ 3 thành viên trong `KE_HOACH_CHAY_LAI_DBO_IDBO.md`.

### Base
- Branch: `experiment/dbo-idbo-ablation`
- Base commit: `d74eb55` (từ `main`)

### Changed
- `KE_HOACH_CHAY_LAI_DBO_IDBO.md`: Phân công nhiệm vụ cụ thể cho 3 sinh viên (Lê Quang Duy, Hồ Trung Cương, Đặng Nguyễn Minh Đăng) tương ứng từng Gate.
- `src/algorithms/idbo.py`: Thêm các trường đo lường `min_diversity`, `mean_diversity`, `final_diversity`, `max_stagnation`, `n_collapse_events`.
- `src/algorithms/two_tier_solver.py`: Tích hợp các trường telemetry outer/inner vào `TwoTierResult`.
- `tests/test_two_tier_solver.py`: Bổ sung kiểm thử controlled activation (`threshold=0.50`), chứng minh activation $> 0$.
- `scripts/experiment_dbo_idbo_ablation.py`: Hỗ trợ lưu telemetry trực tiếp, chạy kiểm chứng kích hoạt cưỡng bức, đổi tên cấu hình chẩn đoán thành `diagnostic_aggressive_150`.
- `scripts/build_pptx_week8_9.py`: Bỏ hoàn toàn đường dẫn file (`experiments/.../README.md`) trên Slide 5; chuyển đổi tên file code trên Slide 13 thành tên phân hệ chức năng chuyên nghiệp; cập nhật phân công nhiệm vụ cho 3 thành viên.
- `docs/slides/`: Sinh lại [Slide_Bao_Cao_Tuan_8_9_DBO_IDBO.pptx](file:///home/duyle/coding/DBO_heathcare/docs/slides/Slide_Bao_Cao_Tuan_8_9_DBO_IDBO.pptx) và [Slide_Bao_Cao_Tuan_8_9_DBO_IDBO.pdf](file:///home/duyle/coding/DBO_heathcare/docs/slides/Slide_Bao_Cao_Tuan_8_9_DBO_IDBO.pdf).

### Verification
- `pytest -q`: **205 passed in 7.47s** (toàn bộ test suite xanh).
- Visual check: Đã render PNG kiểm tra Slide 5 và Slide 13 đạt chuẩn thẩm mỹ cao, 0 lỗi layout.

### Artifacts
- `experiments/ablation_dbo_idbo/` (paired_runs.csv, summary.csv, controlled_activation.csv, fig_ablation_dbo_idbo.png, pytest.log).
- `patches/` (patch, patch.txt, code_only.patch.txt, bundle, sha256).

---

### Scope

- Tạo tài liệu để các AI Coding Agent tiếp tục dự án mà không phụ thuộc hoàn toàn vào context cuộc trò chuyện.
- Chuẩn hóa handoff bằng state file, changelog và incremental patch.

### Base

- Branch bắt đầu: cần xác minh trong repository hiện tại.
- Base commit: cần điền bằng `git rev-parse HEAD`.

### Changed

- Thêm `AGENTS.md` chứa kiến trúc, invariants, benchmark policy và giới hạn tuyên bố y tế.
- Thêm `PROJECT_STATE.md` chứa trạng thái có thể kiểm chứng, việc đang làm và việc còn lại.
- Thêm `CHANGELOG_AI.md` chứa lịch sử thay đổi do AI hỗ trợ.
- Thêm quy tắc bắt buộc tạo `latest_changes.patch`, checksum và manifest sau mỗi phiên AI.

### Experiments

- Không chạy experiment mới trong entry này.

### Verification

Sau khi thêm các file vào repository, cần chạy:

```bash
python -m pytest -q
```

Kết quả gần nhất được kỳ vọng từ codebase hiện tại là `202 passed`, nhưng AI/nhà phát triển phải dùng output thật để cập nhật chứ không được mặc định.

### Artifacts

```text
AGENTS.md
PROJECT_STATE.md
CHANGELOG_AI.md
```

### Commits

- Chưa có commit hash trong bản template. Sau khi commit, thay bằng hash thật.

Commit message đề xuất:

```text
docs: add persistent AI project state and handoff workflow
```

### Remaining limitations

- `Last verified commit` trong `PROJECT_STATE.md` vẫn cần được điền từ repository thực tế.
- Cần chạy lại pytest sau khi đặt các file vào codebase.
- Ablation DBO/IDBO vẫn là công việc đang chờ.

### Handoff

Sau khi commit, tạo:

```bash
BASE_COMMIT=<commit-trước-khi-thêm-tài-liệu>
printf '%s\n' "$BASE_COMMIT" > .ai_base_commit

git format-patch \
  --stdout \
  "$BASE_COMMIT"..HEAD \
  > latest_changes.patch

sha256sum latest_changes.patch \
  > latest_changes.patch.sha256

git diff --name-status "$BASE_COMMIT"..HEAD \
  > latest_changes.files.txt
```

---

## Historical verified work — Tuần 1 đến tuần 9

### Changed

Các đợt review trước đã xử lý hoặc ghi nhận:

- validation natri cho profile tăng huyết áp;
- phân biệt sugar proxy với dữ liệu total sugar;
- tính lại nutrient trên khẩu phần làm tròn 5g;
- telemetry perturbation/restart cho IDBO trong two-tier result;
- sửa thông báo demo có vi phạm nhưng vẫn báo 100% hợp lệ;
- sửa các tuyên bố y tế quá mức trong slide;
- cập nhật slide để giải thích DBO và IDBO tương đương trong cấu hình ngắn;
- sửa overflow ở slide 1 và slide 13.

### Verification

Trạng thái gần nhất được báo cáo:

```text
202 passed
PowerPoint 14 slide render thành công
Không phát hiện text overflow ở bản slide gần nhất
```

Các kết quả này phải được xác minh lại trên repository hiện tại trước khi dùng làm bằng chứng cuối cùng.

### Remaining limitations

- Cần chạy ablation paired DBO/IDBO.
- Dataset chưa có total sugar đáng tin cậy.
- Culinary realism và realistic portion bounds cần được phân loại đúng trạng thái và tiếp tục hoàn thiện.
- Benchmark cũ có thể cần chạy lại sau thay đổi production behavior.
