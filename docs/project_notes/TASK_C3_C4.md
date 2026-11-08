# TASK C3 + C4 — 2026-11-08

## Mục tiêu chung

Sửa hai vấn đề nghiêm trọng còn lại sau feedback của thầy Nghĩa:

- **C3:** hệ thống hiển thị danh sách nguyên liệu thô như “thực đơn”, người dùng không ăn trực tiếp được hoặc không biết chế biến.
- **C4:** vai trò món/cơ cấu bữa bị chê sai hàng loạt (“toàn bộ 169 thực đơn chưa đúng vai trò”), và trùng món trong ngày.

Nhánh gốc để làm: `fix/c4-c6-takeover` (commit mới nhất tại thời điểm giao việc: `8e87db3`).

**Không làm trên PR #39.** PR #39 có số liệu cũ/không đủ provenance; nếu cần dữ liệu audit/budget, dùng `experiments/audit_after_c4c6_clean/` và `experiments/budget_cap_263870_after_c4c6/`.

## Quy tắc chung — bắt buộc

1. Không chỉnh tay `data/processed/`. Chỉ được đổi overlay `data/vn_food_display.json` hoặc thêm overlay mới nếu thật sự cần.
2. Không dùng lớp ghép món/relabel như “Gạo lứt” → “Cơm gạo lứt” mà giữ nguyên nutrient raw rồi gọi là món ăn.
3. Không hard-code kết luận trong báo cáo. Số liệu phải lấy từ audit/CSV mới.
4. Không báo “đã giải quyết triệt để” nếu audit còn lỗi hoặc pool bị vỡ ngưỡng tối thiểu.
5. Nếu pool sau khi siết role/whitelist còn dưới `MIN_ROLE_POOL_SIZE = 3` hoặc meal pool dưới `MIN_MEAL_POOL_SIZE = 20`, **báo lỗi/dừng**, không fallback im lặng.
6. Không dùng dữ liệu có năng lượng không khớp macro: kiểm tra `calories ≈ 4×protein + 4×carbs + 9×fat`; sai lệch lớn bất thường thì loại candidate.
7. Mỗi PR phải có:
   - test mới/đọc rõ;
   - `python -m pytest -q`;
   - demo P1;
   - audit black-box mới trong `experiments/<tên>/` với `raw_requests.jsonl`, `raw_menus.jsonl`, `summary.json`, `REPORT.md`, `README.md`;
   - `python scripts/check_audit_report.py experiments/<tên>` PASS.
8. Không gộp C3 (dữ liệu/whitelist), C4 (thuật toán/role), báo cáo/slides vào một commit. Tách commit rõ ràng.

## Phân công đề xuất

- **Cương — C3: dữ liệu món ăn được / thay nguyên liệu thô trong whitelist người dùng.**
- **Đăng — C4: vai trò món, cơ cấu bữa, kiểm chứng lại role pools và audit vai trò.**

---

# TASK C3 — Cương: “Người dùng nhận được món ăn được, không phải nguyên liệu thô”

## Phạm vi

Chỉ xử lý **whitelist người dùng** (`data/vn_food_display.json`; hiện ~183 entries, ~137 món user-facing tại audit mới), **không** xử lý toàn bộ 13.709 hoặc 15.929 dòng dữ liệu nguồn.

Không được tuyên bố “toàn bộ kho dữ liệu đã là thực đơn món ăn”.

## Bước 1 — Inventory và phân loại

Tạo bảng rà soát, ví dụ `experiments/c3_whitelist_inventory/whitelist_audit.csv`, gồm:

```text
food_id, display_name, current_category, current_role,
verdict, replacement_id, replacement_name, reason, atwater_ok, notes
```

`verdict` chỉ được nhận:

- `keep_ready_to_eat`: món/food item ăn được trực tiếp (trái cây, sữa, trứng luộc, đậu phụ, món nấu chín…)
- `replace_with_cooked`: thay bằng bản cooked/eatable trong `merged_food_nutrition.csv`
- `remove_from_user_facing`: không đủ điều kiện là món người dùng ăn trực tiếp
- `keep_with_warning`: giữ nhưng phải đánh dấu giới hạn rõ trong `data_limitations` (case hiếm)

