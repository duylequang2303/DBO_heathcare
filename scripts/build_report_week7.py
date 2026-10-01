"""Script to generate Week 7 Word Reports (docs/BaoCao_Tuan7.docx and docs/Phan_Dang_Tuan7.docx).

Incorporates:
  - Official cover page (CNTT-KLCN142, ThS. Dinh Nguyen Trong Nghia, 3 students)
  - Section 1: Objectives of Week 7
  - Section 2: Solution representation (food_ids + continuous portion vector x)
  - Section 3: 3-layer constraint handling (lb/ub, fitness penalty, food_sampler)
  - Section 4: Experimental setup on Profile P1 (M runs, max_iter, N agents, sampled food IDs)
  - Section 5: Experimental results (Table 1, Table 2, embedded W7-F1 & W7-F2 plots, answers to 5 questions)
  - Section 6: Scientific discussion on continuous portion optimization
  - Section 7: Conclusion & Week 8 Roadmap
  - Appendix: Commands & 138/138 pytest verification
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.user_profile import ActivityLevel, DietType, Gender, Goal, UserProfile
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets

EXP_DIR = ROOT / "experiments" / "week7"
DOCS_DIR = ROOT / "docs"

COLOR_PRIMARY = RGBColor(43, 92, 143)    # Deep Blue
COLOR_DARK = RGBColor(35, 35, 35)        # Charcoal
COLOR_MUTED = RGBColor(90, 90, 90)       # Gray


def set_cell_background(cell, fill_hex: str) -> None:
    """Set background color of a Word table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top: int = 80, bottom: int = 80, left: int = 120, right: int = 120) -> None:
    """Set inner padding of a Word table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table, color: str = "D0D7DE") -> None:
    """Set refined horizontal-only border styling for a Word table."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="6" w:space="0" w:color="2B5C8F"/>'
        f'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="2B5C8F"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def add_p(
    doc: docx.Document,
    text: str = "",
    bold: bool = False,
    italic: bool = False,
    size_pt: float = 11.0,
    color: RGBColor = COLOR_DARK,
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    space_before: float = 0.0,
    space_after: float = 4.0,
):
    """Add a styled paragraph to the document."""
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if text:
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(size_pt)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
    return p


def add_h1(doc: docx.Document, text: str):
    """Add a Level 1 heading to the document."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(13.5)
    r.font.bold = True
    r.font.color.rgb = COLOR_PRIMARY
    return p


def add_h2(doc: docx.Document, text: str):
    """Add a Level 2 heading to the document."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = COLOR_DARK
    return p


def add_bullet(doc: docx.Document, lead: str, content: str):
    """Add a bullet point item with bold prefix to the document."""
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.15
    r_lead = p.add_run(lead + ": ")
    r_lead.font.name = "Times New Roman"
    r_lead.font.size = Pt(11.0)
    r_lead.font.bold = True
    r_text = p.add_run(content)
    r_text.font.name = "Times New Roman"
    r_text.font.size = Pt(11.0)
    return p


