# DBO_heathcare - Hệ Thống Đề Xuất Thực Đơn Dinh Dưỡng Cá Nhân Hóa Dựa Trên Thuật Toán DBO Cải Tiến (IDBO)

> **Khóa Luận Cử Nhân Ngành CNTT (2025 - 2026)**
> **Trường Đại Học Công Thương TP.HCM - Khoa Công Nghệ Thông Tin**

---

## 🎯 Mục Tiêu Đề Tài
1. Nghiên cứu và xây dựng mô hình bài toán tối ưu thực đơn dinh dưỡng cá nhân hóa.
2. Xây dựng **Dung Beetle Optimizer cải tiến với cơ chế ngẫu nhiên (IDBO)** nhằm nâng cao khả năng tìm kiếm và tránh cực trị địa phương.
3. Phát triển hệ thống web (FastAPI/Flask/Django + HTML/CSS/JS) hỗ trợ tự động xây dựng và đề xuất thực đơn.
4. Đánh giá, so sánh IDBO với DBO gốc và các phương pháp cơ sở.

---

## 📂 Cấu Trúc Dự Án Dự Kiến

```text
DBO_heathcare/
├── data/                       # Dữ liệu thực phẩm & dinh dưỡng (Tuần 2)
│   ├── raw/                    # Dữ liệu CSV thô thu thập
│   │   └── foods_nutrition_sample.csv
│   ├── processed/              # Dữ liệu CSV đã qua xử lý & làm sạch
│   └── README.md               # Mô tả quy chuẩn cấu trúc dữ liệu
├── src/                        # Mã nguồn chính
│   ├── algorithms/             # Thuật toán DBO, IDBO & các hàm mục tiêu / ràng buộc
│   ├── api/                    # Backend API (FastAPI)
│   ├── models/                 # Mô hình dữ liệu & cơ sở dữ liệu
│   └── utils/                  # Các hàm tiện ích tính toán BMR, TDEE, dinh dưỡng
├── web/                        # Giao diện người dùng (Frontend)
├── docs/                       # Tài liệu đề cương, báo cáo
├── tests/                      # Thử nghiệm benchmark & unit tests
├── requirements.txt            # Thư viện phụ thuộc (numpy, pandas, scipy, fastapi,...)
└── README.md
```
