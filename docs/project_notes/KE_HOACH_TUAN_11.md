# KẾ HOẠCH THỰC HIỆN TUẦN 11

**Chủ đề:** Hoàn thiện đánh giá DBO và IDBO, kiểm tra tính công bằng của thực nghiệm và cập nhật kết quả vào hệ thống Web/API đã xây dựng ở tuần 10.

---

## 1. Mục tiêu tuần 11

- Hoàn thiện phần so sánh giữa DBO và IDBO.
- Xác định rõ lợi ích và chi phí của IDBO khi dùng ngưỡng độ đa dạng 0,28.
- Kiểm tra lại tính công bằng giữa hai thuật toán theo số lần tính hàm mục tiêu.
- Phân biệt hoạt động của IDBO tại tầng chọn món (Outer) và tầng điều chỉnh khẩu phần (Inner).
- Cập nhật Web/API bằng cấu hình thuật toán đã được chốt.
- Chuẩn hóa kết luận để đưa vào báo cáo và slide.
- Không chạy lại các thí nghiệm cũ nếu không cần thiết.

---

## 2. Kết quả đã có trước tuần 11

Nhóm đã chọn `diversity_threshold = 0,28` làm **ngưỡng ứng viên**.

### Tập hiệu chỉnh (Calibration set):
- **Seed 8001–8002**.
- Chỉ dùng để lựa chọn ngưỡng ứng viên.
- Không dùng làm bằng chứng chính để kết luận IDBO tốt hơn.

### Tập đánh giá độc lập (Independent Evaluation set):
- **Seed 8003–8010** (N=8).
- IDBO thắng 5 lần và thua 3 lần (5W / 0T / 3L).
- Chênh lệch điểm trung bình: **+0,1659**.
- Chênh lệch điểm trung vị: **+0,1115**.
- Thời gian chạy tăng khoảng **7,22 giây**, tương đương **14,6%** (DBO: 49,39s → IDBO: 56,61s).
- Kiểm định thống kê:
  - Wilcoxon signed-rank test: $p = 0,6406$.
  - Sign test: $p = 0,7266$.
  - **Khác biệt chưa có ý nghĩa thống kê ở mức 0,05.**

> **Kết luận hiện tại:**  
> IDBO đã tạo ra hành vi tìm kiếm khác DBO và có xu hướng cải thiện nhẹ điểm số. Tuy nhiên, với số lần chạy hiện tại, nhóm chưa có đủ bằng chứng để khẳng định IDBO tốt hơn DBO một cách ổn định.

---

## 3. Nội dung công việc tuần 11

### 3.1. Chuẩn hóa kết quả DBO và IDBO
- Tổng hợp kết quả từ hai tập:
  - Tập hiệu chỉnh: seed 8001–8002.
  - Tập đánh giá độc lập: seed 8003–8010.
- Báo cáo riêng kết quả của tập đánh giá độc lập.
- Không gộp hai seed hiệu chỉnh vào kết quả chính mà không chú thích.
- Giữ ngưỡng 0,28 cố định.
- Không tiếp tục thay đổi ngưỡng dựa trên kết quả seed 8003–8010.
- Ghi rõ IDBO thắng, hòa và thua trên từng seed.
- Ghi cả điểm số, thời gian, số lần tính hàm mục tiêu và số lần kích hoạt cơ chế bổ sung.

### 3.2. Kiểm tra tính công bằng theo ngân sách tính toán (Budget-Matched Benchmark)
So sánh hiện tại đã dùng:
- Cùng số vòng lặp.
- Cùng số cá thể.
- Cùng dữ liệu.
- Cùng seed.
- Cùng hàm đánh giá.

*Tuy nhiên, IDBO thực hiện thêm các bước xáo trộn và khởi động lại nên có nhiều lần tính hàm mục tiêu hơn DBO (~291k so với 263k lượt đánh giá).*

