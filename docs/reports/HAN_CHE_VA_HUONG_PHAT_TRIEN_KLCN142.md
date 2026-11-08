# HẠN CHẾ CỦA ĐỀ TÀI VÀ HƯỚNG PHÁT TRIỂN TIẾP THEO
**Khóa luận tốt nghiệp CNTT-KLCN142 – ĐH Công Thương TP.HCM**
*Hệ thống đề xuất thực đơn dinh dưỡng cá nhân hóa bằng thuật toán tối ưu hóa bọ phân lai (DBO/IDBO)*

---

## 1. Giới thiệu

Đề tài CNTT-KLCN142 đã thành công trong việc xây dựng một hệ thống prototype hỗ trợ quyết định (decision-support prototype) theo kiến trúc tối ưu hai tầng **Mixed-Integer Two-Tier**:
- **Tầng ngoài (Discrete Outer Tier)**: Giải quyết bài toán tổ hợp rời rạc, chọn lựa danh mục món ăn `food_ids` phù hợp với sở thích, dị ứng và cơ cấu bữa ăn văn hóa Việt Nam.
- **Tầng trong (Continuous Inner Tier)**: Giải quyết bài toán tối ưu liên tục, tinh chỉnh khẩu phần gram chính xác cho từng món ăn nhằm thỏa mãn các ràng buộc calo, đa lượng (protein, carbs, fat, fiber) và vi lượng (natri).

Mặc dù hệ thống đã đáp ứng đầy đủ các yêu cầu kỹ thuật và vượt qua 435+ bài kiểm thử tự động (unit tests, integration tests, contract tests), nhóm nghiên cứu nghiêm túc nhìn nhận và minh bạch các **hạn chế nội tại** của đề tài dưới góc độ khoa học và thực tiễn lâm sàng.

---

## 2. Các hạn chế trọng tâm của đề tài

### 2.1. Thành phần hằng số trong hàm mục tiêu tổng thể
- **Thực trạng**: Hàm mục tiêu tổng quát được cấu hình theo dạng kết hợp tuyến tính đa tiêu chí:
  $$F(M) = 0.35 \cdot S_{energy} + 0.30 \cdot S_{macros} + 0.20 \cdot S_{pref} + 0.15 \cdot S_{div} - \text{Penalty}$$
  Trong các kịch bản người dùng không nhập danh sách món thích/ghét (`likes`, `dislikes`) hoặc trong các bữa ăn đơn lẻ, điểm sở thích $S_{pref}$ và điểm đa dạng $S_{div}$ ít biến thiên, hoạt động như một thành phần cộng hằng số.
- **Giải trình & Minh bạch**: Để bảo toàn tính nhất quán và không làm xáo trộn toàn bộ các kết quả thực nghiệm lịch sử sát ngày bảo vệ, nhóm giữ nguyên cấu trúc hàm mục tiêu nhưng **luôn báo cáo song song** các chỉ số đo trực tiếp:
  - Sai số calo tuyệt đối trung bình (MAE kcal).
  - Độ lệch phần trăm của các chất đa lượng (protein, carbs, fat, xơ).
  - Tỷ lệ vi phạm các ngưỡng ràng buộc dinh dưỡng.

### 2.2. Đánh đổi giữa số lượng đánh giá tầng ngoài và độ trễ phản hồi Web API
- **Thực trạng**: Ở chế độ trực tuyến trên giao diện Web (`balanced` / `fast`), thuật toán tầng ngoài chỉ được cấp ngân sách khoảng 200–300 lượt đánh giá để đảm bảo thời gian phản hồi dưới 28 giây cho người dùng. Điều này khiến tỷ lệ vi phạm ràng buộc dinh dưỡng ở cấu hình nhanh cao hơn so với khi chạy cấu hình đầy đủ (full-scale iterations).
- **Ý nghĩa kỹ thuật**: Đây là sự đánh đổi có chủ đích (trade-off) giữa **trải nghiệm người dùng tương tác thời gian thực** và **độ hội tụ tối đa của thuật toán metaheuristic**. Khi tăng số cá thể và số vòng lặp lên mức nghiên cứu (offline), chất lượng thực đơn đạt độ chính xác gần như tuyệt đối (sai lệch calo dưới 1%).

