# Hướng dẫn & Quy chuẩn Cấu trúc Dữ liệu Dinh dưỡng (Tuần 2)

Theo đề cương khóa luận:
- **Nội dung Tuần 2:** Nghiên cứu nhu cầu năng lượng, các thành phần dinh dưỡng và lựa chọn nguồn dữ liệu thực phẩm phù hợp.
- **Yêu cầu dữ liệu:** Xây dựng cơ sở dữ liệu thực phẩm gồm năng lượng (calories), protein, carbohydrate, chất béo (fat), chất xơ (fiber) và một số vi chất cần thiết (sodium, calcium, iron, vitamin...).

---

## 1. Cấu trúc thư mục `data/`

```text
data/
├── raw/                      # Chứa các file CSV dữ liệu thô thu thập ban đầu
│   └── foods_nutrition_sample.csv  # File CSV mẫu với các trường chuẩn
├── processed/                # Dữ liệu CSV sau khi đã làm sạch, chuẩn hóa đơn vị
└── README.md                 # Tài liệu mô tả cấu trúc trường dữ liệu
```

---

## 2. Quy chuẩn các cột trong file CSV thực phẩm (`foods.csv`)

| Tên cột | Kiểu dữ liệu | Đơn vị | Mô tả |
| :--- | :--- | :--- | :--- |
| `food_id` | Integer / String | - | Mã định danh thực phẩm / món ăn |
| `food_name` | String | - | Tên món ăn / thực phẩm (VD: Ức gà áp chảo, Cơm trắng,...) |
| `category` | String | - | Phân loại (Thịt, Hải sản, Rau củ, Trái cây, Tinh bột, Canh, v.v.) |
| `meal_type` | String | - | Phù hợp cho bữa nào: `breakfast`, `lunch`, `dinner`, `snack`, `all` |
| `serving_size_g` | Float | gram (g) | Khối lượng 1 khẩu phần chuẩn (VD: 100g hoặc 1 phần ăn) |
| `calories` | Float | kcal | Năng lượng |
| `protein_g` | Float | g | Chất đạm (Protein) |
| `carbs_g` | Float | g | Carbohydrate (Tinh bột/Đường) |
| `fat_g` | Float | g | Tổng chất béo (Fat) |
| `fiber_g` | Float | g | Chất xơ (Fiber) |
| `sodium_mg` | Float | mg | Natri (Sodium) |
| `calcium_mg` | Float | mg | Canxi (Calcium) |
| `iron_mg` | Float | mg | Sắt (Iron) |
| `vitamin_a_mcg` | Float | mcg | Vitamin A |
| `vitamin_c_mg` | Float | mg | Vitamin C |
| `price_vnd` | Float | VNĐ | Giá tiền ước lượng (nếu cần) |
| `allergy_warnings` | String | - | Cảnh báo dị ứng (hải sản, đậu phộng, trứng,...) |