## Bước 2 — Candidate thay thế phải đạt tiêu chí

Chỉ nhận candidate cooked/eatable nếu:

1. Cùng nhóm thực phẩm thật sự: gạo → cơm/gạo nấu chín; đậu → đậu nấu chín; khoai → khoai luộc/nướng; không lấy spaghetti để thay cơm nếu không giải thích.
2. `calories` hợp lý với macro:
   - chấp nhận sai lệch nhỏ: `abs(kcal - (4P + 4C + 9F)) <= 15` hoặc ≤10% tùy trường hợp;
   - không dùng hàng `calories ≈ 4 × macro` kiểu kJ bị gắn nhãn kcal.
3. `sodium_mg > 0` vì production filter đang dùng điều kiện này.
4. Không dùng hàng “with salt” nếu có bản không mặn vẫn hợp lệ; nếu chỉ dùng bản with salt thì ghi rõ.
5. Không dùng hàng bị trùng lặp vô nghĩa (ví dụ 3 bản gạo trắng raw thay chỗ cho nhau). Giữ một bản cooked tương đương, bỏ các bản raw khỏi user-facing.

Ví dụ candidate đã sơ bộ kiểm tra:

| Nguyên liệu thô hiện có | Candidate cooked | Ghi chú |
|---|---|---|
| `Gạo lứt` / `Gạo nếp cái` / `Gạo tẻ giã` | `USDA_169704` — Rice, brown, long-grain, cooked | hoặc `USDA_168878` — Rice, white, long-grain, enriched, cooked |
| `Kê` | `USDA_168871` — Millet, cooked | 119 kcal |
| `Khoai tây` | `USDA_170440` — Potatoes, boiled, without skin, without salt | 86 kcal |
| `Khoai lang` | `USDA_169307` — Sweet potato, frozen, baked, without salt | 100 kcal |
| `Đậu xanh` / `Đậu tương` / `Đậu hà lan` | chỉ dùng hàng cooked có calories khớp macro | tránh hàng “without salt” bị kJ |

Nếu không tìm được candidate đáng tin: **loại khỏi user-facing**, không cố giữ.

## Bước 3 — Sửa overlay, không sửa source data

- Sửa/phủ `data/vn_food_display.json` hoặc overlay mới.
- Không chỉnh tay `data/processed/*.csv`.
- Không thêm raw staples mới vào user-facing list.
- Không giữ đồng thời raw và cooked của cùng một món nếu làm pool bị lẫn (raw vẫn xuất hiện).

## Bước 4 — Cập nhật presentation cho khớp dữ liệu mới

Sau khi thay sang cooked equivalents:

- `Gạo lứt` raw không nên còn là output người dùng.
- Nếu output là `Cơm gạo lứt`, nutrient phải là của `Rice, brown, ..., cooked`, không phải `Gạo lứt raw`.
- `ingredient_basis` phải nói đúng: `món nấu chín` / `cơm từ gạo` / tên gốc dữ liệu cooked, không nói `gạo khô` cho item cooked.
- Nếu là món raw ăn trực tiếp (trái cây, sữa), ghi `ingredient_basis` phù hợp: `quả tươi`, `sữa`, `protein sẵn sàng ăn`, v.v.

## Bước 5 — Test bắt buộc

Thêm/sửa test:

- Không có approved item nào thuộc `RAW_INGREDIENT` theo `classify_dish_role`.
- Mọi replacement đều pass Atwater check cơ bản.
- Pools theo role vẫn ≥ `MIN_ROLE_POOL_SIZE = 3`; meal pools ≥ `MIN_MEAL_POOL_SIZE = 20`.
- `get_food_map()` không trả về món bị chặn.
- Output API không còn nguyên liệu thô như “Gạo lứt”, “Kê”, “Khoai tây” khi chúng chưa nấu.

## Bước 6 — Verification

Chạy:

```bash
python -m pytest -q
python scripts/demo_week8.py --data-path data/processed/merged_food_nutrition.csv --outer-iter 5 --outer-agents 6 --inner-iter 5 --inner-agents 6 --seed 42
python scripts/auditor_grill_live_web.py --base-url http://127.0.0.1:8010 --profiles 30 --hypertension-web 10 --min-seconds 0 --max-seconds 900 --out experiments/c3_cooked_whitelist
python scripts/check_audit_report.py experiments/c3_cooked_whitelist
```

Báo cáo sau audit phải có tối thiểu:

- số request, số menu, số thực đơn vi phạm;
- bao nhiêu món approved bị loại/thay;
- bao nhiêu menu còn nguyên liệu bị auditor xem là raw;
- hạn chế còn lại của dữ liệu món Việt Nam nấu chín.

## Acceptance criteria C3

- Không còn candidate raw-only trong user-facing whitelist.
- `raw_display`/`no_prep` trong audit mới = 0.
- `C19` giảm thật sự vì raw bases đã được loại/thay; ghi số cụ thể.
- Báo cáo ghi rõ: “phạm vi whitelist người dùng, không phải toàn bộ kho 15.929/13.709 món”.
- Không claim “công thức nấu ăn định lượng” hoặc “an toàn tuyệt đối”.

## Không được làm

- Không chuyển sang chỉ dùng USDA tiếng Anh mà bỏ hết món Việt Nam, trừ khi được Duy duyệt.
- Không dùng món chưa có nutrient cooked để “làm cho đủ món”.
- Không sửa số liệu trong PDF/report để ép khớp.
- Không mở rộng sang “tất cả dữ liệu nguồn” trong task này.

---

# TASK C4 — Đăng: “Vai trò món và cơ cấu bữa không bị chê hàng loạt”

## Phạm vi

- `src/models/dish_category.py`: `classify_dish_role`, patterns, RAW/junk rules.
- `src/models/food_selector.py`: `_roles_for_slot`, `build_meal_pools`, `decode_food_selection`.
- `src/models/dish_presentation.py`: nếu đổi tên món thì role phải khớp.
- `tests/`: bổ sung test cho role/slot.
- `scripts/auditor_grill_live_web.py`: chỉ chỉnh nếu rule auditor rõ sai; không sửa auditor để “đẹp số”.

## Bước 1 — Sửa các role rõ sai

Các trường hợp tối thiểu phải xử lý:

- `Đậu hà lan` không được bị xếp là `FRUIT_SNACK` chỉ vì có chữ “hạt”.
- Các đậu/legume nấu chín không được vừa là staple tùy tiện vừa là snack tùy tiện.
- `Mãng cầu xiêm`, các trái cây lạ: nếu là trái cây sẵn sàng ăn thì `FRUIT_SNACK`, không phải unknown/raw.
- Các tên có `luộc/hấp/xào/canh/nấu/cháo` phải được nhận là món chế biến, không phải nguyên liệu thô.

Thêm unit tests cho tối thiểu các tên:

```text
Cơm gạo lứt
Cơm kê
Cơm tẻ trắng
Đậu hà lan luộc
Đậu đậu nành/đậu tương hấp
Đậu xanh luộc
Khoai tây luộc
Khoai lang luộc
Sữa bò tươi
Sữa đậu nành
Trứng vịt lộn luộc
Rau muống luộc
Măng tre luộc
Mãng cầu xiêm
```

## Bước 2 — Siết slot policy cho web menu 2–2–2–1

Mục tiêu: output phải “trông như bữa ăn”, không phải nguyên liệu:

- `breakfast_0`: `STAPLE`
- `breakfast_1`: `MAIN_PROTEIN` (hoặc `VEGETABLE` nếu team quyết định, nhưng không cho fruit/snack nếu mục tiêu là bữa chính)
- `lunch_0`, `dinner_0`: `STAPLE`
- lunch/dinner slots khác: `MAIN_PROTEIN`, `VEGETABLE`, hoặc `SOUP`; không cho `FRUIT_SNACK`/`BEVERAGE`.
- `snack_0`: `FRUIT_SNACK` hoặc `BEVERAGE`.
- Không slot nào được chọn `RAW_INGREDIENT`.

