# Multi-Agent Tester Plan: Báo cáo thực đơn bằng tiếng Việt dễ hiểu

## Vấn đề cốt lõi

Đầu ra hiện tại của hệ thống dùng tên thức phẩm kỹ thuật và mã food_id, người dùng không hiểu:

- `Cereals ready-to-eat, POST, Honey Nut Shredded Wheat`
- `USDA_173894`

Yêu cầu: mỗi món trong báo cáo phải có **tên tiếng Việt dễ hiểu**, giải thích món ăn là gì, cách ăn/chế biến đơn giản, khẩu phần (g). Không chỉ liệt kê số liệu thô và mã ID.

## Mục tiêu

Xây dựng hệ thống multi-agent (subagent thay con người) để:
1. Tự sinh hồ sơ kiểm thử (tuổi, cân nặng, giới tính, cường độ vận động, nhu cầu dinh dưỡng).
2. Tự chạy hệ thống đề xuất thực đơn trên các hồ sơ đó.
3. Tự kiểm tra logic nghiệp vụ (năng lượng, macrom, dị ứng, vai trò món, phần ăn).
4. Tự viết báo cáo tiếng Việt: mỗi món có tên dễ hiểu, mô tả, cách ăn, phần ăn, cảnh báo nếu vi phạm.

## Quyết định thiết kế

1. **Giao diện:** CLI script trên terminal. Chạy một lệnh, hệ thống tự sinh profiles và chạy test.
2. **Subagent roles:**
   - `profile-agent`: Sinh hồ sơ kiểm thử ngẫu nhiên.
   - `runner-agent`: Chạy two-tier solver trên mỗi profile.
   - `validator-agent`: Kiểm tra ràng buộc business (năng lượng, macrom, dị ứng, vai trò món, phần ăn).
   - `reviewer-agent`: Kiểm tra đầu ra báo cáo — đảm bảo không có mã ID kỹ thuật, tên tiếng Anh khó hiểu, món nguyên liệu thô xuất hiện như món ăn; xác nhận mỗi món có tên tiếng Việt, mô tả, cách ăn, phần ăn. Báo cáo vi phạm nếu đầu ra khó hiểu.
   - `reporter-agent`: Dịch tên thức phẩm sang tiếng Việt, viết báo cáo dễ hiểu (món là gì, ăn như thế nào, phần bao nhiêu).
3. **Đầu ra:** Báo cáo văn bản tiếng Việt, không có mã ID kỹ thuật hoặc tên tiếng Anh khó hiểu.

## Rang buộc từ AGENTS.md

- §4.4: Làm tròn khẩu phần: continuous → round 5g → decode → recalc → validate → report trên nghiệm đã làm tròn.
- §4.5: Không đề xuất nguyên liệu thô, bột công nghiệp, gia vị như món độc lập.
- §4.7: Giới hạn phần ăn theo vai trò (staple 100–250g, protein 60–180g, rau 100–300g, v.v.).
- §4.2: Không dùng proxy đường như dữ liệu đo thực tế.
- §6.2: Không silently fallback IDBO sang DBO.
- §6.3: IDBO telemetry phải được báo cáo.
- §10: Chỉ sửa file cần thiết.

## Danh sách công việc (ordered)

1. **Xác định ánh xạ tên thức phẩm sang tiếng Việt** — tra cứu food_map, lấy food_name, sinh tên tiếng Việt dễ hiểu + mô tả món ăn + cách ăn đơn giản (ví dụ: "Bánh mì", "Cơm", "Thịt gà nấu", "Rau xào").
2. **Tạo module báo cáo tiếng Việt** (`src/models/report.py` hoặc tương tự) — nhận Menu, food_map, kết quả validate, xuất báo cáo văn bản tiếng Việt.
3. **Tạo `scripts/multi_agent_tester.py`** — CLI điều phối pipeline: sinh profile → chạy solver → validate → viết báo cáo tiếng Việt.
4. **Viết test** — kiểm tra:
   - Báo cáo không chứa mã ID kỹ thuật (USDA_..., VN_...) hoặc tên tiếng Anh khó hiểu không có giải thích tiếng Việt.
   - Mỗi món có tên tiếng Việt, loại, khẩu phần, cách ăn.
   - Reviewer-agent phát hiện được đầu ra khó hiểu và báo cáo vi phạm.
   - Nếu vi phạm ràng buộc, báo cáo trình bày bằng tiếng Việt dễ hiểu.
5. **Chạy demo smoke test** — xác nhận báo cáo tiếng Việt dễ hiểu, 0 vi phạm (hoặc vi phạm được mô tả rõ ràng bằng tiếng Việt).

## Kết quả xác nhận (definition of done)

- Lệnh `python scripts/multi_agent_tester.py --seed 42` thành công, xuất báo cáo tiếng Việt.
- Báo cáo mỗi món: tên tiếng Việt, loại món, khối lượng (g), cách ăn đơn giản.
- Reviewer-agent xác nhận đầu ra dễ hiểu cho người dùng (không có mã ID kỹ thuật, tên tiếng Anh khó hiểu, món nguyên liệu thô như món ăn độc lập).
- Nếu vi phạm ràng buộc, báo cáo nêu rõ bằng tiếng Việt.
- Tất cả pytest tests hiện tại vẫn pass.

## Mục ra ngoài phạm vi

- Giao diện web/trình duyệt.
- Xuất PDF/Excel.
- Cơ sở dữ liệu người dùng thực.