**Nhiệm vụ tuần 11:**
- Bổ sung giới hạn chung về số lần tính hàm mục tiêu (`max_evaluations`).
- Cho DBO và IDBO dừng khi đạt cùng ngân sách tính toán.
- Trước tiên chạy kiểm tra với 2 seed.
- Chỉ chạy tập đánh giá đầy đủ nếu cơ chế dừng hoạt động đúng.
- So sánh kết quả “cùng số vòng” với kết quả “cùng số lần tính”.

**Kết quả cần trả lời:**
1. IDBO cải thiện nhờ cơ chế tìm kiếm hay nhờ được sử dụng thêm tài nguyên tính toán?
2. Khi dùng cùng ngân sách, IDBO còn giữ được xu hướng cải thiện hay không?

### 3.3. Tách ngưỡng tầng ngoài và tầng trong
Hiện `diversity_threshold = 0,28` được truyền cho cả hai tầng:
- Tầng ngoài: chọn tổ hợp món (không gian rời rạc).
- Tầng trong: điều chỉnh số gram (không gian liên tục).

**Nhiệm vụ:**
- Bổ sung hai tham số riêng trong `TwoTierConfig`:
  - `outer_diversity_threshold`
  - `inner_diversity_threshold`
- Giữ `outer_diversity_threshold = 0,28` trong giai đoạn hiện tại.
- Đo độ đa dạng thực tế của tầng trong.
- Chưa tự chọn `inner_diversity_threshold` nếu chưa có số liệu.
- Không dùng chung một ngưỡng chỉ vì thuận tiện.
- Thêm unit tests để xác nhận hai ngưỡng được truyền đúng vào từng solver.

### 3.4. Phân tích hoạt động của tầng trong
Một số seed không kích hoạt ở tầng ngoài nhưng IDBO vẫn cho kết quả khác DBO vì cơ chế bổ sung hoạt động ở tầng trong (như đã xác minh tại seed 8007 và 8008).

**Cần lưu các số liệu:**
- `inner_perturbations_total`
- `inner_restarts_total`
- `final_inner_perturbations`
- `final_inner_restarts`
- Số lần tính hàm mục tiêu ở tầng trong (`inner_evals_total`)
- Điểm trả về từ tầng trong
- Thời gian chạy tầng trong

**Mục tiêu:**
- Giải thích rõ tầng nào tạo ra khác biệt giữa DBO và IDBO.
- Không kết luận toàn bộ cải thiện đến từ tầng ngoài.
- Kiểm tra xem mức kích hoạt tại tầng trong có quá cao hay không.

### 3.5. Cập nhật Web/API đã hoàn thành ở tuần 10
*Không xây dựng lại Web/API. Chỉ cập nhật phần thông tin thuật toán:*
- Cho phép chọn DBO hoặc IDBO bằng cấu hình (query param / request body).
- IDBO dùng ngưỡng ứng viên 0,28 ở tầng ngoài.
- Trả về payload đầy đủ:
  - `algorithm_requested`
  - `algorithm_used`
  - `seed`
  - `best_fitness`
  - `runtime_s`
  - `outer_perturbations`
  - `outer_restarts`
  - `n_evaluations`
  - `n_violations`

**Quy tắc hiển thị giao diện:**
- **Tuyệt đối không hiển thị:**
  - ❌ *“IDBO vượt trội hơn DBO”*
  - ❌ *“IDBO tối ưu nhất”*
  - ❌ *“Thực đơn an toàn tuyệt đối”*
  - ❌ *“Đạt chuẩn y tế”*
- **Có thể hiển thị:**
  - ✓ *“Thuật toán được sử dụng: IDBO”*
  - ✓ *“Thời gian xử lý: ...s”*
  - ✓ *“Điểm đánh giá: ...”*
  - ✓ *“Không ghi nhận vi phạm trong bộ điều kiện kỹ thuật đang kiểm tra”*

---

