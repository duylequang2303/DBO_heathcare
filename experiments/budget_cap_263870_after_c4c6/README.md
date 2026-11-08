# Budget cap 263,870 — DBO vs IDBO (sau takeover C4/C6)

## Phạm vi

- Đây là so sánh **cap-matched**, không phải equal-evaluation: `max_evaluations=263870` là trần chung cho Outer + tất cả Inner + final Inner. Số evaluation thực tế của DBO/IDBO khác nhau (xem `function_evaluations`).
- Cấu hình lấy từ hướng dẫn Tuần 11: `outer_diversity_threshold=0.28`, `inner_diversity_threshold=None`, `outer_n_agents=10`, `inner_n_agents=10`, `outer_max_iter=25`, `inner_max_iter=25`, `stagnation_window=25`.
- 10 seed độc lập 8001–8010, chạy paired cùng seed; mỗi seed có một lượt DBO và một lượt IDBO.
- Git commit: xem `config_locked.json`. Cùng config hash giữa các lượt.
- Không đổi tham số sau khi xem kết quả. Không dùng kết quả này để tuyên bố IDBO “tốt hơn” nếu paired evidence không hỗ trợ.

## Tệp

- `config_locked.json`: config + hash + Git commit.
- `runs/*.json`: raw từng lượt.
- `paired_runs.csv`: dữ liệu paired từng lượt.
- `paired_summary.csv`: trung bình, paired difference (IDBO − DBO), số seed IDBO cao hơn/bằng/thấp hơn.

## Kết quả chính

- `best_fitness`: DBO mean 98.803895; IDBO mean 98.746094; paired difference mean **−0.057801** (IDBO cao hơn 2, bằng 5, thấp hơn 3).
- `final_fitness`: DBO 99.395275; IDBO 99.403751; paired difference mean **+0.008475** (cao hơn 3, bằng 5, thấp hơn 2). Đây là khác biệt rất nhỏ, không đủ cơ sở kết luận IDBO vượt trội.
- `function_evaluations`: DBO 68,120 mỗi seed; IDBO 68,120–77,516 (mean +1,983.6). Cap 263,870 không bị chạm.
- `runtime_seconds`: IDBO mean +2.26 s (+8.0%); IDBO chậm hơn ở 8/10 seed.
- Telemetry IDBO: Outer perturbation kích hoạt ở 5/10 seed (0–18 lần), inner perturbation 0 ở mọi seed; outer restart 0. Vì vậy đây là “hành vi khác nhưng chưa cải thiện có ý nghĩa”, không phải bằng chứng IDBO vượt trội.
- Không chạy Wilcoxon vì n=10, nhiều tie và chênh lệch rất nhỏ; báo trực tiếp paired difference, wins/ties/losses. Nếu bổ sung kiểm định, phải ghi rõ giả thuyết và hiệu chỉnh nhiều so sánh.

## Giới hạn

- Chỉ P1, một cấu hình, 10 seed; không ngoại suy cho mọi hồ sơ.
- Fitness là hàm mục tiêu nội bộ, không phải chỉ số sức khỏe.
- Không phải thẩm định lâm sàng.

## Không so trực tiếp với đợt cũ

Đợt `experiments/budget_matched_263870` (PR #39) dùng `outer_max_iter=100` và `inner_diversity_threshold=0.28`, khác cấu hình này (`outer_max_iter=25`, `inner_diversity_threshold=None`). Hai đợt không phải cùng config; không được trích số của đợt cũ như kết quả của code hiện tại.
