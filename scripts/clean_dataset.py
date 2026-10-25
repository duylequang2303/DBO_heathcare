#!/usr/bin/env python3
"""Dataset Cleaning & Validation Pipeline for DBO Healthcare.

Reproducible Phase 1 data cleaning script addressing committee feedback:
1. Eliminates physiological outliers (e.g. sodium > 3,000 mg/100g, calories > 900 kcal/100g).
2. Enforces conservation of mass (protein, carbs, fat each <= 100g per 100g; sum <= 105g; non-negative).
3. Removes unpalatable/raw meats & organs (raw poultry/game/quail/chicken/beef/pork/organs, flours, leavening agents).
4. Preserves healthy raw produce (apples, bananas, raw salad greens).
5. Excludes standalone condiments/seasonings/bases from candidate meal pool (salt, fish sauce, soy sauce, broth bases).
6. Generates a comprehensive markdown report documenting provenance, drop funnels, and before/after statistics.

Usage:
    python scripts/clean_dataset.py
    python scripts/clean_dataset.py --input data/processed/merged_food_nutrition.csv --output data/processed/cleaned_food_nutrition.csv --report data/processed/cleaning_report.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Paths
ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT_DIR / "data" / "processed" / "merged_food_nutrition.csv"
DEFAULT_OUTPUT = ROOT_DIR / "data" / "processed" / "cleaned_food_nutrition.csv"
DEFAULT_REPORT = ROOT_DIR / "data" / "processed" / "cleaning_report.md"

CORE_NUTRIENTS = [
    "calories", "protein_g", "carbs_g", "fat_g", "fiber_g",
    "sodium_mg", "calcium_mg", "iron_mg", "vitamin_c_mg",
]

# Physical thresholds per 100g for meal items
MAX_CALORIES_PER_100G = 900.0  # Theoretical limit (pure lipid ~ 900 kcal)
MIN_CALORIES_PER_100G = 0.0
MAX_SODIUM_PER_100G = 3000.0  # Meals with > 3000 mg/100g are concentrated sauces, salts, or data entry errors
MAX_MACRO_SINGLE_G = 100.0   # Cannot exceed 100g per 100g
MAX_MACRO_SUM_G = 105.0      # Protein + Carbs + Fat sum cannot exceed 105g (with margin for dry isolate measurement)

# Category exclusions (non-food, wild game organs, raw industrial additives)
EXCLUDED_CATEGORIES = {
    "American Indian/Alaska Native Foods",  # Beluga whale, owl flesh, walrus liver, caribou eye
    "Gia vị, nước chấm",                   # Standalone condiments (muối, nước mắm, xì dầu)
}

# Animals / animal proteins that must never be consumed raw
ANIMAL_TERMS = (
    r"\b(quail|chicken|turkey|duck|poultry|beef|pork|lamb|veal|meat|fish|salmon|"
    r"tuna|seafood|shrimp|crab|clam|oyster|squid|egg|liver|heart|tongue|kidney|"
    r"bison|venison|game|tiết|bò|lợn|heo|gà|vịt|ngan|ngỗng|chim|cút)\b"
)
RAW_TERMS = r"\b(raw|uncooked|unprepared|sống)\b"

# Combined pattern: raw animal meats/organs
RAW_ANIMAL_PATTERN = rf"(?:{RAW_TERMS}.*{ANIMAL_TERMS}|{ANIMAL_TERMS}.*{RAW_TERMS})"
RAW_ANIMAL_REGEX = re.compile(RAW_ANIMAL_PATTERN, re.IGNORECASE)

# Industrial flours, leavening agents, and unpalatable concentrates
INDUSTRIAL_JUNK_PATTERNS = [
    r"\b(flour|shortening|starch|baking powder|baking soda|leavening|yeast extract|industrial)\b",
    r"\b(broth concentrate|soup base|bouillon|flavoring|flavor mix|drink mix|beverage mix)\b",
    r"\b(anchovy paste|tahini|sesame butter)\b",
    r"\b(bột mì|bột gạo|bột năng|bột bắp|bột sắn|bột nở|bột trứng|men nở|phụ gia|tinh bột)\b",
    r"\b(bánh phồng tôm sống)\b",
]
INDUSTRIAL_JUNK_REGEX = re.compile("|".join(INDUSTRIAL_JUNK_PATTERNS), re.IGNORECASE)

# Condiments, seasonings, and table salts
CONDIMENT_PATTERNS = [
    r"\b(salt|muối|soy sauce|nước mắm|xì dầu|fish sauce|seasoning|bouillon|broth base)\b",
    r"\b(mustard|mayonnaise|ketchup|salad dressing|vinegar|giấm|bột canh|hạt nêm|bột ngọt|mì chính)\b",
]
CONDIMENT_REGEX = re.compile("|".join(CONDIMENT_PATTERNS), re.IGNORECASE)


def filter_dataset(
    df: pd.DataFrame,
    max_sodium: float = MAX_SODIUM_PER_100G,
    max_calories: float = MAX_CALORIES_PER_100G,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Apply strict multi-stage filtering to clean raw merged dataset.

    Returns:
        Tuple of (cleaned_df, dropped_dict_by_reason)
    """
    dropped: Dict[str, pd.DataFrame] = {}
    current_df = df.copy()

    # Clamp negative nutrient measurements (e.g. -0.1g instrumental drift) to 0.0
    for col in CORE_NUTRIENTS:
        if col in current_df.columns:
            current_df[col] = current_df[col].apply(lambda v: 0.0 if (pd.notna(v) and v < 0) else v)

    # 1. Sodium Outliers (> max_sodium mg / 100g)
    mask_sodium = current_df["sodium_mg"] > max_sodium
    dropped["1_sodium_outliers"] = current_df[mask_sodium]
    current_df = current_df[~mask_sodium]

    # 2. Calorie Outliers (> max_calories kcal / 100g or negative)
    mask_calories = (current_df["calories"] > max_calories) | (current_df["calories"] < MIN_CALORIES_PER_100G)
    dropped["2_calorie_outliers"] = current_df[mask_calories]
    current_df = current_df[~mask_calories]

    # 3. Mass Conservation Violations
    # - Any single macro > 100g / 100g
    # - Macro sum (protein + carbs + fat) > 105g / 100g
    p = current_df["protein_g"].fillna(0)
    c = current_df["carbs_g"].fillna(0)
    f = current_df["fat_g"].fillna(0)
    mask_mass = (
        (current_df["protein_g"] > MAX_MACRO_SINGLE_G) |
        (current_df["carbs_g"] > MAX_MACRO_SINGLE_G) |
        (current_df["fat_g"] > MAX_MACRO_SINGLE_G) |
        ((p + c + f) > MAX_MACRO_SUM_G)
    )
    dropped["3_mass_conservation_violations"] = current_df[mask_mass]
    current_df = current_df[~mask_mass]

    # 4. Missing all core macronutrients
    mask_macros = (
        current_df["protein_g"].isna() &
        current_df["carbs_g"].isna() &
        current_df["fat_g"].isna()
    )
    dropped["4_missing_all_macros"] = current_df[mask_macros]
    current_df = current_df[~mask_macros]

    # 5. Excluded Categories (Alaska Native wildlife, Gia vị nước chấm)
    mask_cats = current_df["category"].isin(EXCLUDED_CATEGORIES)
    dropped["5_excluded_categories"] = current_df[mask_cats]
    current_df = current_df[~mask_cats]

    # 6. Raw Meats, Poultry, Seafood, Game & Animal Organs (e.g. Quail meat raw)
    names = current_df["food_name"].fillna("").astype(str)
    mask_raw_animal = names.apply(lambda s: bool(RAW_ANIMAL_REGEX.search(s)))
    dropped["6_raw_animal_meats"] = current_df[mask_raw_animal]
    current_df = current_df[~mask_raw_animal]

    # 7. Industrial Flours, Leavening, and Unpalatable Concentrates
    names_rem = current_df["food_name"].fillna("").astype(str)
    mask_industrial = names_rem.apply(lambda s: bool(INDUSTRIAL_JUNK_REGEX.search(s)))
    dropped["7_industrial_powders"] = current_df[mask_industrial]
    current_df = current_df[~mask_industrial]

    # 8. Remaining Standalone Condiments/Seasonings
    names_rem2 = current_df["food_name"].fillna("").astype(str)
    mask_cond = names_rem2.apply(lambda s: bool(CONDIMENT_REGEX.search(s)))
    dropped["8_condiments_seasonings"] = current_df[mask_cond]
    current_df = current_df[~mask_cond]

    # Cleaned output
    cleaned_df = current_df.reset_index(drop=True)
    return cleaned_df, dropped