## 4. Phân công công việc (3 Thành viên)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MA TRẬN PHÂN CÔNG TUẦN 11                             │
├────────────────────────┬─────────────────────────┬──────────────────────────┤
│ Lê Quang Duy (Nhóm Trưởng)│ Hồ Trung Cương        │ Đặng N. Minh Đăng        │
│ Báo cáo, Thống kê, Slide│ Budget & Dual Threshold │ Web/API Metadata & UX    │
│ Mục 3.1, 4, 8, 9, 10   │ Mục 3.2, 3.3, 3.4       │ Mục 3.5                  │
└────────────────────────┴─────────────────────────┴──────────────────────────┘
```

### Thành viên 1: Lê Quang Duy (Nhóm trưởng / Báo cáo & Thống kê)
- Tổng hợp kết quả DBO và IDBO từ hai tập (hiệu chỉnh vs độc lập).
- Kiểm tra lại các phép tính thống kê (Wilcoxon, Sign test, mean, median).
- Tạo bảng thắng, hòa, thua rõ ràng.
- Cập nhật báo cáo Word và Slide tuần 11.
- Kiểm tra câu chữ, tuyệt đối không kết luận vượt quá dữ liệu.

### Thành viên 2: Hồ Trung Cương (Budget-Matched & Phân tách ngưỡng)
- Bổ sung cơ chế giới hạn số lần tính hàm mục tiêu (`max_evaluations`) cho cả hai solver.
- Tách tham số hai ngưỡng: `outer_diversity_threshold` và `inner_diversity_threshold`.
- Bổ sung các trường telemetry theo dõi hoạt động chi tiết ở cả hai tầng.
- Viết unit tests cho cách truyền tham số và điều kiện dừng ngân sách.
- Chỉ chạy thử nghiệm ngắn (smoke test 2 seed) trước khi chạy benchmark đầy đủ.

### Thành viên 3: Đặng Nguyễn Minh Đăng (Tích hợp Web/API & Trải nghiệm)
- Cập nhật metadata thuật toán trong Web/API (FastAPI backend & Frontend UI).
- Hiển thị rõ ràng thuật toán, seed, thời gian, số lần gọi hàm và điểm kết quả.
- Kiểm tra luồng cho phép người dùng chuyển đổi giữa DBO và IDBO.
- Kiểm tra xử lý lỗi, timeout và phản hồi khi bộ giải không hoàn thành.
- Không sửa thuật toán hoặc tự ý chạy benchmark đầy đủ.

---

## 5. Quy tắc chạy thử nghiệm

1. Không thay đổi ngưỡng 0,28 trong tập đánh giá chính.
2. Không sử dụng seed 8003–8010 để tiếp tục hiệu chỉnh ngưỡng.
3. Mọi lần chạy phải lưu kết quả ngay sau khi hoàn thành từng seed (incremental flush).
4. Script phải hỗ trợ chạy tiếp (`--resume`), không chạy lại các seed đã có.
5. Mỗi kết quả phải lưu commit Git và mã cấu hình (`config_hash`).
6. Không trộn kết quả từ các commit hoặc cấu hình khác nhau.
7. Không chạy benchmark đầy đủ khi kiểm thử ngắn (smoke) chưa đạt.
8. Không chạy lại benchmark chỉ vì thay đổi giao diện Web.
9. Nếu code thuật toán thay đổi, kết quả cũ phải được ghi rõ là kết quả lịch sử (historical).

---

## 6. Các trường dữ liệu cần lưu

Mọi bản ghi thực nghiệm phải lưu trữ tối thiểu các trường sau:

```text
- algorithm
- seed
- outer_diversity_threshold
- inner_diversity_threshold
- best_fitness
- final_fitness
- runtime_seconds
- function_evaluations
- outer_min_diversity
- outer_mean_diversity
- outer_max_stagnation
- outer_collapse_events
- outer_perturbations
- outer_restarts
- inner_perturbations_total
- inner_restarts_total
- final_inner_perturbations
- final_inner_restarts
- number_of_violations
- git_commit
- config_hash
```

---

## 7. Điều kiện được phép chạy benchmark đầy đủ

Chỉ chạy benchmark đầy đủ khi thỏa mãn **tất cả 8 điều kiện**:
- [ ] Các kiểm thử thuật toán đều đạt (100% pytest PASS).
- [ ] Hai ngưỡng tầng ngoài và tầng trong được truyền đúng và độc lập.
- [ ] Giới hạn số lần tính hàm mục tiêu hoạt động chính xác.
- [ ] Kết quả được lưu tự động sau từng seed.
- [ ] Chế độ chạy tiếp (`--resume`) hoạt động tin cậy.
- [ ] Cấu hình đã được khóa (`config_locked.json`).
- [ ] Không thành viên nào còn đang sửa script benchmark.
- [ ] Kết quả 2 seed thử nghiệm ngắn (smoke test) đã được review và kiểm tra.

> **Nếu thiếu dù chỉ một điều kiện: DỪNG LẠI, KHÔNG CHẠY ĐẦY ĐỦ.**

---

## 8. Kết quả cần có cuối tuần 11

1. Bảng đối chuẩn DBO và IDBO chuẩn hóa.
2. Kết quả riêng biệt của 8 seed đánh giá độc lập.
3. Bảng thắng, hòa, thua chi tiết.
4. Chênh lệch điểm trung bình và trung vị.
5. Kết quả kiểm định thống kê (Wilcoxon, Sign test).
6. So sánh thời gian chạy thực tế.
7. So sánh số lần tính hàm mục tiêu giữa hai thuật toán.
8. Báo cáo phân tích hoạt động tầng ngoài và tầng trong.
9. Kết quả thử nghiệm đối chuẩn cùng ngân sách tính toán (Budget-matched).
10. Báo cáo Word Tuần 11 (`docs/BaoCao_Tuan11.docx`).
11. Slide PowerPoint báo cáo Tuần 11.
12. Log kiểm thử hệ thống.
13. Patch thay đổi mã nguồn.
14. `PROJECT_STATE.md` được cập nhật đầy đủ.
15. `CHANGELOG_AI.md` được ghi nhận chi tiết.

---

## 9. Câu kết luận dự kiến cho Báo cáo Tuần 11

> Sau khi lựa chọn ngưỡng ứng viên 0,28 bằng hai seed hiệu chỉnh, nhóm giữ cố định ngưỡng và đánh giá trên tám seed độc lập. IDBO thắng 5 và thua 3, với chênh lệch điểm trung bình +0,1659 và trung vị +0,1115. Thời gian chạy tăng khoảng 14,6%. Tuy nhiên, khác biệt chưa có ý nghĩa thống kê với cỡ mẫu hiện tại.  
>  
> Kết quả xác nhận IDBO đã tạo ra hành vi tìm kiếm khác DBO ở cả tầng chọn món và tầng điều chỉnh khẩu phần. IDBO có xu hướng cải thiện nhẹ nhưng chưa đủ bằng chứng để khẳng định vượt trội. Tuần 11 tiếp tục kiểm tra tính công bằng theo cùng số lần tính hàm mục tiêu và tách ngưỡng cho hai tầng trước khi đưa ra kết luận cuối cùng.

---

## 10. Câu ngắn để trình bày với Giảng viên Hướng dẫn

> *“Trong tuần 11, nhóm tập trung hoàn thiện đánh giá DBO và IDBO. Ngưỡng 0,28 được chọn từ tập hiệu chỉnh và giữ cố định khi đánh giá trên tám seed độc lập. IDBO thắng 5 và thua 3, nhưng mức cải thiện còn nhỏ và chưa có ý nghĩa thống kê. Vì IDBO sử dụng thêm số lần tính hàm mục tiêu, nhóm sẽ bổ sung phép so sánh cùng ngân sách tính toán để xác định lợi ích đến từ cơ chế cải tiến hay từ chi phí xử lý tăng thêm.”*