### 2.3. Cơ chế Thay món (Swap) ưu tiên quyền quyết định của người dùng
- **Thực trạng**: Báo cáo kiểm toán tự động (Audit Report) ghi nhận trong 5 kịch bản người dùng liên tục đổi món, có 2 trường hợp điểm fitness tổng thể bị giảm so với thực đơn ban đầu.
- **Nguyên nhân**: Hệ thống hiện tại tôn trọng tối đa quyền tự quyết của người dùng (user agency) — nếu người dùng chủ động muốn ăn món mới, hệ thống sẽ giữ nguyên món đó và tối ưu lại khẩu phần gram của các món còn lại thay vì từ chối yêu cầu của người dùng.
- **Hướng khắc phục**: Bổ sung cơ chế *soft-rejection* hoặc thanh cảnh báo tương tác (vd: *"Món ăn này khiến thực đơn bị lệch protein +18%, bạn có chắc chắn muốn đổi không?"*).

### 2.4. Tầng trong sử dụng Metaheuristic thay vì Quy hoạch tuyến tính (LP/MILP)
- **Thực trạng**: Với hàm mục tiêu dinh dưỡng hiện tại (sai lệch tuyến tính so với ngưỡng mục tiêu), bài toán tối ưu khẩu phần gram ở tầng trong hoàn toàn có thể được giải rất nhanh và chính xác bằng Quy hoạch tuyến tính (Linear Programming - Simplex). Việc sử dụng DBO/IDBO cho tầng trong khiến thời gian tính toán kéo dài hơn.
- **Lý do lựa chọn**: Nhóm duy trì kiến trúc metaheuristic đồng nhất ở cả 2 tầng nhằm tạo tiền đề cho việc mở rộng sang các hàm mục tiêu phi tuyến phức tạp hơn trong tương lai (ví dụ: chỉ số đường huyết hấp thu phi tuyến Glycemic Load, hiệu ứng cộng hưởng hấp thu giữa sắt và vitamin C). Trong ngắn hạn, việc kết hợp LP cho tầng trong là một hướng phát triển rất hứa hẹn để rút ngắn độ trễ.

### 2.5. Dữ liệu thực phẩm và chỉ số dinh dưỡng
- **Hồ sơ mô phỏng**: Các hồ sơ bệnh nhân P1 (Khỏe mạnh), P2 (Tiểu đường), P3 (Tăng huyết áp) là các hồ sơ mô phỏng kỹ thuật phục vụ benchmark, chưa bao quát toàn bộ phổ bệnh lý phức tạp trong đời sống thực.
- **Kho món ăn hiển thị (Whitelist 163 món)**: Được chọn lọc và làm sạch từ cơ sở dữ liệu lớn để đảm bảo tên món chuẩn Việt Nam và vai trò ẩm thực hợp lý, tuy nhiên danh mục này còn khiêm tốn so với ẩm thực phong phú của các vùng miền Việt Nam.
- **Chỉ số đường (Sugar Proxy)**: Cơ sở dữ liệu hiện tại chưa có trường đo đạc đường tổng (total sugar). Hệ thống sử dụng giá trị ước tính có nhãn minh bạch (`sugar_proxy_g`, `sugar_is_estimated = True`) và **tuyệt đối không dùng proxy này để tuyên bố thực đơn "an toàn tuyệt đối cho bệnh nhân tiểu đường"**.