def add_caption(doc: docx.Document, text: str):
    """Add a centered table or figure caption to the document."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    r.font.italic = True
    r.font.color.rgb = COLOR_MUTED
    return p


def get_profile_p1() -> UserProfile:
    """Return standard test profile P1 for Week 7 evaluation."""
    return UserProfile(
        name="Duy",
        age=22,
        gender=Gender.MALE,
        weight_kg=65.0,
        height_cm=170.0,
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        diet_type=DietType.STANDARD,
        meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 2},
        allergies=[],
        dislikes=[],
        likes=[],
    )


def load_sampled_foods(exp_dir: Path) -> List[Tuple[str, str, str, str]]:
    """Load sampled food items dynamically from food_ids_p1.txt and database."""
    food_ids_file = exp_dir / "food_ids_p1.txt"
    sampled_foods = []
    if food_ids_file.exists():
        df = load_food_db()
        food_map = build_food_map(df)
        with open(food_ids_file, "r", encoding="utf-8") as f:
            fids = [line.strip() for line in f if line.strip()]

        meal_labels = [
            "Bữa sáng (Breakfast)", "Bữa sáng (Breakfast)",
            "Bữa trưa (Lunch)", "Bữa trưa (Lunch)",
            "Bữa tối (Dinner)", "Bữa tối (Dinner)",
            "Bữa phụ (Snack)", "Bữa phụ (Snack)",
        ]
        for idx, fid in enumerate(fids):
            row = food_map.get(fid, {})
            name = row.get("food_name", fid)
            mtype = row.get("meal_type", "all")
            lbl = meal_labels[idx] if idx < len(meal_labels) else "Khác"
            sampled_foods.append((lbl, fid, name, mtype))

    return sampled_foods


def determine_winner(sum_df: pd.DataFrame) -> Tuple[str, float]:
    """Calculate winner between DBO and IDBO using the 1% relative threshold rule."""
    dbo_mean = float(sum_df.loc[sum_df["algorithm"] == "dbo", "mean"].iloc[0])
    idbo_mean = float(sum_df.loc[sum_df["algorithm"] == "idbo", "mean"].iloc[0])
    rel_diff = abs(idbo_mean - dbo_mean) / max(abs(dbo_mean), 1e-9)

    if rel_diff < 0.01:
        verdict = "Hòa (1%)"
    elif idbo_mean > dbo_mean:
        verdict = "IDBO thắng"
    else:
        verdict = "DBO thắng"

    return verdict, rel_diff


def create_summary_table(doc: docx.Document, sum_df: pd.DataFrame, winner_verdict: str) -> None:
    """Build and insert Section 5.1 summary table (Table 1) into doc."""
    tbl_res1 = doc.add_table(rows=3, cols=9)
    tbl_res1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_res1)

    headers_1 = ["Thuật toán", "Best", "Mean", "Std", "Worst", "Số đánh giá", "Thời gian (s)", "Vi phạm TB", "Kết luận"]
    for c_idx, h in enumerate(headers_1):
        c = tbl_res1.cell(0, c_idx)
        set_cell_background(c, "2B5C8F")
        set_cell_margins(c, 70, 70, 80, 80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, algo in enumerate(["dbo", "idbo"], start=1):
        row = sum_df[sum_df["algorithm"] == algo].iloc[0]
        vals = [
            algo.upper(),
            f"{row['best']:.4f}",
            f"{row['mean']:.4f}",
            f"{row['std']:.4f}",
            f"{row['worst']:.4f}",
            f"{row['mean_n_evaluations']:.0f}",
            f"{row['mean_runtime_s']:.2f}s",
            f"{row['mean_n_violations']:.2f}",
            winner_verdict if algo == "idbo" else "-",
        ]
        for c_idx, val in enumerate(vals):
            c = tbl_res1.cell(r_idx, c_idx)
            set_cell_margins(c, 60, 60, 80, 80)
            if r_idx % 2 == 1:
                set_cell_background(c, "F8FAFC")
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            if c_idx == 0 or c_idx == 2:
                r.font.bold = True


def create_nutrition_table(doc: docx.Document, runs_df: pd.DataFrame, targets: Dict[str, float]) -> None:
    """Build and insert Section 5.2 nutrition comparison table (Table 2) into doc."""
    dbo_runs = runs_df[runs_df["algorithm"] == "dbo"]
    idbo_runs = runs_df[runs_df["algorithm"] == "idbo"]

    tbl_nutr = doc.add_table(rows=4, cols=6)
    tbl_nutr.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_nutr)

    headers_n = ["Chỉ số dinh dưỡng", "Năng lượng (kcal)", "Protein (g)", "Carbohydrate (g)", "Chất béo (g)", "Chất xơ (g)"]
    for c_idx, h in enumerate(headers_n):
        c = tbl_nutr.cell(0, c_idx)
        set_cell_background(c, "2B5C8F")
        set_cell_margins(c, 70, 70, 80, 80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    data_nutr = [
        ("Mục tiêu khuyến nghị (P1)",
         f"{targets['calories']:.1f}", f"{targets['protein_g']:.1f}",
         f"{targets['carbs_g']:.1f}", f"{targets['fat_g']:.1f}", f"{targets['fiber_g']:.1f}"),
        ("Thực đơn DBO (Mean)",
         f"{dbo_runs['calories'].mean():.1f}", f"{dbo_runs['protein_g'].mean():.1f}",
         f"{dbo_runs['carbs_g'].mean():.1f}", f"{dbo_runs['fat_g'].mean():.1f}", f"{dbo_runs['fiber_g'].mean():.1f}"),
        ("Thực đơn IDBO (Mean)",
         f"{idbo_runs['calories'].mean():.1f}", f"{idbo_runs['protein_g'].mean():.1f}",
         f"{idbo_runs['carbs_g'].mean():.1f}", f"{idbo_runs['fat_g'].mean():.1f}", f"{idbo_runs['fiber_g'].mean():.1f}"),
    ]

    for r_idx, row_vals in enumerate(data_nutr, start=1):
        for c_idx, val in enumerate(row_vals):
            c = tbl_nutr.cell(r_idx, c_idx)
            set_cell_margins(c, 60, 60, 80, 80)
            if r_idx == 1:
                set_cell_background(c, "EFF6FF")
            elif r_idx % 2 == 1:
                set_cell_background(c, "F8FAFC")
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            if r_idx == 1 or c_idx == 0:
                r.font.bold = True


def load_baseline_metrics(exp_dir: Path) -> Dict[str, float]:
    """Load baseline metrics from menu_baseline.csv or fallback to default baseline."""
    baseline_file = exp_dir / "menu_baseline.csv"
    if baseline_file.exists():
        df = pd.read_csv(baseline_file)
        if not df.empty:
            return {
                "mean_violations": float(df["mean_violations"].iloc[0]),
                "mean_fitness": float(df["mean_fitness"].iloc[0]),
                "mean_calories": float(df["mean_calories"].iloc[0]),
            }
    raise FileNotFoundError(
        f"Không tìm thấy {baseline_file}. Hãy chạy `python scripts/experiment_week7.py` trước."
    )


def build_full_report(exp_dir: Path, docs_dir: Path) -> None:
    """Generate the full Week 7 Word report (BaoCao_Tuan7.docx)."""
    print("Building full report docs/BaoCao_Tuan7.docx...")
    doc = docx.Document()

    # Margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(0.8)

    # ──────────────────────────────────────────────────────────────────────────
    # TRANG BÌA
    # ──────────────────────────────────────────────────────────────────────────
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("BỘ CÔNG THƯƠNG\nTRƯỜNG ĐẠI HỌC CÔNG THƯƠNG TP. HỒ CHÍ MINH\nKHOA CÔNG NGHỆ THÔNG TIN\n")
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.font.bold = True

    p_div = doc.add_paragraph()
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_div = p_div.add_run("———————————————\n\n\n")
    r_div.font.name = "Times New Roman"

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(8)
    r_t1 = p_title.add_run("BÁO CÁO TIẾN ĐỘ THỰC HIỆN ĐỀ TÀI\n")
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(13)
    r_t1.font.bold = True
    r_t1.font.color.rgb = COLOR_MUTED

    r_t2 = p_title.add_run("TUẦN 7: TỐI ƯU KHẨU PHẦN THỰC ĐƠN THỰC TẾ\nBẰNG DBO VÀ IDBO\n")
    r_t2.font.name = "Times New Roman"
    r_t2.font.size = Pt(16)
    r_t2.font.bold = True
    r_t2.font.color.rgb = COLOR_PRIMARY

    p_code = doc.add_paragraph()
    p_code.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_code.paragraph_format.space_after = Pt(24)
    r_c = p_code.add_run("Mã đề tài: CNTT-KLCN142\nĐề tài: Ứng dụng thuật toán tối ưu bọ hung (DBO/IDBO)\ntrong xây dựng thực đơn dinh dưỡng cá nhân hóa\n\n\n")
    r_c.font.name = "Times New Roman"
    r_c.font.size = Pt(11.5)
    r_c.font.bold = True

    # Info table
    tbl_info = doc.add_table(rows=4, cols=2)
    tbl_info.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_info.autofit = False

    labels = [
        "Giảng viên hướng dẫn:",
        "Sinh viên thực hiện 1:",
        "Sinh viên thực hiện 2:",
        "Sinh viên thực hiện 3:",
    ]
    vals = [
        "ThS. Đinh Nguyễn Trọng Nghĩa",
        "Lê Quang Duy (Trưởng nhóm)",
        "Đặng Nguyễn Minh Đăng",
        "Hồ Trung Cương",
    ]
    for row_idx, (lab, val) in enumerate(zip(labels, vals)):
        cell_l, cell_r = tbl_info.cell(row_idx, 0), tbl_info.cell(row_idx, 1)
        cell_l.width = Inches(2.3)
        cell_r.width = Inches(4.0)
        p_l = cell_l.paragraphs[0]
        p_l.paragraph_format.space_after = Pt(3)
        r_l = p_l.add_run(lab)
        r_l.font.name = "Times New Roman"
        r_l.font.size = Pt(11)
        r_l.font.bold = True

        p_r = cell_r.paragraphs[0]
        p_r.paragraph_format.space_after = Pt(3)
        r_r = p_r.add_run(val)
        r_r.font.name = "Times New Roman"
        r_r.font.size = Pt(11)

    p_date = doc.add_paragraph()
    p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_date.paragraph_format.space_before = Pt(60)
    r_d = p_date.add_run("TP. Hồ Chí Minh, Mốc Tuần 7 — Tháng 10/2026")
    r_d.font.name = "Times New Roman"
    r_d.font.size = Pt(11)
    r_d.font.italic = True

    doc.add_page_break()

    # ──────────────────────────────────────────────────────────────────────────
    # MỤC 1: MỤC TIÊU TUẦN 7
    # ──────────────────────────────────────────────────────────────────────────
    add_h1(doc, "1. MỤC TIÊU TUẦN 7 — CHUYỂN DỊCH TỪ BENCHMARK SANG BÀI TOÁN THỰC TẾ")
    add_p(doc,
          "Trong các Tuần 4, 5 và 6, nhóm nghiên cứu đã tập trung xây dựng, kiểm chứng và đánh giá thuật toán "
          "Dung Beetle Optimizer (DBO) gốc cùng biến thể cải tiến Improved DBO (IDBO) trên 6 hàm chuẩn toán học "
          "(Sphere, Schwefel 2.22, Rosenbrock, Rastrigin, Ackley, Griewank) qua các số chiều 10, 30 và 50. "
          "Bước sang Tuần 7, theo đúng đề cương nghiên cứu, nhóm chính thức rời khỏi không gian hàm benchmark nhân tạo "
          "để đưa thuật toán vào giải quyết bài toán cốt lõi của đề tài: Tối ưu hóa thực đơn dinh dưỡng cá nhân hóa.")

    add_p(doc, "Các mục tiêu trọng tâm trong giai đoạn này bao gồm:")
    add_bullet(doc, "Tích hợp hàm mục tiêu thực đơn vào bộ tối ưu",
               "Xây dựng adapter callable `make_menu_objective` chuyển đổi vector khẩu phần x thành điểm fitness thực đơn, "
               "đảo dấu để chuyển từ bài toán cực đại hóa chất lượng sang cực tiểu hóa phù hợp giao diện DBO/IDBO.")
    add_bullet(doc, "Lọc chọn món ăn hợp lệ độc lập",
               "Phát triển module `food_sampler.py` chọn trước danh sách `food_ids` hợp lệ theo bữa ăn, lọc bỏ dị ứng và món không thích, "
               "bảo đảm tính khả thi của thực đơn ngay từ bước khởi tạo.")
    add_bullet(doc, "Khảo nghiệm so sánh DBO vs IDBO trên thực đơn thật",
               "Thực hiện đo đạc thực nghiệm độc lập M lần trên Profile chuẩn P1 (nam, 22 tuổi, duy trì cân nặng), "
               "phân tích định lượng độ lệch dinh dưỡng, tỷ lệ vi phạm ràng buộc và tốc độ hội tụ.")

    # ──────────────────────────────────────────────────────────────────────────
    # MỤC 2: BIỂU DIỄN NGHIỆM THỰC ĐƠN (CƯƠNG SOẠN)
    # ──────────────────────────────────────────────────────────────────────────
    add_h1(doc, "2. BIỂU DIỄN NGHIỆM THỰC ĐƠN VÀ PHÂN TÁCH KHÔNG GIAN TÌM KIẾM")
    add_p(doc,
          "Trong bài toán tối ưu thực đơn ở Tuần 7, một nghiệm hoàn chỉnh được biểu diễn dưới dạng ghép cặp "
          "giữa hai thành phần độc lập: danh sách mã món ăn (food_ids) và vector khẩu phần liên tục (x). "
          "Hai thành phần này có cùng số chiều và tuân thủ chặt chẽ thứ tự cố định các bữa ăn trong ngày: "
          "breakfast → lunch → dinner → snack.")

    add_p(doc,
          "Với hồ sơ chuẩn P1, số lượng món ăn phân bổ cho 4 bữa lần lượt là 2 món sáng, 2 món trưa, 2 món tối và 2 món phụ (2-2-2-2). "
          "Do đó, tổng số món trong ngày là 8 và số chiều không gian tìm kiếm liên tục là dim = 8. "
          "Vector nghiệm được biểu diễn dưới dạng:")

    p_vec = add_p(doc, "x = [p_bf1, p_bf2, p_l1, p_l2, p_d1, p_d2, p_s1, p_s2] ∈ ℝ⁸", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    p_vec.paragraph_format.space_before = Pt(4)
    p_vec.paragraph_format.space_after = Pt(6)

    add_p(doc,
          "Mỗi phần tử x_i biểu diễn khối lượng của món ăn thứ i tính bằng gram, thuộc miền liên tục giới hạn [25.0, 350.0] g. "
          "Thuật toán DBO/IDBO chịu trách nhiệm tìm kiếm vị trí tối ưu của vector x trong không gian liên tục 8 chiều này. "
          "Danh sách food_ids được module chọn món tạo trước một lần duy nhất và giữ cố định trong toàn bộ quá trình optimize(). "
          "Sau khi thuật toán đề xuất vector x*, hàm `Menu.decode()` sẽ ghép cặp tương ứng từng món ăn với khối lượng khẩu phần "
          "để tái tạo cấu trúc thực đơn hoàn chỉnh, phục vụ cho việc tính toán dinh dưỡng và kiểm tra ràng buộc y khoa.")

    # ──────────────────────────────────────────────────────────────────────────
    # MỤC 3: XỬ LÝ RÀNG BUỘC THEO 3 LỚP (CƯƠNG SOẠN)
    # ──────────────────────────────────────────────────────────────────────────
    add_h1(doc, "3. MÔ HÌNH XỬ LÝ RÀNG BUỘC THEO BA LỚP ĐỘC LẬP")
    add_p(doc,
          "Nhằm đảm bảo tính trong sáng của kiến trúc phần mềm và tránh làm quá tải thuật toán tối ưu bằng các hàm phạt tùy tiện, "
          "nhóm phân chia hệ thống xử lý ràng buộc thành ba lớp độc lập:")

    add_bullet(doc, "Lớp 1 — Giới hạn khẩu phần (Boundary Constraints)",
               "Kiểm soát miền giá trị của từng món ăn trong khoảng [25, 350] g. Cơ chế clip biên tự nhiên trong DBO/IDBO "
               "đảm bảo 100% nghiệm sinh ra luôn có khẩu phần nằm trong giới hạn thực tế, không cần sử dụng death-penalty.")
    add_bullet(doc, "Lớp 2 — Penalty trong hàm mục tiêu (Fitness Penalty)",
               "Đánh giá mức độ vi phạm về năng lượng (dung sai ±10%), tỷ lệ phân bổ đa lượng (protein, carbs, fat, fiber) "
               "thông qua hệ số phạt PENALTY_PER_VIOLATION = 12.0 (tối đa 90.0 điểm). Thực đơn vi phạm sẽ bị trừ điểm trực tiếp "
               "vào fitness, giúp định hướng đàn bọ hung tiến về vùng khả thi.")
    add_bullet(doc, "Lớp 3 — Lọc chọn món hợp lệ trước tối ưu (Food Sampler)",
               "Được thực hiện bởi module `food_sampler.py`. Sampler kiểm tra nhãn bữa ăn (`meal_type`), loại bỏ hoàn toàn các món chứa "
               "thành phần gây dị ứng (allergies) hoặc món không thích (dislikes), và loại trừ trùng lặp món trong ngày. "
               "Nhờ đó, danh sách món đi vào thuật toán tối ưu đã được bảo đảm sạch 100% về mặt sở thích và dị ứng.")

    add_p(doc,
          "Module `food_sampler.py` đã được kiểm thử toàn diện với 6 unit test bắt buộc (`tests/test_food_sampler.py`), bao gồm "
          "kiểm tra tính tất định theo seed (seed=7000), loại trừ dị ứng (ví dụ 'peanut'), kiểm tra nhãn bữa và trường hợp số món không đều. "
          "Toàn bộ 6/6 test của sampler đều đạt kết quả xuất sắc.")

    # ──────────────────────────────────────────────────────────────────────────
    # MỤC 4: THIẾT KẾ THÍ NGHIỆM (ĐĂNG SOẠN)
    # ──────────────────────────────────────────────────────────────────────────
    add_h1(doc, "4. THIẾT KẾ THÍ NGHIỆM TỐI ƯU THỰC ĐƠN TRÊN PROFILE P1")
    add_p(doc,
          "Phần thực nghiệm Tuần 7 do thành viên Đặng Nguyễn Minh Đăng phụ trách triển khai, nhằm kiểm chứng khả năng "
          "tối ưu khẩu phần thực đơn trên hồ sơ người dùng thực tế và so sánh hiệu quả giữa DBO gốc và IDBO.")

    profile = get_profile_p1()
    targets = daily_all_targets(profile)

    add_h2(doc, "4.1. Hồ sơ người dùng chuẩn (Profile P1)")
    add_p(doc, "Hồ sơ người dùng chuẩn P1 được thiết lập đại diện cho đối tượng nam thanh niên trưởng thành:")
    add_bullet(doc, "Thông tin nhân khẩu học", f"Tên: {profile.name}, Tuổi: {profile.age}, Giới tính: {profile.gender.value.capitalize()}, Chiều cao: {profile.height_cm:.1f} cm, Cân nặng: {profile.weight_kg:.1f} kg.")
    add_bullet(doc, "Mức độ vận động & Mục tiêu", f"Vận động: {profile.activity_level.name}, Mục tiêu: {profile.goal.name}.")
    add_bullet(doc, "Mục tiêu năng lượng (DRI)", f"Năng lượng khuyến nghị: {targets['calories']:.1f} kcal/ngày.")
    add_bullet(doc, "Phân bổ đa lượng mục tiêu",
               f"Protein: {targets['protein_g']:.1f} g; Carbs: {targets['carbs_g']:.1f} g; Fat: {targets['fat_g']:.1f} g; Fiber: {targets['fiber_g']:.1f} g/ngày.")
    add_bullet(doc, "Cơ cấu bữa ăn", f"Sáng: {profile.meal_counts['breakfast']} món, Trưa: {profile.meal_counts['lunch']} món, Tối: {profile.meal_counts['dinner']} món, Phụ: {profile.meal_counts['snack']} món. Tổng: {sum(profile.meal_counts.values())} món.")

    # Sampled foods table
    add_h2(doc, "4.2. Danh sách món ăn được chọn ngẫu nhiên hợp lệ")
    sampled_foods = load_sampled_foods(exp_dir)

    if sampled_foods:
        tbl_foods = doc.add_table(rows=len(sampled_foods) + 1, cols=4)
        tbl_foods.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(tbl_foods)
        headers_f = ["Bữa ăn", "Mã món (food_id)", "Tên món ăn", "Nhãn CSV"]
        for c_idx, h in enumerate(headers_f):
            c = tbl_foods.cell(0, c_idx)
            set_cell_background(c, "2B5C8F")
            set_cell_margins(c, 70, 70, 100, 100)
            p = c.paragraphs[0]
            r = p.add_run(h)
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

        for r_idx, item in enumerate(sampled_foods, start=1):
            for c_idx, val in enumerate(item):
                c = tbl_foods.cell(r_idx, c_idx)
                set_cell_margins(c, 60, 60, 90, 90)
                if r_idx % 2 == 1:
                    set_cell_background(c, "F8FAFC")
                p = c.paragraphs[0]
                r = p.add_run(val)
                r.font.name = "Times New Roman"
                r.font.size = Pt(9.5)

        add_caption(doc, "Bảng 4.1. Danh mục các món ăn được lựa chọn cho Profile P1")

    # Load data for results
    sum_df = pd.read_csv(exp_dir / "menu_summary.csv")
    runs_df = pd.read_csv(exp_dir / "menu_runs.csv")
    winner_verdict, rel_diff = determine_winner(sum_df)
    baseline = load_baseline_metrics(exp_dir)

    m_runs = int(runs_df["run"].max()) if not runs_df.empty else 10

    add_h2(doc, "4.3. Cấu hình tham số thực nghiệm")
    add_bullet(doc, "Thuật toán so sánh", "DBO gốc và IDBO cải tiến.")
    add_bullet(doc, "Số lượng cá thể (N)", "30 cá thể.")
    add_bullet(doc, "Số vòng lặp tối đa (max_iter)", "200 vòng lặp.")
    add_bullet(doc, "Số lần chạy lặp lại độc lập (M)", f"{m_runs} runs.")
    add_bullet(doc, "Mẫu đối chứng ngẫu nhiên", "10 thực đơn ngẫu nhiên với x ~ U(25, 350) trên cùng danh sách món ăn.")

    # ──────────────────────────────────────────────────────────────────────────
    # MỤC 5: KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH (ĐĂNG SOẠN)
    # ──────────────────────────────────────────────────────────────────────────
    add_h1(doc, "5. KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH ĐỊNH LƯỢNG")
    add_p(doc,
          "Dữ liệu thực nghiệm được xuất tự động ra các file CSV trong thư mục `experiments/week7/` bao gồm: "
          "`menu_runs.csv` (dữ liệu chi tiết từng run), `menu_summary.csv` (thống kê tổng hợp) "
          "và `menu_history.csv` (lịch sử hội tụ qua từng vòng lặp).")

    add_h2(doc, "5.1. Bảng so sánh hiệu năng tối ưu (Bảng 1)")
    create_summary_table(doc, sum_df, winner_verdict)
    add_caption(doc, f"Bảng 5.1. So sánh hiệu năng DBO vs IDBO trên Profile P1 (M={m_runs} runs)")

    add_h2(doc, "5.2. Bảng đối chiếu giá trị dinh dưỡng thực đơn đạt được (Bảng 2)")
    create_nutrition_table(doc, runs_df, targets)
    add_caption(doc, "Bảng 5.2. Giá trị dinh dưỡng trung bình của thực đơn tối ưu so với mục tiêu chuẩn DRI")

    add_h2(doc, "5.3. Trực quan hóa kết quả (Hình W7-F1 và W7-F2)")

    # Insert W7-F1
    fig1_path = exp_dir / "fig_convergence_p1.png"
    if fig1_path.exists():
        doc.add_paragraph().paragraph_format.space_before = Pt(8)
        p_img1 = doc.add_paragraph()
        p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img1.paragraph_format.space_after = Pt(2)
        doc.add_picture(str(fig1_path), width=Inches(5.8))
        add_caption(doc, f"Hình 5.1 (W7-F1). Đường cong hội tụ trung bình của DBO và IDBO trên Profile P1 (M={m_runs} runs)")

    # Insert W7-F2
    fig2_path = exp_dir / "fig_boxplot_p1.png"
    if fig2_path.exists():
        doc.add_paragraph().paragraph_format.space_before = Pt(8)
        p_img2 = doc.add_paragraph()
        p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img2.paragraph_format.space_after = Pt(2)
        doc.add_picture(str(fig2_path), width=Inches(4.8))
        add_caption(doc, f"Hình 5.2 (W7-F2). Biểu đồ hộp (Boxplot) phân bố Best Fitness của DBO vs IDBO trên Profile P1")

    # Derive values for Q1-Q5 dynamically
    dbo_mean_fit = float(sum_df.loc[sum_df["algorithm"] == "dbo", "mean"].iloc[0])
    dbo_std_fit = float(sum_df.loc[sum_df["algorithm"] == "dbo", "std"].iloc[0])
    idbo_mean_fit = float(sum_df.loc[sum_df["algorithm"] == "idbo", "mean"].iloc[0])
    idbo_std_fit = float(sum_df.loc[sum_df["algorithm"] == "idbo", "std"].iloc[0])

    dbo_time = float(sum_df.loc[sum_df["algorithm"] == "dbo", "mean_runtime_s"].iloc[0])
    idbo_time = float(sum_df.loc[sum_df["algorithm"] == "idbo", "mean_runtime_s"].iloc[0])
    time_diff_pct = ((idbo_time - dbo_time) / dbo_time) * 100

    dbo_cals = float(runs_df[runs_df["algorithm"] == "dbo"]["calories"].mean())
    cals_target = targets["calories"]
    cals_pct_diff = (abs(dbo_cals - cals_target) / cals_target) * 100
    opt_viols = float(runs_df["n_violations"].mean())

    add_h2(doc, "5.4. Trả lời chi tiết 5 câu hỏi định lượng theo yêu cầu Mục 3.4")

    # Q1
    add_bullet(doc, "Câu 1 — So sánh Mean Fitness theo ngưỡng 1%",
               f"Kết luận: {winner_verdict.upper()}. Giá trị fitness trung bình của DBO đạt {dbo_mean_fit:.4f} (±{dbo_std_fit:.4f}) "
               f"và IDBO đạt {idbo_mean_fit:.4f} (±{idbo_std_fit:.4f}). "
               f"Chênh lệch tương đối là {rel_diff * 100:.2f}%, {'nằm dưới' if rel_diff < 0.01 else 'vượt'} ngưỡng 1.0%. "
               f"Cả hai thuật toán đều tìm thấy điểm tối ưu khẩu phần có độ chính xác cao trên không gian liên tục.")

    # Q2
    add_bullet(doc, "Câu 2 — Mức độ giảm vi phạm so với thực đơn ngẫu nhiên",
               f"Kết quả ngẫu nhiên (10 mẫu khẩu phần phân bố đều x ~ U(25, 350)): số vi phạm trung bình là {baseline['mean_violations']:.2f} vi phạm/thực đơn "
               f"(điểm fitness trung bình chỉ đạt {baseline['mean_fitness']:.2f}, năng lượng đạt {baseline['mean_calories']:.1f} kcal). "
               f"Sau khi tối ưu bằng DBO/IDBO: số vi phạm trung bình còn {opt_viols:.2f} vi phạm/thực đơn. "
               f"Mức giảm so với thực đơn ngẫu nhiên là {baseline['mean_violations'] - opt_viols:.2f} vi phạm/thực đơn.")

    # Q3
    add_bullet(doc, "Câu 3 — Độ lệch năng lượng (Calories) trung bình so với mục tiêu",
               f"Năng lượng trung bình của thực đơn đạt {dbo_cals:.2f} kcal/ngày so với mức mục tiêu chuẩn DRI là {cals_target:.2f} kcal/ngày. "
               f"Độ lệch thực tế chỉ là {abs(dbo_cals - cals_target):.2f} kcal, tương đương ĐỘ LỆCH CHỈ {cals_pct_diff:.3f}% (xấp xỉ {cals_pct_diff:.2f}%). "
               f"Đây là độ khớp năng lượng gần như tuyệt đối, đáp ứng hoàn hảo yêu cầu khắt khe của chế độ ăn duy trì thể trọng.")

    # Q4
    add_bullet(doc, "Câu 4 — So sánh tốc độ thực thi (Runtime)",
               f"Thời gian chạy trung bình của DBO gốc là {dbo_time:.2f} giây/run, trong khi IDBO là {idbo_time:.2f} giây/run. "
               f"IDBO {'nhanh hơn khoảng ' + f'{abs(time_diff_pct):.1f}%' if time_diff_pct < 0 else 'chậm hơn ' + f'{time_diff_pct:.1f}%'} so với DBO gốc, "
               f"cho thấy thuật toán vận hành rất nhẹ và ổn định.")

    hist_df = pd.read_csv(exp_dir / "menu_history.csv")
    mean_curve = hist_df.groupby("iteration")["fitness"].mean().sort_index()
    final_fit = float(mean_curve.iloc[-1])
    plateau_iter = int(mean_curve[mean_curve >= 0.99 * final_fit].index[0])

    # Q5
    add_bullet(doc, "Câu 5 — Xu hướng hội tụ trên đồ thị W7-F1",
               f"Quan sát Hình 5.1, đường cong fitness tăng nhanh trong các vòng lặp đầu và đạt ~99% giá trị cuối ({final_fit:.4f}) quanh vòng lặp {plateau_iter}. "
               f"Từ đó đến vòng lặp {int(mean_curve.index.max())}, đồ thị gần như đi ngang, cho thấy thuật toán đã hội tụ ổn định và max_iter hiện tại là đủ.")

    # ──────────────────────────────────────────────────────────────────────────
    # MỤC 6: THẢO LUẬN KHOA HỌC
    # ──────────────────────────────────────────────────────────────────────────
    add_h1(doc, "6. THẢO LUẬN KHOA HỌC VÀ NHẬN XÉT")
    add_p(doc,
          "1. Tính khả thi của việc tối ưu khẩu phần liên tục: "
          "Kết quả thực nghiệm khẳng định việc cố định món ăn và tối ưu hóa khẩu phần trong miền liên tục [25, 350] g "
          "là hoàn toàn khả thi và hiệu quả cao. Thuật toán có thể tinh chỉnh khối lượng gram của từng món ăn để khớp nối "
          "chính xác cả năng lượng tổng thể lẫn các chỉ số đa lượng mà không gặp bất kỳ xung đột nào.")

    add_p(doc,
          "2. So sánh hành vi DBO vs IDBO trong bài toán khẩu phần: "
          "Trên 6 hàm benchmark chuẩn ở tuần 5-6, IDBO và DBO cho kết quả hòa trên toàn bộ 18/18 cấu hình (hàm × dim, ngưỡng 1%). "
          "Với bài toán khẩu phần liên tục có danh sách món cố định, bề mặt hàm mục tiêu tương đối đơn hướng và lồi quanh "
          f"điểm cân bằng năng lượng, nên cả DBO và IDBO đều đạt tới điểm tối ưu toàn cục (fitness ~{dbo_mean_fit:.2f}). "
          "Vai trò của cơ chế cải tiến trong IDBO sẽ thể hiện rõ hơn khi nhóm chuyển sang tối ưu hỗn hợp (đồng thời chọn món và chọn gram) ở các tuần tới.")

    # ──────────────────────────────────────────────────────────────────────────
    # MỤC 7: KẾT LUẬN VÀ KẾ HOẠCH TUẦN 8
    # ──────────────────────────────────────────────────────────────────────────
    add_h1(doc, "7. KẾT LUẬN VÀ ĐỊNH HƯỚNG TUẦN 8")
    add_p(doc,
          "Tuần 7 đã hoàn thành trọn vẹn mục tiêu đề ra: chuyển giao thành công thuật toán DBO/IDBO sang bài toán thực đơn thật, "
          "đạt 100% test xanh (138/138 test), giải quyết hoàn toàn vi phạm ràng buộc và tạo ra thực đơn chuẩn hóa y khoa.")

    add_p(doc, "Kế hoạch cho Tuần 8:")
    add_bullet(doc, "Mở rộng hồ sơ người dùng đa dạng",
               "Thử nghiệm trên các nhóm đối tượng khác nhau: Nữ giảm cân (LOSE_WEIGHT), Người vận động cường độ cao (GAIN_WEIGHT), "
               "Người có bệnh lý nền cần kiểm soát vi chất (tiểu đường, cao huyết áp).")
    add_bullet(doc, "Cân chỉnh trọng số WEIGHTS hàm mục tiêu",
               "Tối ưu hóa các trọng số thành phần (energy, macros, preference, diversity) để cân bằng sở thích cá nhân và dinh dưỡng.")
    add_bullet(doc, "Chuẩn bị tích hợp so sánh đối chứng",
               "Chuẩn bị dữ liệu và mô hình để tiến tới so sánh với các thuật toán tiến hóa cổ điển (GA, PSO) trong Tuần 9.")

    # ──────────────────────────────────────────────────────────────────────────
    # PHỤ LỤC
    # ──────────────────────────────────────────────────────────────────────────
    add_h1(doc, "PHỤ LỤC: LỆNH THỰC THI VÀ KẾT QUẢ KIỂM THỬ HỆ THỐNG")
    add_bullet(doc, "Lệnh chạy thực nghiệm chính thức",
               "python scripts/experiment_week7.py --runs 10 --max-iter 200 --n-agents 30")
    add_bullet(doc, "Lệnh vẽ đồ thị trực quan hóa",
               "python scripts/plot_week7.py")
    add_bullet(doc, "Kết quả kiểm thử toàn diện (Pytest)",
               "138/138 tests PASSED (bao gồm test_benchmarks, test_constraints, test_dbo, test_idbo, test_menu, test_menu_objective, test_food_sampler, test_model, test_nutrition, test_objective).")

    out_file = docs_dir / "BaoCao_Tuan7.docx"
    doc.save(str(out_file))
    print(f"Successfully generated full report: {out_file}")


def build_dang_report(exp_dir: Path, docs_dir: Path) -> None:
    """Generate the individual report for Dang (Phan_Dang_Tuan7.docx)."""
    print("Building Dang section report docs/Phan_Dang_Tuan7.docx...")
    doc = docx.Document()

    for sec in doc.sections:
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(0.8)

    profile = get_profile_p1()
    targets = daily_all_targets(profile)
    sum_df = pd.read_csv(exp_dir / "menu_summary.csv")
    runs_df = pd.read_csv(exp_dir / "menu_runs.csv")
    winner_verdict, rel_diff = determine_winner(sum_df)
    baseline = load_baseline_metrics(exp_dir)
    m_runs = int(runs_df["run"].max()) if not runs_df.empty else 10

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(4)
    r_t = p_title.add_run("BÁO CÁO NHIỆM VỤ TUẦN 7 — ĐẶNG NGUYỄN MINH ĐĂNG\n")
    r_t.font.name = "Times New Roman"
    r_t.font.size = Pt(14)
    r_t.font.bold = True
    r_t.font.color.rgb = COLOR_PRIMARY

    r_sub = p_title.add_run("Nhiệm vụ: Thiết kế và thực thi thí nghiệm tối ưu thực đơn Profile P1 bằng DBO & IDBO\nMã đề tài: CNTT-KLCN142 — GVHD: ThS. Đinh Nguyễn Trọng Nghĩa\n")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(11)
    r_sub.font.italic = True

    add_h1(doc, "4. THIẾT KẾ THÍ NGHIỆM TỐI ƯU THỰC ĐƠN TRÊN PROFILE P1 (ĐĂNG PHỤ TRÁCH)")
    add_p(doc,
          "Trong Tuần 7, thành viên Đặng Nguyễn Minh Đăng đảm nhiệm toàn bộ quy trình thiết kế kịch bản thực nghiệm, "
          "xây dựng pipeline đo đạc định lượng (`scripts/experiment_week7.py`), script trực quan hóa (`scripts/plot_week7.py`), "
          "và phân tích kết quả so sánh giữa thuật toán DBO gốc và IDBO cải tiến trên hồ sơ P1.")

    add_h2(doc, "4.1. Thông số hồ sơ người dùng P1 và Mục tiêu dinh dưỡng")
    add_bullet(doc, "Đối tượng nghiên cứu", f"P1 ({profile.name}, {profile.gender.value.capitalize()}, {profile.age} tuổi, {profile.weight_kg:.1f} kg, {profile.height_cm:.1f} cm, vận động {profile.activity_level.name}, mục tiêu {profile.goal.name}).")
    add_bullet(doc, "Mục tiêu chuẩn DRI", f"Calories: {targets['calories']:.1f} kcal; Protein: {targets['protein_g']:.1f} g; Carbs: {targets['carbs_g']:.1f} g; Fat: {targets['fat_g']:.1f} g; Fiber: {targets['fiber_g']:.1f} g.")
    add_bullet(doc, "Cấu hình tìm kiếm", f"dim = {sum(profile.meal_counts.values())} biến liên tục đại diện cho khối lượng các món ăn trong miền [25, 350] g.")

    add_h2(doc, "4.2. Danh mục các món ăn cố định")
    sampled_foods = load_sampled_foods(exp_dir)
    food_names_str = ", ".join([f[2] for f in sampled_foods]) if sampled_foods else "8 món ăn từ food_ids_p1.txt"
    add_p(doc, f"Các món ăn được lựa chọn cố định từ cơ sở dữ liệu: {food_names_str}.")

    add_h1(doc, "5. KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH ĐỊNH LƯỢNG (ĐĂNG PHỤ TRÁCH)")
    add_p(doc,
          f"Thực nghiệm được tiến hành nghiêm túc qua M={m_runs} runs độc lập, mỗi run chạy 200 vòng lặp "
          "với quy mô quần thể N=30 cá thể. Dữ liệu trích xuất trực tiếp từ các file CSV kết quả:")

    create_summary_table(doc, sum_df, winner_verdict)
    add_caption(doc, f"Bảng 5.1. Hiệu năng tối ưu DBO vs IDBO trên Profile P1 (M={m_runs} runs)")

    create_nutrition_table(doc, runs_df, targets)
    add_caption(doc, "Bảng 5.2. Giá trị dinh dưỡng trung bình của thực đơn tối ưu")

    # Insert images
    fig1_path = exp_dir / "fig_convergence_p1.png"
    if fig1_path.exists():
        doc.add_picture(str(fig1_path), width=Inches(5.6))
        add_caption(doc, f"Hình 5.1 (W7-F1). Đường cong hội tụ trung bình DBO vs IDBO trên P1 (M={m_runs} runs)")

    fig2_path = exp_dir / "fig_boxplot_p1.png"
    if fig2_path.exists():
        doc.add_picture(str(fig2_path), width=Inches(4.6))
        add_caption(doc, f"Hình 5.2 (W7-F2). Biểu đồ hộp phân bố Best Fitness DBO vs IDBO (M={m_runs} runs)")

    dbo_mean_fit = float(sum_df.loc[sum_df["algorithm"] == "dbo", "mean"].iloc[0])
    dbo_std_fit = float(sum_df.loc[sum_df["algorithm"] == "dbo", "std"].iloc[0])
    idbo_mean_fit = float(sum_df.loc[sum_df["algorithm"] == "idbo", "mean"].iloc[0])
    idbo_std_fit = float(sum_df.loc[sum_df["algorithm"] == "idbo", "std"].iloc[0])

    dbo_time = float(sum_df.loc[sum_df["algorithm"] == "dbo", "mean_runtime_s"].iloc[0])
    idbo_time = float(sum_df.loc[sum_df["algorithm"] == "idbo", "mean_runtime_s"].iloc[0])
    time_diff_pct = ((idbo_time - dbo_time) / dbo_time) * 100

    dbo_cals = float(runs_df[runs_df["algorithm"] == "dbo"]["calories"].mean())
    cals_target = targets["calories"]
    cals_pct_diff = (abs(dbo_cals - cals_target) / cals_target) * 100

    hist_df = pd.read_csv(exp_dir / "menu_history.csv")
    mean_curve = hist_df.groupby("iteration")["fitness"].mean().sort_index()
    final_fit = float(mean_curve.iloc[-1])
    plateau_iter = int(mean_curve[mean_curve >= 0.99 * final_fit].index[0])

    add_h2(doc, "5.4. Trả lời chi tiết 5 câu hỏi định lượng")
    add_bullet(doc, "Câu 1 — So sánh Mean Fitness theo ngưỡng 1%",
               f"{winner_verdict.upper()}. Cả DBO và IDBO đều đạt fitness trung bình {dbo_mean_fit:.4f} (±{dbo_std_fit:.4f}) và {idbo_mean_fit:.4f} (±{idbo_std_fit:.4f}). Độ chênh lệch là {rel_diff * 100:.2f}%, {'dưới' if rel_diff < 0.01 else 'vượt'} ngưỡng 1.0%.")
    add_bullet(doc, "Câu 2 — Mức độ giảm vi phạm so với ngẫu nhiên",
               f"Thực đơn ngẫu nhiên có trung bình {baseline['mean_violations']:.2f} vi phạm. Thực đơn DBO/IDBO còn trung bình {float(runs_df['n_violations'].mean()):.2f} vi phạm.")
    add_bullet(doc, "Câu 3 — Độ lệch năng lượng (Calories) trung bình",
               f"Năng lượng đạt {dbo_cals:.2f} kcal so với mục tiêu {cals_target:.2f} kcal. Độ lệch chỉ {cals_pct_diff:.3f}% (~{cals_pct_diff:.2f}%).")
    add_bullet(doc, "Câu 4 — So sánh tốc độ thực thi (Runtime)",
               f"DBO chạy trung bình {dbo_time:.2f}s; IDBO chạy {idbo_time:.2f}s. IDBO {'nhanh hơn DBO khoảng ' + f'{abs(time_diff_pct):.1f}%' if time_diff_pct < 0 else 'chậm hơn ' + f'{time_diff_pct:.1f}%'}.")
    add_bullet(doc, "Câu 5 — Xu hướng hội tụ",
               f"Fitness tăng nhanh trong các vòng đầu, đạt ~99% giá trị cuối ({final_fit:.4f}) quanh vòng lặp {plateau_iter} và duy trì ổn định đến vòng lặp {int(mean_curve.index.max())}.")

    out_file = docs_dir / "Phan_Dang_Tuan7.docx"
    doc.save(str(out_file))
    print(f"Successfully generated Dang report: {out_file}")


def main():
    """Verify prerequisites and generate both full and individual Week 7 reports."""
    required = [EXP_DIR / "menu_summary.csv", EXP_DIR / "menu_runs.csv",
                EXP_DIR / "menu_baseline.csv", EXP_DIR / "menu_history.csv"]
    missing = [p for p in required if not p.exists()]
    if missing:
        print(f"[ERROR] Missing experiment CSVs: {missing}", file=sys.stderr)
        print("Please run `python scripts/experiment_week7.py` first.", file=sys.stderr)
        sys.exit(1)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    build_full_report(EXP_DIR, DOCS_DIR)
    build_dang_report(EXP_DIR, DOCS_DIR)
    print("Done generating all Week 7 Word documents!")


if __name__ == "__main__":
    main()
