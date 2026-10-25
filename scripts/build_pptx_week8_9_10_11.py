"""Dựng slide báo cáo tổng hợp Tuần 8 – 9 – 10 – 11 (DBO / IDBO Healthcare Menu Optimization).

Đề tài: CNTT-KLCN142 — Trường Đại học Công Thương TP.HCM (HUIT)
Thực hiện: Lê Quang Duy (Nhóm trưởng), Hồ Trung Cương, Đặng Nguyễn Minh Đăng.

Chuỗi tiến độ gộp 4 tuần trọng tâm (14 slide chuẩn học thuật 16:9, đầy đủ hình ảnh dẫn chứng thực tế):
- Slide 1: Bìa báo cáo tổng quan Tuần 8 – 9 – 10 – 11
- Slide 2: [Tổng quan] Lộ trình phát triển & Bước chuyển kiến trúc qua 4 tuần (Tuần 8 -> 11)
- Slide 3: [Tuần 8] Kiến trúc tối ưu 2 tầng (Mixed-Integer Two-Tier Solver) & Bể ứng viên 15.929 món
- Slide 4: [Tuần 8] Thực nghiệm đối chuẩn 10 runs độc lập, Đồ thị hội tụ & Phân phối nghiệm (W8-F1 & W8-F2)
- Slide 5: [Tuần 8] Cân đối dinh dưỡng & Thực đơn đề xuất chuẩn hóa khẩu phần 5g (W8-F3)
- Slide 6: [Tuần 9] Lập thực đơn chu kỳ 7 ngày & Cơ chế Diversity Penalty (Kèm hình Heatmap W9-F1)
- Slide 7: [Tuần 9] Đối chuẩn trên 3 hồ sơ bệnh lý (P1, P2, P3) & Trải nghiệm UX Option A/B/C (Kèm hình W9-F2 & W9-F3)
- Slide 8: [Tuần 10] Nghiệm thu Hệ thống Web API & Giao diện Người dùng Web UI (Kèm ảnh chụp màn hình thực tế)
- Slide 9: [Tuần 11] Thực nghiệm đối đầu DBO vs IDBO trên Tập độc lập Seed 8003–8010 (Kèm hình W11-F1)
- Slide 10: [Tuần 11] Đánh đổi chi phí tính toán: Lượt Evaluations & Thời gian chạy (Kèm hình W11-F2)
- Slide 11: [Tuần 11] Giải mã Telemetry: Hoạt động Tầng ngoài vs Tầng trong (Kèm hình W11-F3)
- Slide 12: [Tuần 11] Kiểm soát ngân sách tính toán chung (Budget-Matched Benchmark, Kèm hình W11-F4)
- Slide 13: [Tuần 11] Kiến trúc Ngưỡng kép (Dual Threshold) & Nghiệm thu chất lượng 253/253 tests PASS
- Slide 14: Tổng kết toàn diện giai đoạn Tuần 8–11 & Kế hoạch nghiên cứu Tuần 12
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image
import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "slides"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PPTX_MERGED = OUT_DIR / "Slide_Bao_Cao_Tuan_8_9_10_11_DBO_IDBO.pptx"
OUT_PPTX_USER_TAGGED = OUT_DIR / "Slide_Bao_Cao_Tuan_9_10_11_DBO_IDBO.pptx"

W8_DIR = ROOT / "experiments" / "week8"
W9_DIR = ROOT / "experiments" / "week9"
W11_DIR = ROOT / "experiments" / "ablation_dbo_idbo"

# --------------------------------------------------------------------------- #
# Bảng màu chuẩn học thuật (Academic Dark Navy / Teal / Coral)
# --------------------------------------------------------------------------- #
INDIGO = RGBColor(0x1B, 0x2A, 0x4A)       # Xanh Navy đậm chủ đạo
INDIGO2 = RGBColor(0x2D, 0x3E, 0x63)      # Xanh Navy phụ
AMBER = RGBColor(0xD9, 0x82, 0x2B)        # Cam Vàng điểm nhấn
TEAL = RGBColor(0x1D, 0x6F, 0x6F)         # Xanh Teal
GREEN = RGBColor(0x21, 0x7A, 0x4B)        # Xanh lá tích cực
RED = RGBColor(0xB8, 0x32, 0x28)          # Đỏ cảnh báo / điểm nghẽn
INK = RGBColor(0x1E, 0x24, 0x30)          # Đen chữ chính
MUTED = RGBColor(0x5A, 0x64, 0x78)        # Xám ghi chữ phụ
LIGHT = RGBColor(0xF8, 0xFA, 0xFC)        # Nền thẻ sáng
LINE = RGBColor(0xCB, 0xD5, 0xE1)         # Đường viền ngăn cách
WHITE = RGBColor(0xFF, 0xFF, 0xFF)        # Trắng tinh
CREAM = RGBColor(0xFD, 0xF6, 0xEB)        # Nền kem ghi chú

FONT = "Calibri"
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
TOTAL_SLIDES = 14


def _add_run(paragraph, text=""):
    r = paragraph.add_run()
    if text:
        r.text = text
    return r


def _style_run(run, size, bold, color, italic=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", FONT)


def _header(slide, title_text, category_text):
    cat_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.1), Inches(0.3))
    tf_cat = cat_box.text_frame
    tf_cat.word_wrap = True
    tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
    p_cat = tf_cat.paragraphs[0]
    r_cat = _add_run(p_cat, category_text.upper())
    _style_run(r_cat, 11, True, AMBER)

    t_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.68), Inches(12.1), Inches(0.6))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
    p_t = tf_t.paragraphs[0]
    r_t = _add_run(p_t, title_text)
    _style_run(r_t, 21, True, INDIGO)

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.32), Inches(12.133), Pt(1.5))
    line.fill.solid()
    line.fill.fore_color.rgb = LINE
    line.line.color.rgb = LINE


def _footer(slide, current_page, total_pages=TOTAL_SLIDES):
    foot_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(7.05), Inches(12.133), Pt(1))
    foot_line.fill.solid()
    foot_line.fill.fore_color.rgb = LINE
    foot_line.line.color.rgb = LINE

    tb = slide.shapes.add_textbox(Inches(0.6), Inches(7.12), Inches(9.5), Inches(0.3))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    r = _add_run(p, "CNTT-KLCN142 — Đề xuất thực đơn dinh dưỡng cá nhân hóa bằng DBO/IDBO | Tổng hợp Tuần 8 – 9 – 10 – 11")
    _style_run(r, 9.5, False, MUTED)

    tb2 = slide.shapes.add_textbox(Inches(10.5), Inches(7.12), Inches(2.2), Inches(0.3))
    tf2 = tb2.text_frame
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    r2 = _add_run(p2, f"{current_page} / {total_pages}")
    _style_run(r2, 9.5, True, MUTED)


def _card(slide, left, top, width, height, bg_color=LIGHT, border_color=LINE):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
    else:
        card.line.fill.background()
    return card


def _fit_image(path: Path, box_w: float, box_h: float) -> Tuple[int, int]:
    with Image.open(path) as im:
        iw, ih = im.size
    box_aspect = box_w / box_h
    aspect = iw / ih
    if aspect > box_aspect:
        w = int(box_w)
        h = int(box_w / aspect)
    else:
        h = int(box_h)
        w = int(box_h * aspect)
    return w, h


def _table(slide, rows, l, t, w, h, col_w, header_color, body_size=10.0,
           row_h=None, highlight=None, header_size=11.0, align_cols=None):
    n_row, n_col = len(rows), len(rows[0])
    shape = slide.shapes.add_table(n_row, n_col, l, t, w, h)
    tbl = shape.table
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = cw
    if row_h is not None:
        for r in range(n_row):
            tbl.rows[r].height = row_h if r else Inches(0.40)
    highlight = highlight or {}
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            if align_cols is not None and c in align_cols:
                p.alignment = align_cols[c]
            else:
                p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            run = p.add_run()
            run.text = str(val)
            is_header = r == 0
            col, bold = INK, (c == 0)
            if is_header:
                col, bold = WHITE, True
            elif (r, c) in highlight:
                col, bold = highlight[(r, c)]
            _style_run(run, header_size if is_header else body_size, bold, col)
            cell.fill.solid()
            if is_header:
                cell.fill.fore_color.rgb = header_color
            else:
                cell.fill.fore_color.rgb = LIGHT if r % 2 == 1 else WHITE
    return tbl


# =========================================================================== #
# SLIDE 1: BÌA BÁO CÁO TỔNG HỢP TUẦN 8 - 9 - 10 - 11
# =========================================================================== #
def build_slide_1(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = INDIGO
    bg.line.fill.background()

    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.2), Inches(0.15), Inches(4.8))
    bar.fill.solid()
    bar.fill.fore_color.rgb = AMBER
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(11.0), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "TRƯỜNG ĐẠI HỌC CÔNG THƯƠNG TP. HỒ CHÍ MINH — KHOA CÔNG NGHỆ THÔNG TIN\nKHÓA LUẬN TỐT NGHIỆP | MÃ ĐỀ TÀI: CNTT-KLCN142\n")
    _style_run(r0, 13, True, AMBER)

    p1 = tf.add_paragraph()
    p1.space_before = Pt(12)
    r1 = _add_run(p1, "Tối Ưu Hóa Thực Đơn Dinh Dưỡng Cá Nhân Hóa\nBằng Thuật Toán DBO và IDBO")
    _style_run(r1, 30, True, WHITE)

    p2 = tf.add_paragraph()
    p2.space_before = Pt(12)
    r2 = _add_run(p2, "BÁO CÁO TIẾN ĐỘ TỔNG HỢP GIAI ĐOẠN TUẦN 8 – TUẦN 9 – TUẦN 10 – TUẦN 11\n(TỐI ƯU 2 TẦNG · LẬP KẾ HOẠCH 7 NGÀY · HỆ THỐNG WEB API · ĐỐI CHUẨN BUDGET-MATCHED)")
    _style_run(r2, 15.5, True, RGBColor(0x6E, 0xC5, 0xC5))

    p3 = tf.add_paragraph()
    p3.space_before = Pt(24)
    r3 = _add_run(p3, "Sinh viên thực hiện:\n"
                      "• Lê Quang Duy (2001210356) — Nhóm trưởng (Thống kê, Báo cáo & Phân tích Thuật toán)\n"
                      "• Hồ Trung Cương (2001215682) — Phụ trách Two-Tier Solver, Budget-Matched & Dual Threshold\n"
                      "• Đặng Nguyễn Minh Đăng (2001230175) — Phụ trách Web/API, Trực quan hóa & Trải nghiệm Người dùng\n\n"
                      "Giảng viên hướng dẫn: ThS. Đinh Nguyễn Trọng Nghĩa | Thời gian: Tháng 10/2026")
    _style_run(r3, 13, False, RGBColor(0xE2, 0xE8, 0xF0))


# =========================================================================== #
# SLIDE 2: LỘ TRÌNH PHÁT TRIỂN & BƯỚC CHUYỂN KIẾN TRÚC QUA 4 TUẦN
# =========================================================================== #
def build_slide_2(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "Lộ Trình Phát Triển & Bước Chuyển Kiến Trúc Giai Đoạn Tuần 8 – 11", "Bối Cảnh & Tổng Quan Tiến Độ")

    weeks = [
        ("TUẦN 8: BÀI TOÁN 2 TẦNG",
         "Mixed-Integer Two-Tier Solver",
         "• Chuyển từ định lượng cố định 8 món sang tự do chọn món từ 15.929 thực phẩm.\n"
         "• Tầng 1 (Outer): Chọn tổ hợp món rời rạc theo 4 bữa.\n"
         "• Tầng 2 (Inner): Tối ưu gram liên tục x ∈ [25, 350].\n"
         "• Chuẩn hóa làm tròn khẩu phần theo bước 5g thực tế.\n"
         "• Đối chuẩn 10 seed độc lập trên Profile P1.",
         INDIGO, LIGHT),
        ("TUẦN 9: KẾ HOẠCH 7 NGÀY",
         "Diversity Penalty & Multi-Profile",
         "• Lập thực đơn chu kỳ 7 ngày liên tục, giải quyết nhàm chán.\n"
         "• Cơ chế Diversity Penalty cửa sổ trượt 2 ngày (>= 80% độc nhất món chính).\n"
         "• Mở rộng 3 hồ sơ bệnh lý: P1 (Chuẩn), P2 (Giảm Carbs), P3 (Kiểm soát Natri <= 1500mg).\n"
         "• Sinh 3 phương án UX Option A/B/C.",
         TEAL, LIGHT),
        ("TUẦN 10: WEB API & UI",
         "FastAPI Backend & Glassmorphism",
         "• Đóng gói toàn bộ solver thành Web API RESTful.\n"
         "• Kiến trúc Single-port phục vụ đồng thời API & Static Frontend trên cổng 8000.\n"
         "• 6 endpoints chuẩn hóa, xử lý phi nghẽn async.\n"
         "• Giao diện Dark Theme Glassmorphism hiện đại, biểu đồ Radar 6 trục dinh dưỡng.",
         AMBER, CREAM),
        ("TUẦN 11: CHUẨN HÓA KHOA HỌC",
         "Budget-Matched & Dual Threshold",
         "• Tách riêng tập hiệu chỉnh và tập kiểm định độc lập (seed 8003–8010).\n"
         "• Kiểm định Wilcoxon: đo lường ý nghĩa thống kê.\n"
         "• Giải mã Telemetry & Chi phí tính toán (+18.6% Evals).\n"
         "• Kiểm soát ngân sách chung (Budget-Matched).\n"
         "• Hoàn thiện Dual Threshold & 253 tests PASS.",
         GREEN, LIGHT),
    ]

    for i, (title, sub, body, accent_col, bg_col) in enumerate(weeks):
        l = Inches(0.55 + i * 3.11)
        _card(slide, l, Inches(1.50), Inches(2.93), Inches(5.35), bg_color=bg_col, border_color=LINE)
        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, Inches(1.50), Inches(2.93), Inches(0.08))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = accent_col
        top_bar.line.fill.background()

        tb = slide.shapes.add_textbox(l + Inches(0.18), Inches(1.68), Inches(2.57), Inches(5.0))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        r0 = _add_run(p0, title)
        _style_run(r0, 12.5, True, accent_col)

        p1 = tf.add_paragraph()
        p1.space_before = Pt(3)
        r1 = _add_run(p1, sub)
        _style_run(r1, 10, True, INK)

        sep = tf.add_paragraph()
        sep.space_before = Pt(6)
        r_sep = _add_run(sep, "—" * 22)
        _style_run(r_sep, 8, False, LINE)

        p2 = tf.add_paragraph()
        p2.space_before = Pt(6)
        r2 = _add_run(p2, body)
        _style_run(r2, 9.8, False, INK)

    _footer(slide, 2)


# =========================================================================== #
# SLIDE 3: [TUẦN 8] KIẾN TRÚC TỐI ƯU 2 TẦNG & BỂ ỨNG VIÊN 15.929 MÓN
# =========================================================================== #
def build_slide_3(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 8] Kiến Trúc Tối Ưu Hóa 2 Tầng & Chiến Lược Lọc Bể Ứng Viên", "Thiết Kế Giải Thuật (Tuần 8)")

    # Cột trái: Kiến trúc 2 tầng
    _card(slide, Inches(0.6), Inches(1.5), Inches(5.9), Inches(5.4))
    tb1 = slide.shapes.add_textbox(Inches(0.85), Inches(1.7), Inches(5.4), Inches(5.0))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    r0 = _add_run(p0, "Kiến Trúc Two-Tier Solver (Mixed-Integer)")
    _style_run(r0, 15.5, True, INDIGO)

    outer_inner_points = [
        ("Tầng 1 — Outer Solver (Chọn tổ hợp món rời rạc):",
         "• Vector cá thể bọ hung: z = (z₁, ..., z₈) với z_i ∈ [0, 1).\n"
         "• Ánh xạ chỉ mục Pool: idx_i = floor(z_i × |Pool_i|), giải mã ra tập food_ids.\n"
         "• Cơ cấu 4 bữa ăn (meal_counts): Sáng (2 món), Trưa (2 món: Đạm + Rau/Canh), Tối (2 món), Phụ (2 món: Trái cây/Hạt).\n"
         "• Độ thích nghi của z: Chính là kết quả tốt nhất đạt được sau khi chạy tầng 2 trên tổ hợp món đó."),
        ("Tầng 2 — Inner Solver (Tối ưu định lượng khẩu phần liên tục):",
         "• Vector liên tục x = (x₁, ..., x₈) ∈ [25g, 350g]^8 biểu diễn số gram từng món.\n"
         "• Chạy IDBO bám sát mục tiêu Năng lượng & Tỷ lệ đa lượng (Carbs / Protein / Fat).\n"
         "• Thời gian giải nhanh: 0.17s – 0.30s cho mỗi lần chạy Inner Solver."),
        ("Quy chuẩn làm tròn khẩu phần 5g thực tế chế biến:",
         "• module portion_utils: round_portions(x, step=5) loại bỏ hoàn toàn số lẻ thập phân.\n"
         "• Dinh dưỡng được tính toán lại và thẩm định validate_menu() trên chính nghiệm đã làm tròn.")
    ]
    for title, desc in outer_inner_points:
        p = tf1.add_paragraph()
        p.space_before = Pt(8)
        rt = _add_run(p, f"★ {title}\n")
        _style_run(rt, 11, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 10, False, INK)

    # Cột phải: Bể ứng viên
    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb2 = slide.shapes.add_textbox(Inches(7.05), Inches(1.7), Inches(5.4), Inches(5.0))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    p2 = tf2.paragraphs[0]
    r2 = _add_run(p2, "Chiến Lược Lọc Bể Ứng Viên (Candidate Pools)")
    _style_run(r2, 15.5, True, INDIGO)

    pool_points = [
        ("Kho CSDL gốc tích hợp 15.929 thực phẩm:",
         "Hợp nhất từ nguồn thực phẩm chuẩn USDA và Viện Dinh Dưỡng Quốc Gia Việt Nam, cung cấp đầy đủ thông số calo và dinh dưỡng đa lượng."),
        ("Phân loại 4 Bể Ứng Viên chuyên biệt theo bữa:",
         "• Bữa sáng (Breakfast Pool): 2.140 món (Ngũ cốc, bánh mì, sữa tươi, cháo dinh dưỡng).\n"
         "• Món chính trưa (Lunch Main): 3.480 món giàu Protein (thịt gà, bò, cá, đậu phụ).\n"
         "• Canh / Rau trưa (Lunch Side): 1.850 món giàu chất xơ, vitamin và khoáng chất.\n"
         "• Món chính tối (Dinner Main): 3.120 món đạm dễ tiêu hóa, khống chế Natri & chất béo.\n"
         "• Rau / Bữa phụ (Dinner Side & Snack): 2.680 món trái cây ít ngọt, các loại hạt, sữa chua."),
        ("Lọc ràng buộc sở thích & dị ứng trước khi giải:",
         "Tự động loại bỏ các thành phần dị ứng (hải sản, đậu phộng, gluten) theo hồ sơ người dùng. Đảm bảo mỗi slot có từ 50–200 món khả thi 100%.")
    ]
    for title, desc in pool_points:
        p = tf2.add_paragraph()
        p.space_before = Pt(8)
        rt = _add_run(p, f"• {title}\n")
        _style_run(rt, 11, True, TEAL)
        rd = _add_run(p, desc)
        _style_run(rd, 10, False, INK)

    _footer(slide, 3)


# =========================================================================== #
# SLIDE 4: [TUẦN 8] THỰC NGHIỆM ĐỐI CHUẨN 10 RUNS & ĐỒ THỊ W8-F1, W8-F2
# =========================================================================== #
def build_slide_4(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 8] Kết Quả Đối Chuẩn 10 Runs Độc Lập & Đồ Thị Hội Tụ / Phân Phối", "Đối Chuẩn Giải Thuật (Tuần 8)")

    f1_path = W8_DIR / "fig_convergence_2tier_p1.png"
    if f1_path.exists():
        w, h = _fit_image(f1_path, Inches(6.0), Inches(2.6))
        slide.shapes.add_picture(str(f1_path), Inches(0.6), Inches(1.5), w, h)

    f2_path = W8_DIR / "fig_boxplot_2tier_p1.png"
    if f2_path.exists():
        w, h = _fit_image(f2_path, Inches(6.0), Inches(2.6))
        slide.shapes.add_picture(str(f2_path), Inches(0.6), Inches(4.3), w, h)

    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(7.05), Inches(1.7), Inches(5.4), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Số Liệu Đối Chuẩn Tuần 8 (Profile P1, 10 Seeds)")
    _style_run(r0, 15.5, True, INDIGO)

    points = [
        ("Cấu hình thử nghiệm:", "10 seed độc lập (8001–8010), hồ sơ nam 22 tuổi (mục tiêu 2491.6 kcal). Cấu hình cơ sở: 25 vòng ngoài, 25 vòng trong, quần thể 20/15 cá thể."),
        ("Kết quả hiệu năng đạt được:", "• Best Fitness: 99.5106 tại seed 8003; mức sai lệch calo chỉ 8.1 kcal (0.32%).\n• Mean Fitness: 98.2148 ± 1.0663 | Worst Fitness: 96.3425.\n• Vi phạm ràng buộc: 0.0 / 10 lượt chạy (100% hợp lệ). Thời gian chạy TB: 7.6s – 8.2s."),
        ("Nhận định từ đồ thị W8-F1 & W8-F2:", "• W8-F1 (Hội tụ): Đường cong hội tụ tầng ngoài giảm nhanh và ổn định sau ~10 vòng lặp.\n• W8-F2 (Boxplot): Phân phối Best Fitness có trung vị 98.4, khoảng biến thiên hẹp [96.3, 99.5], không xuất hiện outlier suy biến."),
        ("Chẩn đoán Telemetry Tuần 8 (Ablation Diagnostic):", "Trong cấu hình cơ sở 25 vòng, DBO và IDBO cho kết quả tương đương do độ đa dạng thực tế duy trì ở mức cao (min_diversity = 0.246 > threshold 0.05). Khi nâng ngưỡng chẩn đoán lên 0.50, IDBO kích hoạt mạnh 30 lần ở Outer và 8.098 lần ở Inner -> Khẳng định thuật toán kết nối chính xác và mở đường cho việc tối ưu ngưỡng ở Tuần 11.")
    ]
    for title, desc in points:
        p = tf.add_paragraph()
        p.space_before = Pt(6)
        rt = _add_run(p, f"• {title}\n  ")
        _style_run(rt, 11, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 10, False, INK)

    _footer(slide, 4)


# =========================================================================== #
# SLIDE 5: [TUẦN 8] CÂN ĐỐI DINH DƯỠNG & THỰC ĐƠN ĐỀ XUẤT 5G (W8-F3)
# =========================================================================== #
def build_slide_5(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 8] Cân Đối Dinh Dưỡng & Thực Đơn Đề Xuất Chuẩn Hóa Khẩu Phần 5g", "Case Study & Khẩu Phần Thực Tế (Tuần 8)")

    f3_path = W8_DIR / "fig_radar_nutrition_p1.png"
    if f3_path.exists():
        w, h = _fit_image(f3_path, Inches(5.8), Inches(5.4))
        slide.shapes.add_picture(str(f3_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(6.6), Inches(1.5), Inches(6.1), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(6.8), Inches(1.65), Inches(5.7), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Thực Đơn Tối Ưu Cho Profile P1 (Seed 8003)")
    _style_run(r0, 14.5, True, INDIGO)

    p_sub = tf.add_paragraph()
    p_sub.space_before = Pt(2)
    r_sub = _add_run(p_sub, "Tổng Calo: 2483.6 / 2491.6 kcal (Lệch 8.1 kcal, 0.32%) · Vi phạm: 0 · Fitness: 99.51")
    _style_run(r_sub, 10, True, GREEN)

    menu_rows = [
        ["Bữa ăn", "Tên món ăn (CSDL 15.929 món)", "Gram gốc", "Gram làm tròn 5g"],
        ["Sáng", "Apple & Cinnamon Filled Crepes", "350.0g", "350g"],
        ["Sáng", "Artisan Bread Loaf", "85.1g", "85g"],
        ["Trưa", "Artichoke Hearts Natural", "350.0g", "350g"],
        ["Trưa", "Chicken, broilers or fryers (thigh)", "26.8g", "25g"],
        ["Tối", "Quail, breast, meat only, raw", "123.4g", "125g"],
        ["Tối", "Albacore Solid With Tuna, Olive Oil", "119.3g", "120g"],
        ["Phụ", "A Non-Alcoholic Drink Mix (Mango)", "157.6g", "160g"],
        ["Phụ", "100% Pure Sesame Tahini", "84.9g", "85g"],
    ]
    align = {0: PP_ALIGN.CENTER, 1: PP_ALIGN.LEFT, 2: PP_ALIGN.RIGHT, 3: PP_ALIGN.CENTER}
    highlight = {(i, 3): (GREEN, True) for i in range(1, len(menu_rows))}
    _table(slide, menu_rows, Inches(6.75), Inches(2.25), Inches(5.8), Inches(3.2),
           col_w=[Inches(0.9), Inches(3.1), Inches(0.9), Inches(0.9)],
           header_color=INDIGO, body_size=9.2, row_h=Inches(0.32),
           highlight=highlight, align_cols=align)

    tb_bot = slide.shapes.add_textbox(Inches(6.8), Inches(5.65), Inches(5.7), Inches(1.1))
    tf_bot = tb_bot.text_frame
    tf_bot.word_wrap = True
    p_b1 = tf_bot.paragraphs[0]
    r_b1 = _add_run(p_b1, "• Quy chuẩn làm tròn 5g: ")
    _style_run(r_b1, 9.5, True, INDIGO2)
    r_b1_desc = _add_run(p_b1, "Loại bỏ số lẻ thập phân, giúp người dùng cân đong khả thi khi chế biến; thẩm định dinh dưỡng sau khi làm tròn (Protein 122.8g, Carbs 312.4g, Fat 82.1g).\n")
    _style_run(r_b1_desc, 9.2, False, INK)

    p_b2 = tf_bot.add_paragraph()
    p_b2.space_before = Pt(2)
    r_b2 = _add_run(p_b2, "• Giới hạn ẩm thực (Edibility): ")
    _style_run(r_b2, 9.5, True, AMBER)
    r_b2_desc = _add_run(p_b2, "Tại Tuần 8 chưa có lớp DishRole nên một số món còn là nguyên liệu (Tahini, thịt sống); đây là cơ sở thực tế để bổ sung ràng buộc ẩm thực ở các tuần sau.")
    _style_run(r_b2_desc, 9.2, False, INK)

    _footer(slide, 5)


# =========================================================================== #
# SLIDE 6: [TUẦN 9] LẬP THỰC ĐƠN 7 NGÀY & DIVERSITY PENALTY (W9-F1)
# =========================================================================== #
def build_slide_6(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 9] Lập Thực Đơn Chu Kỳ 7 Ngày & Cơ Chế Diversity Penalty", "Kế Hoạch Dài Hạn (Tuần 9)")

    f1_path = W9_DIR / "fig_heatmap_nutrition_7days.png"
    if f1_path.exists():
        w, h = _fit_image(f1_path, Inches(7.0), Inches(5.4))
        slide.shapes.add_picture(str(f1_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(7.8), Inches(1.5), Inches(4.9), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(8.05), Inches(1.7), Inches(4.4), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Kỹ Thuật Thực Hiện (Tuần 9)")
    _style_run(r0, 16, True, INDIGO)

    items = [
        ("Mục tiêu mở rộng:", "Chuyển đổi từ đề xuất 1 ngày sang chu kỳ 7 ngày liên tục, giải quyết triệt để bài toán lặp món ăn gây nhàm chán."),
        ("Cơ chế Diversity Penalty:", "Tính toán tỷ lệ trùng lặp món chính giữa các ngày. Phạt nặng nếu tỷ lệ món chính độc nhất dưới ngưỡng 80%."),
        ("Độ bao phủ thực nghiệm (W9-F1):", "Heatmap 7 ngày x 6 dưỡng chất trên Profile P1 cho thấy Năng lượng bám sát mục tiêu hàng ngày (lệch chỉ 2.37%)."),
        ("Tối ưu hóa khẩu phần 5g:", "Tất cả các món trong 7 ngày đều tuân thủ làm tròn khẩu phần bước 5g, dinh dưỡng được thẩm định sau khi làm tròn."),
        ("Kết quả đạt được:", "Tỷ lệ món chính độc nhất đạt 100% trên các phương án tối ưu, không có hiện tượng lặp món chính trong tuần.")
    ]
    for title, desc in items:
        p = tf.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"• {title} ")
        _style_run(rt, 11.5, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 10.5, False, INK)

    _footer(slide, 6)


# =========================================================================== #
# SLIDE 7: [TUẦN 9] ĐỐI CHUẨN 3 HỒ SƠ & TRẢI NGHIỆM UX OPTION A/B/C (W9-F2 & W9-F3)
# =========================================================================== #
def build_slide_7(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 9] Đánh Giá Trên 3 Hồ Sơ Bệnh Lý & Trải Nghiệm Option A/B/C", "Đa Dạng Hóa Hồ Sơ & UX (Tuần 9)")

    f2_path = W9_DIR / "fig_barchart_profiles_p1_p2_p3.png"
    if f2_path.exists():
        w, h = _fit_image(f2_path, Inches(6.0), Inches(2.6))
        slide.shapes.add_picture(str(f2_path), Inches(0.6), Inches(1.5), w, h)

    f3_path = W9_DIR / "fig_radar_options_abc.png"
    if f3_path.exists():
        w, h = _fit_image(f3_path, Inches(6.0), Inches(2.6))
        slide.shapes.add_picture(str(f3_path), Inches(0.6), Inches(4.3), w, h)

    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(7.05), Inches(1.7), Inches(5.4), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Số Liệu Thực Nghiệm Tuần 9 (weekly_summary.csv)")
    _style_run(r0, 16, True, INDIGO)

    points = [
        ("Mở rộng 3 hồ sơ bệnh lý thực tế:", "P1 (Nam 22t, duy trì 2492 kcal) · P2 (Nữ 45t, thừa cân, tiểu đường mô phỏng 1838 kcal, giảm Carbs) · P3 (Nam 55t, tăng huyết áp mô phỏng 1836 kcal, kiểm soát Natri <= 1500mg)."),
        ("Đối chuẩn hiệu năng 7 ngày (W9-F2):", "• P1: Mean Fitness 90.68, lệch calo 2.37%, 0.43 vi phạm/ngày.\n• P2: Mean Fitness 79.27, lệch calo 5.59%, 1.09 vi phạm/ngày.\n• P3: Mean Fitness 88.09, lệch calo 1.84%, 0.60 vi phạm/ngày."),
        ("Đa dạng hóa trải nghiệm người dùng (UX):", "Xây dựng 3 phương án thực đơn A/B/C độc lập cho cùng hồ sơ:\n• Option A (seed 9001): Fitness 90.67, lệch calo 42.3 kcal, 100% món độc nhất.\n• Option B (seed 9002): Fitness 86.55, lệch calo 76.8 kcal, 85.7% món độc nhất.\n• Option C (seed 9003): Fitness 91.35, lệch calo 14.7 kcal, 100% món độc nhất (tối ưu nhất)."),
        ("Trực quan hóa đa chiều (W9-F3):", "Biểu đồ Radar so sánh trực tiếp độ cân bằng dinh dưỡng giữa 3 Option giúp người dùng dễ dàng lựa chọn theo sở thích.")
    ]
    for title, desc in points:
        p = tf.add_paragraph()
        p.space_before = Pt(6)
        rt = _add_run(p, f"★ {title}\n  ")
        _style_run(rt, 11, True, TEAL)
        rd = _add_run(p, desc)
        _style_run(rd, 10.5, False, INK)

    _footer(slide, 7)


# =========================================================================== #
# SLIDE 8: [TUẦN 10] NGHIỆM THU WEB API & WEB UI (ẢNH CHỤP MÀN HÌNH THỰC TẾ)
# =========================================================================== #
def build_slide_8(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 10] Nghiệm Thu Hệ Thống Web API & Giao Diện Người Dùng", "Nền Tảng Triển Khai (Tuần 10)")

    ui_screenshot = W11_DIR / "fig_web_ui_actual_screenshot.png"
    if ui_screenshot.exists():
        w, h = _fit_image(ui_screenshot, Inches(7.2), Inches(5.4))
        slide.shapes.add_picture(str(ui_screenshot), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(8.0), Inches(1.5), Inches(4.7), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(8.25), Inches(1.7), Inches(4.2), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Nghiệm Thu Kỹ Thuật (PR #28)")
    _style_run(r0, 16, True, INDIGO)

    items = [
        ("Công nghệ sử dụng:", "FastAPI, Pydantic v2, Uvicorn server, Chart.js, Vanilla HTML5/CSS3/ES6 (Dark Theme Glassmorphism)."),
        ("Kiến trúc Single-Port:", "Phục vụ đồng thời REST API (/api/*) và static frontend trên cổng 8000, loại bỏ hoàn toàn lỗi CORS và cấu hình proxy."),
        ("6 Endpoints chuẩn hóa:", "GET /health, GET /profiles, POST /targets (tính BMR/TDEE), POST /menu/generate (chạy IDBO 2 tầng), GET /foods, POST /menu/swap (stub 501 minh bạch)."),
        ("Xử lý phi nghẽn:", "two_tier_optimize() bọc qua asyncio.to_thread, Event Loop không bị nghẽn khi tối ưu."),
        ("Quy chuẩn khẩu phần 5g:", "Bảng thực đơn hiển thị minh bạch Gram gốc và Gram làm tròn 5g (portion_g_rounded), tính lại dinh dưỡng chuẩn."),
        ("Trực quan hóa đa chiều:", "Biểu đồ Radar 6 trục dinh dưỡng và thanh tiến độ theo dải dung sai chuẩn (80%–120%).")
    ]
    for title, desc in items:
        p = tf.add_paragraph()
        p.space_before = Pt(6)
        rt = _add_run(p, f"• {title} ")
        _style_run(rt, 11.5, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 10.5, False, INK)

    _footer(slide, 8)


# =========================================================================== #
# SLIDE 9: [TUẦN 11] ĐỐI ĐẦU DBO vs IDBO TRÊN TẬP ĐỘC LẬP (W11-F1)
# =========================================================================== #
def build_slide_9(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 11] Thực Nghiệm Đối Đầu DBO vs IDBO Trên Tập Độc Lập", "Chuẩn Hóa Dữ Liệu (Tuần 11)")

    f1_path = W11_DIR / "fig_fitness_comparison_seed8003_8010.png"
    if f1_path.exists():
        w, h = _fit_image(f1_path, Inches(6.5), Inches(5.4))
        slide.shapes.add_picture(str(f1_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(7.3), Inches(1.5), Inches(5.4), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(7.55), Inches(1.7), Inches(4.9), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Số Liệu Thực Nghiệm (Ngưỡng 0.28)")
    _style_run(r0, 16, True, INDIGO)

    points = [
        ("Dữ liệu thử nghiệm:", "Tập đánh giá độc lập gồm 8 hạt giống (seed 8003–8010), cấu hình chuẩn 100 vòng ngoài, 50 vòng trong, quần thể 20/15 cá thể."),
        ("Tỷ lệ đối đầu:", "IDBO Thắng 5/8 hạt giống (62.5%), DBO Thắng 3/8 hạt giống (37.5%)."),
        ("Điểm Fitness trung bình:", "DBO: 98.9931 ± 0.7918 | IDBO: 99.1590 ± 0.6851. IDBO cải thiện nhẹ trung bình +0.1659 điểm."),
        ("Kiểm định Wilcoxon Signed-Rank:", "Trị thống kê W = 14.0 > W_critical = 3 (n=8, alpha=0.05). Sự khác biệt chưa có ý nghĩa thống kê (p > 0.05)."),
        ("Phân định tập dữ liệu:", "Tập hiệu chỉnh (Calibration seed 8001–8002: IDBO thắng 1, DBO thắng 1) được tách riêng, không gộp vào tập đánh giá độc lập để tránh thiên lệch chọn mẫu.")
    ]
    for title, desc in points:
        p = tf.add_paragraph()
        p.space_before = Pt(8)
        rt = _add_run(p, f"• {title} ")
        _style_run(rt, 12, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 11, False, INK)

    _footer(slide, 9)


# =========================================================================== #
# SLIDE 10: [TUẦN 11] ĐÁNH ĐỔI CHI PHÍ TÍNH TOÁN: EVALUATIONS & RUNTIME (W11-F2)
# =========================================================================== #
def build_slide_10(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 11] Đánh Đổi Tài Nguyên Tính Toán: Số Evaluations & Thời Gian Chạy", "Phân Tích Chi Phí (Tuần 11)")

    f2_path = W11_DIR / "fig_resource_tradeoff_evals_runtime.png"
    if f2_path.exists():
        w, h = _fit_image(f2_path, Inches(7.2), Inches(5.4))
        slide.shapes.add_picture(str(f2_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(8.0), Inches(1.5), Inches(4.7), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(8.25), Inches(1.7), Inches(4.2), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Phân Tích Chi Phí Tính Toán")
    _style_run(r0, 16, True, INDIGO)

    tradeoffs = [
        ("Số lượt tính hàm mục tiêu:", "DBO cố định ở mức 263.870 lượt. IDBO dao động từ 293.826 đến 337.808 lượt (trung bình 313.005 lượt, tăng +18.6%)."),
        ("Thời gian thực thi:", "DBO trung bình 49.39s. IDBO trung bình 56.61s (tăng +14.6% thời gian xử lý)."),
        ("Bản chất chi phí phụ trội:", "Phát sinh từ các đợt đánh giá ứng viên đa dạng (candidate diversity evaluation), đột biến Cauchy và tái khởi động quần thể khi đình trệ."),
        ("Hệ quả khoa học:", "IDBO có điểm số tốt hơn một phần do được cấp thêm ngân sách tính toán. Cần thiết phải triển khai so sánh Budget-Matched (cố định số lần tính hàm mục tiêu).")
    ]
    for t, d in tradeoffs:
        p = tf.add_paragraph()
        p.space_before = Pt(8)
        rt = _add_run(p, f"▲ {t} ")
        _style_run(rt, 12, True, AMBER)
        rd = _add_run(p, d)
        _style_run(rd, 11, False, INK)

    _footer(slide, 10)


# =========================================================================== #
# SLIDE 11: [TUẦN 11] GIẢI MÃ TELEMETRY TẦNG NGOÀI VS TẦNG TRONG (W11-F3)
# =========================================================================== #
def build_slide_11(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 11] Giải Mã Telemetry: Hoạt Động Tầng Ngoài vs Tầng Trong", "Cơ Chế IDBO (Tuần 11)")

    f3_path = W11_DIR / "fig_telemetry_activations.png"
    if f3_path.exists():
        w, h = _fit_image(f3_path, Inches(7.2), Inches(5.4))
        slide.shapes.add_picture(str(f3_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(8.0), Inches(1.5), Inches(4.7), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(8.25), Inches(1.7), Inches(4.2), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Giải Mã Tác Động Từng Tầng")
    _style_run(r0, 16, True, INDIGO)

    tele_pts = [
        ("Tầng ngoài (Chọn tổ hợp món):", "Kích hoạt trung bình 29.5 lần đột biến và 2.9 lần restart. Giúp quần thể thoát bế tắc ở các seed phức tạp như 8005 (69 lần) và 8009 (58 lần)."),
        ("Tầng trong (Khẩu phần gram):", "Kích hoạt cực kỳ tích cực với trung bình ~16.000 lần đột biến và 103 lần restart trên mỗi lần tối ưu hoàn chỉnh."),
        ("Hiện tượng Seed 8007 & 8008:", "Tầng ngoài hoàn toàn không kích hoạt (0 đột biến, 0 restart) nhưng IDBO vẫn cho kết quả khác biệt DBO nhờ các cơ chế phụ trợ hoạt động hiệu quả tại tầng trong."),
        ("Kết luận:", "Cải thiện của IDBO không chỉ đến từ việc chọn món mà còn đến từ khả năng tinh chỉnh khẩu phần gram liên tục ở tầng trong.")
    ]
    for t, d in tele_pts:
        p = tf.add_paragraph()
        p.space_before = Pt(8)
        rt = p.add_run()
        _style_run(rt, 12, True, TEAL)
        rt.text = f"★ {t} "
        rd = p.add_run()
        _style_run(rd, 11, False, INK)
        rd.text = d

    _footer(slide, 11)


# =========================================================================== #
# SLIDE 12: [TUẦN 11] KIỂM SOÁT NGÂN SÁCH CHUNG (BUDGET-MATCHED W11-F4)
# =========================================================================== #
def build_slide_12(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 11] Kiểm Soát Tính Công Bằng Theo Ngân Sách Tính Toán", "Budget-Matched Benchmark (Tuần 11)")

    f4_path = W11_DIR / "fig_budget_matched_smoke.png"
    if f4_path.exists():
        w, h = _fit_image(f4_path, Inches(6.5), Inches(5.4))
        slide.shapes.add_picture(str(f4_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(7.3), Inches(1.5), Inches(5.4), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(7.55), Inches(1.7), Inches(4.9), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Triển Khai & Kiểm Chứng (PR #30)")
    _style_run(r0, 16, True, INDIGO)

    budget_pts = [
        ("Mục tiêu kỹ thuật:", "Áp đặt giới hạn trên max_evaluations dùng chung cho cả DBO và IDBO. Dừng bộ giải ngay khi chạm trần ngân sách."),
        ("Cơ chế theo dõi xuyên suốt:", "Biến _budget_remaining kiểm soát chặt chẽ từ tầng ngoài, các vòng lặp tầng trong đến bước tối ưu cuối cùng (Final Inner)."),
        ("Khóa cấu hình & Truy vết Git:", "Script experiment_week11_budget.py tự động khóa mã băm config_hash và Git commit hash vào config_locked.json."),
        ("Kết quả Smoke Test (W11-F4):", "Thử nghiệm ngân sách 150 evaluations trên seed 8001 và 8002 cho thấy cả DBO và IDBO đều dừng chính xác ở 150/150 lượt, budget_exceeded = False."),
        ("Tính sẵn sàng:", "Sẵn sàng chạy thực nghiệm toàn diện trên tập độc lập với ngân sách chung ở Tuần 12.")
    ]
    for t, d in budget_pts:
        p = tf.add_paragraph()
        p.space_before = Pt(8)
        rt = _add_run(p, f"✓ {t} ")
        _style_run(rt, 12, True, GREEN)
        rd = _add_run(p, d)
        _style_run(rd, 11, False, INK)

    _footer(slide, 12)


# =========================================================================== #
# SLIDE 13: [TUẦN 11] KIẾN TRÚC NGƯỠNG KÉP & ĐẢM BẢO CHẤT LƯỢNG 253 TESTS PASS
# =========================================================================== #
def build_slide_13(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 11] Kiến Trúc Ngưỡng Kép & Nghiệm Thu Chất Lượng Phần Mềm", "Hoàn Thiện Kiến Trúc & Kiểm Thử")

    _card(slide, Inches(0.6), Inches(1.5), Inches(5.9), Inches(5.4))
    tb1 = slide.shapes.add_textbox(Inches(0.85), Inches(1.7), Inches(5.4), Inches(5.0))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    r1 = _add_run(p1, "Kiến Trúc Ngưỡng Kép (Dual Threshold)")
    _style_run(r1, 16, True, INDIGO)

    pts1 = [
        ("Phân tách bản chất không gian:", "Tầng ngoài hoạt động trên không gian nhị phân/rời rạc (chọn món); tầng trong hoạt động trên không gian liên tục (chọn số gram khẩu phần)."),
        ("Cấu trúc TwoTierConfig mới:", "• outer_diversity_threshold = 0.28 (cố định sau kiểm định độc lập).\n• inner_diversity_threshold = None (chưa tự ý gán khi chưa đo lường)."),
        ("Telemetry đo lường tầng trong:", "Thu thập inner_diversity_min_observed và inner_diversity_mean_observed làm cơ sở hiệu chỉnh."),
        ("Bảo đảm backward compatibility:", "Unit test xác nhận solver tương thích hoàn toàn khi chạy độc lập từng ngưỡng.")
    ]
    for t, d in pts1:
        p = tf1.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"★ {t}\n  ")
        _style_run(rt, 11.5, True, TEAL)
        rd = _add_run(p, d)
        _style_run(rd, 10.5, False, INK)

    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb2 = slide.shapes.add_textbox(Inches(7.05), Inches(1.7), Inches(5.4), Inches(5.0))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    r2 = _add_run(p2, "Đảm Bảo Chất Lượng (253/253 Tests PASS)")
    _style_run(r2, 16, True, INDIGO)

    pts2 = [
        ("Kiểm thử tự động 100% PASS:", "253/253 tests PASSED trong 39.08s (pytest v9.1.1, Python 3.12). Phủ kín Core Solver (82), Constraints (45), Realism (36), Schemas (42), Budget (27), API (21)."),
        ("Tính tái lập tuyệt đối (Deterministic):", "Mọi hàm ngẫu nhiên đều nhận seed tường minh, RNG cục bộ (np.random.default_rng(seed))."),
        ("Làm tròn khẩu phần 5g minh bạch:", "Nghiệm liên tục -> Làm tròn 5g -> Giải mã -> Tính lại dinh dưỡng -> Thẩm định validate_menu()."),
        ("Tuân thủ giới hạn y tế (AGENTS.md):", "Không phát ngôn 'an toàn tuyệt đối', phân định rõ ràng số liệu đo đạc và ước tính (sugar_g_estimated).")
    ]
    for t, d in pts2:
        p = tf2.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"🛡 {t}\n  ")
        _style_run(rt, 11.5, True, GREEN)
        rd = _add_run(p, d)
        _style_run(rd, 10.5, False, INK)

    _footer(slide, 13)


# =========================================================================== #
# SLIDE 14: TỔNG KẾT GIAI ĐOẠN TUẦN 8–11 & ĐỊNH HƯỚNG TUẦN 12
# =========================================================================== #
def build_slide_14(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "Tổng Kết Toàn Diện Giai Đoạn Tuần 8–11 & Kế Hoạch Tuần 12", "Tổng Kết & Định Hướng")

    _card(slide, Inches(0.6), Inches(1.5), Inches(5.9), Inches(5.4))
    tb1 = slide.shapes.add_textbox(Inches(0.85), Inches(1.7), Inches(5.4), Inches(5.0))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    r1 = _add_run(p1, "Chuỗi Thành Quả Giai Đoạn Tuần 8 – 11")
    _style_run(r1, 16, True, INDIGO)

    achievements = [
        ("Tuần 8 — Two-Tier Solver & Khẩu phần 5g:", "Xây dựng thành công bộ giải 2 tầng kết hợp chọn món rời rạc từ 15.929 món và tối ưu gram liên tục, quy chuẩn làm tròn 5g thực tế chế biến."),
        ("Tuần 9 — Lập thực đơn 7 ngày đa hồ sơ:", "Triển khai chu kỳ 7 ngày trên 3 hồ sơ bệnh lý (P1, P2, P3), tích hợp cơ chế Diversity Penalty đạt 100% món chính độc nhất, cung cấp 3 Option UX A/B/C."),
        ("Tuần 10 — Hệ thống Web API & UI:", "Đưa solver lên nền tảng Web với kiến trúc Single-port FastAPI, 6 REST endpoints, giao diện Dark Glassmorphism, Radar chart 6 trục và bảng thực đơn 5g."),
        ("Tuần 11 — Chuẩn hóa độc lập & Budget-Matched:", "Phân định minh bạch tập độc lập (seed 8003–8010), kiểm định Wilcoxon, phân tích chi phí Evals, kiến trúc Dual Threshold, cài đặt Budget-Matched, 253/253 tests pass.")
    ]
    for t, d in achievements:
        p = tf1.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"✓ {t}\n  ")
        _style_run(rt, 11, True, GREEN)
        rd = _add_run(p, d)
        _style_run(rd, 10, False, INK)

    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb2 = slide.shapes.add_textbox(Inches(7.05), Inches(1.7), Inches(5.4), Inches(5.0))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    r2 = _add_run(p2, "Kế Hoạch Nghiên Cứu Trọng Tâm Tuần 12")
    _style_run(r2, 16, True, INDIGO)

    plans = [
        ("1. Benchmark Budget-Matched Đầy Đủ:", "Chạy benchmark toàn diện trên tập seed độc lập với ngân sách chung (ví dụ 260.000 evaluations) để trả lời dứt điểm câu hỏi về tính công bằng tài nguyên giữa DBO và IDBO."),
        ("2. Hiệu Chỉnh Ngưỡng Đa Dạng Tầng Trong:", "Sử dụng dữ liệu quan sát inner_diversity_mean để thiết lập và thử nghiệm ngưỡng inner_diversity_threshold phù hợp."),
        ("3. Kiểm Thử Đầu Cuối (E2E Web Test):", "Thực hiện tự động hóa kiểm thử luồng Người dùng -> UI Web -> API -> Two-Tier Solver -> Hiển thị thực đơn."),
        ("4. Hoàn Thiện Bản Thảo Khóa Luận Tốt Nghiệp:", "Tổng hợp toàn bộ các kết quả thực nghiệm từ Tuần 1 đến Tuần 12 vào báo cáo Word chính thức của đề tài.")
    ]
    for t, d in plans:
        p = tf2.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"★ {t}\n  ")
        _style_run(rt, 11, True, AMBER)
        rd = _add_run(p, d)
        _style_run(rd, 10, False, INK)

    _footer(slide, 14)


def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    print("=" * 80)
    print("XÂY DỰNG SLIDE BÁO CÁO TỔNG HỢP TUẦN 8 – 9 – 10 – 11 (14 SLIDES)")
    print("=" * 80)

    build_slide_1(prs)
    build_slide_2(prs)
    build_slide_3(prs)
    build_slide_4(prs)
    build_slide_5(prs)
    build_slide_6(prs)
    build_slide_7(prs)
    build_slide_8(prs)
    build_slide_9(prs)
    build_slide_10(prs)
    build_slide_11(prs)
    build_slide_12(prs)
    build_slide_13(prs)
    build_slide_14(prs)

    prs.save(str(OUT_PPTX_MERGED))
    prs.save(str(OUT_PPTX_USER_TAGGED))
    print(f"\n[THÀNH CÔNG] Đã lưu {len(prs.slides)} slide tại:")
    print(f" -> {OUT_PPTX_MERGED}")
    print(f" -> {OUT_PPTX_USER_TAGGED}")
    print(f"Kích thước file: {OUT_PPTX_USER_TAGGED.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
