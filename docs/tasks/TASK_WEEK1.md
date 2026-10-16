# Phân Công Công Việc Tuần 1 — Tổng Quan Bài Toán & Phương Pháp Tối Ưu

Nhóm: Lê Quang Duy (trưởng nhóm) · Đặng Nguyễn Minh Đăng · Hồ Trung Cương

> File hồi tố ghi nhận tiến độ tuần 1 (17/08/2026 – 23/08/2026). Toàn bộ nội dung đã thực hiện, lưu làm hồ sơ theo lộ trình đề cương.

## Mục tiêu tuần 1 (theo đề cương)
Tổng quan bài toán lập thực đơn, dinh dưỡng cá nhân hóa và các phương pháp tối ưu; từ đó định hướng chọn thuật toán và phạm vi đề tài.

## Trạng thái
Tuần nghiên cứu lý thuyết, chưa phát sinh mã nguồn chính thức. Sản phẩm chính là outline nghiên cứu + quyết định chọn DBO làm phương pháp trung tâm.

## Nội dung đã nghiên cứu

### 1. Bài toán lập thực đơn (meal planning)
- [x] Khảo sát bài toán: chọn món + khẩu phần cho các bữa trong ngày thỏa nhu cầu dinh dưỡng.
- [x] Xác định đặc thù: ràng buộc đa dạng (năng lượng, macro, sở thích, dị ứng, không lặp món), không gian nghiệm rời rạc + liên tục.
- [x] Tham khảo Amiri et al. "Personalized Flexible Meal Planning" (JMIR 2023) về mô hình hóa bài toán thực đơn linh hoạt.

### 2. Dinh dưỡng cá nhân hóa
- [x] Tìm hiểu khái niệm nhu cầu năng lượng (BMR/TDEE) và mục tiêu dinh dưỡng theo người dùng.
- [x] Tổng hợp các nhóm chất dinh dưỡng cần quản lý: năng lượng, protein, carb, fat, fiber + vi chất (sodium, calcium, iron, vitamin C).
- [x] Ghi nhận tham chiếu Dietary Reference Intakes (DRI) làm cơ sở ngưỡng dinh dưỡng cho tuần 2–3.

### 3. Phương pháp tối ưu
- [x] Rà soát metaheuristic phổ biến: GA, PSO, ACO, Differential Evolution.
- [x] Nghiên cứu Dung Beetle Optimizer (Xue & Shen, 2023): ý tưởng 4 hành vi, ưu điểm hội tụ nhanh, điểm yếu dễ hội tụ sớm ở một số hàm.
- [x] Quyết định chọn **DBO** làm phương pháp nền + hướng cải tiến bằng cơ chế ngẫu nhiên (IDBO) — tương ứng mục tiêu khóa luận.

## Phân công (ghi nhận)

| Thành viên | Nội dung chính |
| :--- | :--- |
| Lê Quang Duy (trưởng) | Chủ trì outline, tổng hợp phương pháp tối ưu, chốt chọn DBO/IDBO |
| Đặng Nguyễn Minh Đăng | Nghiên cứu nhu cầu năng lượng & DRI |
| Hồ Trung Cương | Khảo sát dữ liệu thực phẩm sẵn có & bài toán thực đơn |

## Đầu ra cuối tuần 1
- [x] Outline khóa luận 12 tuần thống nhất (phản ánh trong README).
- [x] Tài liệu tham khảo chính xác định: DBO (Xue & Shen), Amiri et al. (JMIR), DRI.
- [x] Định hướng công nghệ: Python, NumPy/Pandas, web FastAPI/Flask.

## Quy ước chung
- Tuần 1 là nền lý thuyết; các quyết định kỹ thuật được chốt lại và dùng cho các tuần sau.
- Không phát sinh mã nguồn ở tuần này.

## Tài liệu tham khảo
1. J. Xue and B. Shen, "Dung beetle optimizer: a new meta-heuristic algorithm for global optimization," The Journal of Supercomputing, vol. 79, pp. 7305-7336, 2023.
2. M. Amiri, J. Li, and W. Hasan, "Personalized Flexible Meal Planning for Individuals With Diet-Related Health Concerns," JMIR Formative Research, vol. 7, e46434, 2023.
3. National Academies of Sciences, Engineering, and Medicine, Dietary Reference Intakes for Energy, 2023.
