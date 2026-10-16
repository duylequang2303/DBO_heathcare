# AGENTS.md — Hướng Dẫn & Khung Kiến Trúc Cho AI Coding Agents (DBO_heathcare)

Tài liệu này là **Single Source of Truth** quy định khung kiến trúc, ranh giới module, quy ước lập trình và các bất biến nghiệp vụ (domain invariants) dành cho AI Coding Agents và các nhà phát triển làm việc trên dự án **DBO_heathcare**.

---

## 1. Tổng Quan Dự Án & Mục Tiêu

* **Mã đề tài:** CNTT-KLCN142 — Trường Đại học Công Thương TP.HCM (HUIT).
* **Mục tiêu chính:** Hệ thống đề xuất thực đơn dinh dưỡng cá nhân hóa dựa trên thuật toán Dung Beetle Optimizer cải tiến với cơ chế ngẫu nhiên (IDBO).
* **Cơ chế tối ưu:** Mixed-Integer Two-Tier Optimization:
  * **Tầng 1 (Outer - Discrete):** Chọn tổ hợp món ăn từ kho dữ liệu thỏa mãn cấu trúc bữa ăn và sở thích/dị ứng.
  * **Tầng 2 (Inner - Continuous):** Tối ưu định lượng khẩu phần gram cho từng món nhằm khớp mục tiêu calo & DRI (Protein, Carbs, Fat, Fiber, Vi chất).

---

## 2. Bản Đồ Kiến Trúc Hệ Thống (Domain-Driven Architecture)

Codebase được tổ chức theo kiến trúc phân tầng rõ rệt:

```
src/
├── models/             # TẦNG NGHIỆP VỤ & RÀNG BUỘC (Core Domain)
│   ├── food_schema.py      # Schema dữ liệu thực phẩm & validation
│   ├── dish_category.py    # Phân loại vai trò món (Staple, Main Protein, Veg, Soup, Snack)
│   ├── meal_structure.py   # Cấu trúc mâm cơm theo Slot chuẩn ẩm thực
│   ├── user_profile.py     # Hồ sơ người dùng, chỉ số BMR, TDEE, dị ứng, mục tiêu
│   ├── menu.py             # Biểu diễn MenuItem, Meal, Menu (encode / decode)
│   ├── constraints.py      # Ràng buộc dinh dưỡng, năng lượng, dị ứng
│   ├── objective.py        # Hàm mục tiêu đa thành phần (Energy, Macro, Preference, Variety)
│   ├── food_sampler.py     # Lọc và lấy mẫu danh sách món hợp lệ
│   └── food_selector.py    # Ánh xạ vector liên tục z sang food_ids qua Linear Probing
│
├── algorithms/         # TẦNG THUẬT TOÁN TỐI ƯU (Pure Math / Metaheuristics)
│   ├── dbo.py              # Dung Beetle Optimizer gốc
│   ├── idbo.py             # Improved Dung Beetle Optimizer (Gaussian / Cauchy perturbation)
│   ├── behaviors.py        # 4 tập tính của bọ hung (Roll, Dance, Breed, Forage, Steal)
│   ├── benchmarks.py       # 23 hàm chuẩn đánh giá metaheuristic (CEC)
│   ├── menu_objective.py   # Adapter biến bài toán Menu thành hàm f(x) liên tục
│   └── two_tier_solver.py  # Bộ giải 2 tầng phối hợp Outer + Inner
│
├── utils/              # TẦNG TIỆN ÍCH & TRUY XUẤT DỮ LIỆU
│   ├── data_loader.py      # Đọc CSV dữ liệu thực phẩm, xây food_map
│   ├── nutrition.py        # Tính BMR (Mifflin-St Jeor), TDEE, DRI target
│   └── portion_utils.py    # Làm tròn khẩu phần về bội số 5g thực tế
│
data/                   # TẦNG DỮ LIỆU THỰC PHẨM
│   ├── raw/                # Dữ liệu gốc (USDA, Viện Dinh Dưỡng VN)
│   └── processed/          # Dữ liệu sạch (merged_food_nutrition.csv)
│
scripts/                # KỊCH BẢN THỰC NGHIỆM & BÁO CÁO THEO TUẦN (1-12)
tests/                  # BỘ TEST AUTOMATION (Bảo đảm không hồi quy)
```

---

## 3. Các Bất Biến Nghiệp Vụ Cốt Lõi (Domain Invariants)