### 2.6. Giới hạn về thử nghiệm lâm sàng và đối chứng y tế
- **Định vị sản phẩm**: Đề tài được xây dựng dưới dạng **nguyên mẫu hỗ trợ quyết định (decision-support prototype)** dành cho mục đích nghiên cứu và tham khảo, **không phải là thiết bị y tế (medical device)** được cấp phép.
- **Thử nghiệm**: Hệ thống chưa được thử nghiệm lâm sàng trên bệnh nhân thực tế tại các cơ sở y tế và chưa có điều kiện thử nghiệm đối chứng trực tiếp (A/B testing) với các phần mềm dinh dưỡng độc quyền có bản quyền y khoa quốc tế. Mọi khuyến nghị của hệ thống cần có sự tham vấn của chuyên gia dinh dưỡng hoặc bác sĩ điều trị.

### 2.7. Chuẩn hóa ngưỡng dinh dưỡng khuyến nghị
- Các ngưỡng nhu cầu năng lượng và trần natri trong nghiên cứu hiện tham chiếu theo tiêu chuẩn **DRI/RDA (Hoa Kỳ)** và **AHA (Hiệp hội Tim mạch Hoa Kỳ)** kết hợp công thức Mifflin-St Jeor.
- Hướng tiếp theo cần làm là chuẩn hóa triệt để 100% theo **Bảng Nhu cầu Dinh dưỡng Khuyến nghị cho người Việt Nam** do Viện Dinh dưỡng - Bộ Y tế ban hành.

---

## 3. So sánh đối chuẩn DBO vs IDBO và Baseline

Theo nguyên tắc minh bạch thực nghiệm của đề tài (AGENTS.md):
1. **So với Random Search Baseline (cùng ngân sách đánh giá)**: Cả DBO và IDBO đều đạt điểm fitness vượt trội có ý nghĩa thống kê rất cao ($p < 0.001$, kiểm định Wilcoxon signed-rank), chứng minh cơ chế mô phỏng bọ phân thực sự học và hội tụ tối ưu tốt hơn tìm kiếm ngẫu nhiên.
2. **So sánh IDBO vs DBO**:
   - Khi cấu hình `stagnation_window` nhỏ (3–5 vòng lặp) và `diversity_threshold` được hiệu chỉnh tách biệt theo từng tầng, các cơ chế cải tiến của IDBO (**Random Restart** và **Adaptive Cauchy Perturbation**) đã **kích hoạt thành công** theo đúng thiết kế ghi nhận qua telemetry.
   - Tuy nhiên, trên không gian bài toán thực đơn 12 chiều với các ràng buộc dinh dưỡng chặt chẽ, chất lượng nghiệm tối ưu cuối cùng của IDBO tương đương DBO ($p \ge 0.05$). Nhóm nghiên cứu kết luận trung thực: *"Trong phạm vi cấu hình và instance dữ liệu thử nghiệm, chưa ghi nhận bằng chứng thống kê cho thấy IDBO vượt trội hơn DBO về chất lượng thực đơn cuối cùng"*.

---

## 4. Hướng phát triển tiếp theo

1. **Kiến trúc Hybrid Heuristic-LP**: Tích hợp bộ giải tuyến tính (Simplex/Interior Point) cho tầng trong để giảm thời gian phản hồi từ 28 giây xuống dưới 2 giây.
2. **Làm giàu cơ sở dữ liệu ẩm thực Việt Nam**: Thu thập thêm các món ăn truyền thống 3 miền, bổ sung trường đo lường trực tiếp cho đường tự do và chỉ số đường huyết (GI).
3. **Cơ chế phản hồi tương tác (Interactive Rejection)**: Nâng cấp tính năng swap món với hệ số cảnh báo rủi ro tương tác khi người dùng chọn món làm lệch mục tiêu dinh dưỡng.
4. **Chuẩn hóa Bộ Y tế & Thử nghiệm chuyên gia**: Đưa thực đơn đề xuất gửi cho 10–20 chuyên gia/bác sĩ dinh dưỡng đánh giá độc lập (chấm điểm cảm quan, tính khả thi chế biến và độ an toàn bệnh lý).

