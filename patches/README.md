# Thư Mục Quản Lý Bản Vá (Patches & Bundles)

Thư mục này lưu trữ các bản vá (patch) và gói commit (bundle) phục vụ chia sẻ, lưu trữ hoặc áp dụng mã nguồn giữa các môi trường.

## 1. Bản vá Nghiên cứu Ablation DBO vs IDBO (Nhánh `experiment/dbo-idbo-ablation`)

Bao gồm toàn bộ 3 commit thực hiện chẩn đoán thực nghiệm DBO vs IDBO, telemetry, và cập nhật slide Tuần 8–9:

- **[dbo_idbo_ablation_code_only.patch.txt](file:///home/duyle/coding/DBO_heathcare/patches/dbo_idbo_ablation_code_only.patch.txt)** (`60 KB` — **Khuyên dùng khi gửi qua Zalo / Email / Chat**):
  - Chứa toàn bộ thay đổi mã nguồn, test, script thực nghiệm, CSV và tài liệu phân tích.
  - Đã loại bỏ dữ liệu nhị phân (binary PPTX/PDF) nên file rất nhẹ, mở xem được ngay bằng Text Editor.
  - Cách áp dụng:
    ```bash
    git apply patches/dbo_idbo_ablation_code_only.patch.txt
    ```

- **[dbo_idbo_ablation.patch.txt](file:///home/duyle/coding/DBO_heathcare/patches/dbo_idbo_ablation.patch.txt)** & **[dbo_idbo_ablation.patch](file:///home/duyle/coding/DBO_heathcare/patches/dbo_idbo_ablation.patch)** (`508 KB`):
  - Bản vá git diff binary đầy đủ $100\%$, bao gồm cả PPTX, PDF và đồ thị PNG.
  - Cách áp dụng:
    ```bash
    git apply patches/dbo_idbo_ablation.patch
    ```

- **[dbo_idbo_ablation.bundle](file:///home/duyle/coding/DBO_heathcare/patches/dbo_idbo_ablation.bundle)** (`253 KB`):
  - Gói Git bundle chứa nguyên vẹn lịch sử 3 commits (`69d277c`, `3788180`, `bd1c3bd`).
  - Cách giải nén vào nhánh mới:
    ```bash
    git checkout -b experiment/dbo-idbo-ablation
    git pull patches/dbo_idbo_ablation.bundle HEAD
    ```

---

## 2. Bản vá Lịch sử khác

- **[fix_build_pptx_week8_9.patch](file:///home/duyle/coding/DBO_heathcare/patches/fix_build_pptx_week8_9.patch)**: Bản vá căn chỉnh bố cục slide và khắc phục tràn bảng trước đây.