Bất kỳ AI Agent hay lập trình viên nào khi chỉnh sửa code đều **KHÔNG ĐƯỢC VI PHẠM** các quy tắc sau:

1. **Bất biến Cấu trúc Bữa ăn (Culinary Slot Invariant):**
   * Một bữa chính (Trưa / Tối) **không được** gồm các món trùng nhóm vô lý (ví dụ: không bao giờ xếp 2 loại nui khô, hoặc 2 món cơm vào cùng một bữa).
   * Bữa chính chuẩn mực gồm:
     $$\text{Slot 1: Tinh bột (Staple)} + \text{Slot 2: Đạm chính (Main Protein)} + \text{Slot 3: Rau/Canh (Vegetable/Soup)}$$
2. **Bất biến Thực phẩm Tiêu dùng Được (Edibility & Readiness):**
   * Thực đơn đề xuất phải là **thực phẩm đã chế biến / ăn liền được (cooked/ready-to-eat)**.
   * **Tuyệt đối cấm** đề xuất nguyên liệu thô công nghiệp vào bữa ăn hàng ngày: *Bột trứng, bột mì thô, hạt lúa miến sống, thịt sống, bơ shortening, gia vị đậm đặc.*
3. **Bất biến Cận Khẩu Phần Tự Nhiên (Realistic Portion Bounds):**
   * Không cào bằng khẩu phần `[25g, 350g]` cho mọi món. Khẩu phần tối ưu phải tôn trọng giới hạn thực tế theo nhóm:
     * Cơm/tinh bột: $100g - 250g$
     * Thịt/cá/đạm: $60g - 180g$
     * Rau/canh: $100g - 300g$
     * Trái cây/snack: $60g - 200g$
4. **Bất biến Năng Lượng & Dinh Dưỡng:**
   * Năng lượng tổng ngày phải nằm trong biên độ $\pm 10\%$ calo mục tiêu (TDEE/Goal).
   * Protein/Carbs trong $\pm 15\%$, Fat $\pm 20\%$, Fiber $\pm 30\%$.
   * Không có chất dinh dưỡng nào mang giá trị âm hoặc NaN.
5. **Bất biến Giải mã Hai Tầng (Deterministic Decoding):**
   * Ánh xạ từ vector nghiệm $z \in [0, 1)^k$ sang `food_ids` phải có tính xác định (deterministic) khi cùng seed.
   * Định lượng $x \in \mathbb{R}^k$ sau khi tối ưu được làm tròn về bội số $5g$ thực tế.

---

## 4. Quy Ước Lập Trình Cho Coding Agents

1. **Strict Type Annotations:** Mọi hàm mới phải có đầy đủ type hints (`from __future__ import annotations`, `list[str]`, `dict[str, Any]`, `float`, `Optional`).
2. **Pure Functions trong Tầng Thuật Toán:** Các module `src/algorithms/` phải là hàm thuần túy hoặc lớp không lưu state rác giữa các lần chạy. Không dùng biến toàn cục có thể thay đổi.
3. **Reproducibility (Tính tái lập):** Mọi thực nghiệm, tối ưu ngẫu nhiên đều phải nhận tham số `seed` và khởi tạo `np.random.default_rng(seed)`.
4. **Không Thêm Dependency Nặng Ngoài Luồng:** Dự án hiện dùng `numpy`, `pandas`, `pytest`, `matplotlib`. Mọi mô hình dữ liệu ưu tiên dùng `dataclasses` chuẩn của Python 3.12 để đạt tốc độ tối đa trong vòng lặp metaheuristic.

---

## 5. Lệnh Chạy Kiểm Thử & Xác Nhận Nhanh (Fast Verification Commands)

Trước khi kết thúc bất kỳ chỉnh sửa nào, Agent bắt buộc phải chạy bộ test để xác nhận không gây hồi quy (regression):

```bash
# Chạy toàn bộ test suite (bắt buộc tất cả phải PASS)
./venv/bin/pytest

# Chạy riêng test bộ giải hai tầng
./venv/bin/pytest tests/test_two_tier_solver.py -v

# Chạy test ràng buộc & tính hợp lệ của thực đơn
./venv/bin/pytest tests/test_constraints.py tests/test_menu.py -v

# Chạy kịch bản demo kiểm tra tính thực tế của thực đơn
./venv/bin/python scripts/demo_week8.py --outer-iter 5 --inner-iter 5 --seed 42
```