Nếu policy này làm role pool < `MIN_ROLE_POOL_SIZE = 3`, **không hạ ngưỡng**; phải quay lại C3 để bổ sung/loại món phù hợp, hoặc báo blocker cho Duy.

## Bước 3 — Không fallback im lặng

Giữ nguyên nguyên tắc:

- Pool bữa quá nhỏ → lỗi rõ.
- Role pool quá nhỏ → lỗi rõ.
- Không có món chưa dùng trong ngày cho slot → lỗi rõ.
- Swap vi phạm điều kiện thì HTTP 400, không 500.

## Bước 4 — Chạy audit và đối chiếu

Chạy lại:

```bash
python -m pytest -q
python scripts/demo_week8.py --data-path data/processed/merged_food_nutrition.csv --outer-iter 5 --outer-agents 6 --inner-iter 5 --inner-agents 6 --seed 42
python scripts/auditor_grill_live_web.py --base-url http://127.0.0.1:8010 --profiles 30 --hypertension-web 10 --min-seconds 0 --max-seconds 900 --out experiments/c4_role_slot_check
python scripts/check_audit_report.py experiments/c4_role_slot_check
```

Nếu C3 đã merge trước, dùng output sau merge. Nếu chưa, ghi rõ audit chạy trên branch C4 độc lập.

## Acceptance criteria C4

- `structure_fail_menus = 0`.
- `slot0_staple_pct = 100%`.
- `duplicate_menus = 0`.
- Số slot bị independent auditor xếp sai vai trò giảm tối đa, mục tiêu ≤ 2/133; nếu không đạt thì liệt kê từng case và giải thích theo định nghĩa production, không sửa auditor để giấu lỗi.
- Không có approved raw/industrial item trong output.
- Pool vẫn đạt threshold; không fallback.

## Không được làm

- Không đổi `DishRole` enum toàn cục nếu không thật sự cần; ưu tiên sửa pattern/slot policy/tests.
- Không nới `MIN_ROLE_POOL_SIZE` hoặc `MIN_MEAL_POOL_SIZE` cho vừa.
- Không thêm món chưa kiểm tra Atwater chỉ để đủ pool.
- Không “sửa” auditor để output đẹp hơn mà không đối chiếu production rule.

---

# Thứ tự và tích hợp

1. Cương làm C3 trên branch `fix/c3-cooked-whitelist` từ `fix/c4-c6-takeover`.
2. Đăng làm C4 trên branch `fix/c4-role-slot-hardening` từ `fix/c4-c6-takeover`; nếu C3 merge trước thì rebase, tránh conflict ở `dish_category.py`/whitelist.
3. Duy review vòng 1: test + demo + audit tối thiểu.
4. Sau khi cả hai merge vào `fix/c4-c6-takeover` hoặc nhánh final, chạy lại một audit chung.
5. Chỉ sau đó mới cập nhật báo cáo:
   - Chương 5: số C3/C4 mới;
   - Kết luận: giới hạn dữ liệu đúng phạm vi;
   - phụ lục lệnh tái lập;
   - DOCX/PDF/Turnitin/zip.

# Ước lượng

- C3: 4–8 giờ, chưa tính nếu dữ liệu thay thế bị thiếu/kJ.
- C4: 1–3 giờ nếu rule hiện tại chỉ sai vài điểm; lâu hơn nếu phải bổ sung món cooked để đủ role pool.

Rủi ro lớn nhất: “push để đủ món” làm hỏng tính nhất quán dữ liệu. Ưu tiên ít món nhưng sạch hơn nhiều món mà không truy vết được.

# Kết quả cần nộp cho Duy

Mỗi người nộp:

1. Branch + commit hash.
2. `git diff --stat`.
3. `pytest -q` output.
4. Demo P1 output (ghi rõ data-path).
5. Thư mục audit mới + link nội bộ.
6. Bảng trước/sau: C19/C19b/C20, C17/C18, duplicate, slot0_staple_pct.
7. Danh sách các món bị loại khỏi whitelist và lý do.
8. Câu giới hạn dữ liệu đề xuất cho báo cáo.
