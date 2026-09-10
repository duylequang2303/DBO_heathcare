# `src/models/user_profile.py`

## Mục đích

Định nghĩa hồ sơ người dùng (UserProfile) và các enum liên quan: giới tính, mức vận động, mục tiêu, chế độ ăn.

## Các thành phần chính

### Enum

| Enum | Giá trị | Mô tả |
| :--- | :--- | :--- |
| `Gender` | `MALE`, `FEMALE` | Giới tính sinh học |
| `ActivityLevel` | `SEDENTARY` (1.2), `LIGHT` (1.375), `MODERATE` (1.55), `ACTIVE` (1.725), `VERY_ACTIVE` (1.9) | Hệ số TDEE |
| `Goal` | `LOSE_WEIGHT`, `MAINTAIN`, `GAIN_WEIGHT` | Mục tiêu dinh dưỡng |
| `DietType` | `STANDARD`, `VEGETARIAN`, `VEGAN`, `KETO` | Loại chế độ ăn |

### `UserProfile` (dataclass)

| Trường | Kiểu | Mô tả |
| :--- | :--- | :--- |
| `name` | `str` | Tên người dùng |
| `age` | `int` | Tuổi |
| `gender` | `Gender` | Giới tính |
| `height_cm` | `float` | Chiều cao (cm) |
| `weight_kg` | `float` | Cân nặng (kg) |
| `activity_level` | `ActivityLevel` | Mức vận động |
| `goal` | `Goal` | Mục tiêu (mặc định `MAINTAIN`) |
| `allergies` | `list[str]` | Danh sách dị ứng |
| `dislikes` | `list[str]` | Danh sách món không thích |
| `likes` | `list[str]` | Danh sách món thích |
| `meal_counts` | `dict[str, int]` | Số món mỗi bữa (mặc định 1 món/bữa) |
| `medical_conditions` | `list[str]` | Tình trạng bệnh lý |
| `diet_type` | `DietType` | Chế độ ăn (mặc định `STANDARD`) |

### Ghi chú

- Constructor hỗ trợ positional args theo thứ tự cố định để tương thích ngược.
- Các trường sau `meal_counts` (`medical_conditions`, `diet_type`) được thêm sau để giữ nguyên thứ tự vị trí.

## Kiểm thử (`tests/test_nutrition.py`)

22 bài unit test bao phủ:
- Constructor mặc định và custom (`DietType`, `medical_conditions`)
- Thứ tự positional args không bị ảnh hưởng bởi trường mới
- BMR nam/nữ đúng giá trị chuẩn Mifflin-St Jeor
- TDEE theo hệ số vận động
- Calorie target theo goal (lose/maintain/gain)
- Macro distribution đúng tỷ lệ
- Fiber target đúng giới tính (nam 38g, nữ 25g)
- Micro targets theo DRI: sodium, calcium, iron, vitamin C theo tuổi/giới
- `daily_all_targets()` trả đủ 9 chỉ số