def generate_markdown_report(
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    dropped: Dict[str, pd.DataFrame],
    max_sodium: float,
    max_calories: float,
) -> str:
    """Generate detailed markdown report documenting the cleaning process."""
    total_raw = len(raw_df)
    total_clean = len(clean_df)
    total_dropped = total_raw - total_clean
    pct_dropped = (total_dropped / total_raw) * 100.0

    lines: List[str] = [
        "# Báo Cáo Quy Trình Làm Sạch và Chuẩn Hóa Dữ Liệu Thực Phẩm (Phase 1)",
        "",
        "> **Mục tiêu**: Loại bỏ triệt để các mục dữ liệu phi thực tế, ngoại lai (outliers), ",
        "> vi phạm định luật bảo toàn khối lượng, thịt sống chưa chế biến và gia vị đóng hộp khỏi tập đề xuất.",
        "",
        "## 1. Tổng Quan Quy Trình Lọc (Filter Funnel)",
        "",
        f"- **Tổng số thực phẩm ban đầu**: `{total_raw:,}` món (USDA: `{len(raw_df[raw_df['source'] == 'usda']):,}`, VN: `{len(raw_df[raw_df['source'] == 'vietnamese']):,}`)",
        f"- **Tổng số thực phẩm bị loại**: `{total_dropped:,}` món (`{pct_dropped:.1f}%`)",
        f"- **Số thực phẩm sạch sau chuẩn hóa**: `{total_clean:,}` món (USDA: `{len(clean_df[clean_df['source'] == 'usda']):,}`, VN: `{len(clean_df[clean_df['source'] == 'vietnamese']):,}`)",
        "",
        "| Bước lọc | Lý do loại bỏ | Ngưỡng / Tiêu chí | Số lượng loại | Ví dụ điển hình |",
        "|---|---|---|---|---|",
    ]

    reason_descs = {
        "1_sodium_outliers": (
            "Natri phi vật lý / lỗi đơn vị nhập liệu",
            f"sodium_mg > {max_sodium:.0f} mg/100g",
            "ANCHOVIES IN OLIVE OIL (4.690.000 mg), BASTONCINI (1.000.000 mg)",
        ),
        "2_calorie_outliers": (
            "Calo vượt giới hạn vật lý per 100g",
            f"calories > {max_calories:.0f} kcal hoặc < 0",
            "Món calo > 900 (vượt trần lipid thuần)",
        ),
        "3_mass_conservation_violations": (
            "Vi phạm bảo toàn khối lượng",
            "Macro riêng lẻ > 100g hoặc Tổng Protein+Carbs+Fat > 105g/100g",
            "Noodles ghi nhận Protein 131g/100g, Bánh ghi nhận Carbs 250g/100g",
        ),
        "4_missing_all_macros": (
            "Thiếu toàn bộ macronutrients",
            "Protein, Carbs, Fat đồng thời NaN",
            "Các mục chỉ ghi calo mà không có thành phần đa lượng",
        ),
        "5_excluded_categories": (
            "Nhóm thực phẩm không phù hợp",
            "American Indian/Alaska Native Foods & Gia vị",
            "Thịt cú sống, mắt tuần lộc, gan hải mã, nước mắm cá",
        ),
        "6_raw_animal_meats": (
            "Thịt động vật / gia cầm sống",
            "Regex (raw meat/poultry/game/quail/seafood/organs)",
            "Quail meat raw (chim cút sống), Chicken breast raw, Tiết lợn sống",
        ),
        "7_industrial_powders": (
            "Bột công nghiệp / men nở / hỗn hợp pha",
            "Regex (flour, starch, baking powder, tahini, drink mix)",
            "Bột mì đa dụng, A NON-ALCOHOLIC DRINK MIX (160g), Tahini bơ mè",
        ),
        "8_condiments_seasonings": (
            "Gia vị / nước chấm / hạt nêm",
            "Regex (salt/muối, soy sauce, bouillon, broth base)",
            "Muối ăn, bột canh, nước hầm cô đặc, xì dầu",
        ),
    }

    for step_key, (name, criteria, ex) in reason_descs.items():
        count = len(dropped.get(step_key, pd.DataFrame()))
        step_num = step_key.split("_")[0]
        lines.append(f"| {step_num} | {name} | `{criteria}` | **{count:,}** | {ex} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Giải Trình Trực Tiếp 3 Nhận Xét Của Hội Đồng",
        "",
        "### 2.1. Vấn đề 1: Vi phạm Natri (Ngày 1: 343%, Ngày 6: 260%)",
        "- **Bằng chứng gốc**: Trong dataset cũ, tồn tại các mục lỗi đơn vị nghiêm trọng:",
        "  - `USDA_704`: ANCHOVIES IN OLIVE OIL ghi nhận **4.690.000 mg/100g** (sai số 1.000 lần so với thực tế).",
        "  - `USDA_272`: BASTONCINI ghi nhận **1.000.000 mg/100g**.",
        "  - `USDA_13413`: ARGENTINIAN BRAND SAUSAGE ghi nhận **678.000 mg/100g**.",
        "  - `USDA_3580`: BBQ PORK RIBS ghi nhận **179.000 mg/100g**.",
        "- **Hành động khắc phục**: Thiết lập trần natri tối đa `3.000 mg/100g` cho toàn bộ candidate pool. "
        "Mọi mục gia vị cô đặc, muối thô và lỗi nhập liệu đều bị loại bỏ trước khi chuyển cho thuật toán DBO/IDBO.",
        "",
        "### 2.2. Vấn đề 2: Đề xuất món ăn phi thực tế (Chim cút sống, Đùi gà 25g, Tahini 85g, Pha đồ uống 160g)",
        "- **Thịt chim cút sống (`Quail, breast, meat only, raw`)**: Xuất phát từ mã `USDA_172829`. "
        "Bộ lọc Phase 1 đã bổ sung quy tắc regex chặn toàn bộ thịt/gia cầm có nhãn `raw`, `uncooked`, `sống`.",
        "- **Bột pha đồ uống 160g (`A NON-ALCOHOLIC DRINK MIX`)**: Xuất phát từ mã `USDA_1916338`. "
        "Bộ lọc đã chặn từ khóa `drink mix`, `flavoring`, `powder` dạng công nghiệp.",
        "- **Tahini 85g**: Xuất phát từ nhóm bơ hạt cô đặc (`Seeds, sesame butter, tahini`). "
        "Đã loại bỏ khỏi vai trò snack bữa phụ độc lập.",
        "- **Đùi gà 25g**: Được xử lý bằng cách đồng bộ hóa ràng buộc `PORTION_RANGE` trong `constraints.py` "
        "với `ROLE_PORTION_BOUNDS` trong `dish_category.py` (Main Protein tối thiểu 60g, không còn tình trạng 25g).",
        "",
        "### 2.3. Vấn đề 3: Minh chứng quy trình chuẩn hóa và xử lý dữ liệu",
        "- Toàn bộ quy trình được tự động hóa qua script độc lập `scripts/clean_dataset.py`.",
        "- Bảng so sánh chất lượng dữ liệu trước và sau làm sạch:",
        "",
        "| Chỉ số dinh dưỡng | Trước làm sạch (Min - Max) | Sau làm sạch (Min - Max) | Trạng thái |",
        "|---|---|---|---|",
    ])

    nut_specs = [
        ("Năng lượng (kcal/100g)", "calories"),
        ("Đạm (g/100g)", "protein_g"),
        ("Tinh bột (g/100g)", "carbs_g"),
        ("Chất béo (g/100g)", "fat_g"),
        ("Chất xơ (g/100g)", "fiber_g"),
        ("Natri (mg/100g)", "sodium_mg"),
    ]

    for label, col in nut_specs:
        b_min = raw_df[col].min()
        b_max = raw_df[col].max()
        c_min = clean_df[col].min()
        c_max = clean_df[col].max()
        lines.append(f"| {label} | {b_min:.1f} - {b_max:,.1f} | **{c_min:.1f} - {c_max:,.1f}** | Chuẩn hóa hoàn tất |")

    lines.extend([
        "",
        "## 3. Danh Sách Mẫu Top 10 Ngoại Lai Natri Bị Loại Bỏ",
        "",
        "| STT | Food ID | Tên thực phẩm | Natri (mg/100g) | Nguồn | Phân tích lỗi |",
        "|---|---|---|---|---|---|",
    ])

    top_sodium_dropped = dropped.get("1_sodium_outliers", pd.DataFrame())
    if not top_sodium_dropped.empty:
        top10 = top_sodium_dropped.sort_values("sodium_mg", ascending=False).head(10)
        for idx, (_, r) in enumerate(top10.iterrows(), start=1):
            na_val = r["sodium_mg"]
            f_name = str(r["food_name"]).replace('"', '')
            f_id = r["food_id"]
            src = r["source"]
            lines.append(f"| {idx} | `{f_id}` | {f_name} | **{na_val:,.0f}** | {src} | Sai đơn vị / gia vị cô đặc |")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean and validate food nutrition dataset.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to input merged CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to output cleaned CSV")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Path to markdown report")
    parser.add_argument("--max-sodium", type=float, default=MAX_SODIUM_PER_100G, help="Max sodium mg/100g")
    parser.add_argument("--max-calories", type=float, default=MAX_CALORIES_PER_100G, help="Max calories kcal/100g")

    args = parser.parse_args()

    if not args.input.exists():
        print(f"[ERROR] Input file does not exist: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading raw dataset from {args.input}...")
    raw_df = pd.read_csv(args.input)
    print(f"Loaded {len(raw_df)} items.")

    print("Executing Phase 1 cleaning rules...")
    clean_df, dropped = filter_dataset(
        raw_df,
        max_sodium=args.max_sodium,
        max_calories=args.max_calories,
    )

    print(f"Cleaning complete. Output rows: {len(clean_df)} (Dropped {len(raw_df) - len(clean_df)})")

    # Ensure parent directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"Saved cleaned CSV to: {args.output}")

    # Generate Report
    report_content = generate_markdown_report(
        raw_df,
        clean_df,
        dropped,
        args.max_sodium,
        args.max_calories,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report_content, encoding="utf-8")
    print(f"Saved markdown report to: {args.report}")


if __name__ == "__main__":
    main()
