# AGENTS.md — DBO_heathcare

Prototype hỗ trợ quyết định thực đơn dinh dưỡng cá nhân hóa bằng DBO/IDBO
(đề tài CNTT-KLCN142, ĐH Công Thương TP.HCM). Không phải thiết bị y tế.
Kiến trúc Mixed-Integer Two-Tier: outer (rời rạc) chọn `food_ids`;
inner (liên tục) tối ưu khẩu phần gram.

Nếu tài liệu này mâu thuẫn với code/test, báo rõ mâu thuẫn và ưu tiên bằng chứng
chạy được. Ưu tiên khi xung đột: an toàn dữ liệu > quy tắc đã có test > tái lập
thực nghiệm > phạm vi nhiệm vụ > kiến trúc > quy tắc đang hoàn thiện.

## Ranh giới module
- `src/models/`: logic nghiệp vụ, schema, validation.
- `src/algorithms/`: tối ưu tổng quát, không chứa business rules.
- `scripts/`: điều phối pipeline, không sao chép logic production.
- `tests/`: phải gọi production code thật.
- Slide và báo cáo lấy số liệu từ CSV/output truy vết được, không hard-code kết luận.

## Bất biến nghiệp vụ (đã có test bảo vệ, không được làm hỏng)
- Năng lượng ngày ±10%; protein, carbohydrate ±15%; fat ±20%; fiber ±30%.
  Không có nutrient âm, NaN hoặc vô hạn. Chỉ gọi natri là ràng buộc khi
  production validation thực sự kiểm tra `sodium_mg`.
- Dữ liệu đường: dataset hiện tại không có total sugar. Không trình bày
  `carbs * 0.15` như dữ liệu đo thực tế. Proxy phải đặt tên rõ (`sugar_proxy_g`,
  `sugar_is_estimated = True`) và không dùng để kết luận "an toàn cho tiểu đường".
  Phân biệt dữ liệu đo được / suy ra / proxy trong API, CSV, slide, báo cáo.
- Deterministic: cùng input, seed, candidate pools thì cùng mapping z -> food_ids.
  Mọi thuật toán ngẫu nhiên nhận `seed` và dùng `np.random.default_rng(seed)`,
  không dùng RNG hay state toàn cục.
- Làm tròn: nghiệm liên tục -> làm tròn 5 g -> decode -> tính lại nutrient ->
  validate -> báo metrics cuối. Không báo fitness của nghiệm liên tục rồi hiển thị
  thực đơn đã làm tròn khác.

## Đang hoàn thiện (chưa ENFORCED; chi tiết ở docs/ROADMAP.md)
Không mô tả là đã hoàn thiện và không tuyên bố đã chặn nếu demo/test còn tạo được:
loại nguyên liệu thô/gia vị/dầu khỏi output người dùng, culinary slots,
portion bounds theo role.

## Giới hạn tuyên bố y tế
- Không viết "an toàn tuyệt đối", "điều trị", "chữa", "đạt chuẩn lâm sàng",
  "đạt AHA" khi chưa có thẩm định tương ứng.
- Diễn đạt mặc định: "Đáp ứng/không đáp ứng ngưỡng dinh dưỡng được cấu hình
  trong thử nghiệm". P1/P2/P3 là hồ sơ mô phỏng cho benchmark.
- Thiếu dữ liệu thì nói rõ giới hạn, không suy diễn.

## Thuật toán
- Không mutable global state trong `src/algorithms/`; mỗi `optimize()` độc lập.
- `two_tier_solver.py` dispatch đúng class. Không silent fallback IDBO -> DBO;
  tên thuật toán không hợp lệ phải báo lỗi rõ ràng.
- IDBO trả telemetry: `n_perturbations`, `n_restarts`, stagnation. Không kết luận
  cơ chế hiệu quả nếu telemetry cho thấy nó chưa kích hoạt.

## Benchmark DBO vs IDBO
- So sánh paired cùng seed, cùng objective, bounds, population size, dữ liệu;
  ưu tiên cùng số lần đánh giá objective. Không đổi tham số sau khi xem kết quả
  để IDBO thắng. Cấu hình kiểm tra kích hoạt gọi là `diagnostic`, không phải
  benchmark chính.
- Báo: best/mean/median/std/worst fitness, runtime, n_evaluations, perturbations,
  restarts, paired difference (IDBO − DBO), wins/ties/losses; dùng Wilcoxon nếu
  phù hợp. Nếu mọi paired difference bằng 0: ghi rõ, không ép chạy kiểm định,
  kết luận "tương đương trong phạm vi thử nghiệm".
- Diễn giải: không kích hoạt -> cấu hình chưa cho phép đánh giá cải tiến;
  kích hoạt nhưng fitness không khác -> hành vi khác nhưng chưa cải thiện có ý nghĩa;
  IDBO tốt hơn -> chỉ trong phạm vi instance/cấu hình đã thử, kèm paired evidence;
  IDBO kém hơn -> báo trung thực runtime, variance, khả năng perturbation phá nghiệm tốt.

## Provenance
- Không chỉnh tay `data/processed/` nếu không có script tái tạo.
- Không ghi đè benchmark lịch sử; kết quả mới vào thư mục riêng
  (`experiments/<tên>/` có README, config, raw paired runs, summary CSV, figures).
- Output cũ không còn đại diện cho code mới thì đánh dấu historical và chạy lại
  trước khi cập nhật kết luận. Nếu CSV mới hơn figure: dựng lại figure hoặc báo lỗi.

## Phạm vi thay đổi
- Chỉ sửa file cần cho nhiệm vụ; không refactor toàn codebase ngoài yêu cầu.
- Không gộp sửa dữ liệu, thuật toán và slide vào một commit.
- Không đưa `.venv`, cache, secrets vào Git. Không merge thẳng vào `main` cho
  nhiệm vụ thử nghiệm; thay đổi lớn thì tạo branch riêng. Không force push.

## Kiểm tra (Python 3.12, interpreter của environment đang active)
    python -m pytest -q
    python scripts/demo_week8.py --outer-iter 5 --outer-agents 6 \
        --inner-iter 5 --inner-agents 6 --seed 42
Kiểm tra output, không chỉ exit code: không nutrient âm/NaN; menu sau làm tròn
vẫn validate; không có nguyên liệu thô như món độc lập; không dùng proxy sugar như
dữ liệu đo; DBO/IDBO báo đúng telemetry; cùng seed cho cùng kết quả.

## Slide và báo cáo
- Số liệu lấy từ CSV mới nhất được chỉ định rõ; tổng số tests lấy từ pytest thực tế.
- Nếu DBO và IDBO bằng nhau, ghi: "Trong cấu hình thử nghiệm hiện tại, chưa ghi
  nhận IDBO vượt trội hơn DBO."
- Sau khi sửa script slide: dựng lại PowerPoint, kiểm tra không tràn chữ, không còn
  hình/số liệu cũ.

## Khi kết thúc nhiệm vụ
Báo: file đã đọc/sửa, test đã chạy và kết quả chính xác, seed/cấu hình, nơi lưu
output mới, giới hạn chưa xử lý, có cần chạy lại benchmark/slide không, commit hash.
Không nói "đã hoàn tất" nếu chưa chạy các bước kiểm tra ở trên.