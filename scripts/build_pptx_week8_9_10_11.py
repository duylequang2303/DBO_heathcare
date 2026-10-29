"""Dựng slide báo cáo tổng hợp Tuần 8 – 9 – 10 – 11 (DBO / IDBO Healthcare Menu Optimization).

Đề tài: CNTT-KLCN142 — Trường Đại học Công Thương TP.HCM (HUIT)
Thực hiện: Lê Quang Duy (Nhóm trưởng), Hồ Trung Cương, Đặng Nguyễn Minh Đăng.
Giảng viên hướng dẫn: ThS. Đinh Nguyễn Trọng Nghĩa.

Chuỗi tiến độ gộp 4 tuần trọng tâm (14 slide chuẩn học thuật 16:9, trung thực khoa học 100%):
- Slide 1: Bìa báo cáo tổng quan Tuần 8 – 9 – 10 – 11
- Slide 2: [Tổng quan] Lộ trình phát triển & Bước chuyển kiến trúc qua 4 tuần (Tuần 8 -> 11)
- Slide 3: [Tuần 8] Kiến trúc Two-Tier Solver & Bể ứng viên thực phẩm (15.929 gốc -> 13.709 sạch)
- Slide 4: [Tuần 8] Thực nghiệm 10 Runs đối chuẩn & Bài học ẩm thực từ nghịch lý P1
- Slide 5: [Tuần 8] Phân tích thực đơn Seed 8003 & Sự cần thiết của lọc vai trò ẩm thực (DishRole)
- Slide 6: [Tuần 9] Lập thực đơn chu kỳ 7 ngày & Cơ chế Diversity Penalty (Heatmap W9-F1)
- Slide 7: [Tuần 9] Đánh giá đa hồ sơ (P1 khỏe mạnh, P2/P3 mô phỏng) & Thẩm định Natri/Đường
- Slide 8: [Tuần 10] Nghiệm thu Hệ thống Web API & Giao diện Người dùng Web UI (Ảnh chụp thực tế)
- Slide 9: [Tuần 11] Thực nghiệm đối đầu DBO vs IDBO trên tập độc lập Seed 8003–8010 (W11-F1)
- Slide 10: [Tuần 11] Đánh đổi chi phí tính toán: Lượt Evaluations & Thời gian chạy (W11-F2)
- Slide 11: [Tuần 11] Giải mã Telemetry: Tác động tầng ngoài vs tầng trong & Hiện tượng Seed 8008 (W11-F3)
- Slide 12: [Tuần 11] Kiểm soát ngân sách tính toán chung (Budget-Matched Diagnostic, W11-F4)
- Slide 13: [Tuần 11] Kiến trúc Ngưỡng kép (Dual Threshold) & Nghiệm thu chất lượng 265/265 Tests PASS
- Slide 14: [Tổng kết] Toàn diện giai đoạn Tuần 8–11 & Kế hoạch nghiên cứu thực nghiệm Tuần 12
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
    _style_run(r_t, 20.5, True, INDIGO)

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


def _table(slide, rows, l, t, w, h, col_w, header_color, body_size=9.2,
           row_h=None, highlight=None, header_size=10.5, align_cols=None):
    n_row, n_col = len(rows), len(rows[0])
    shape = slide.shapes.add_table(n_row, n_col, l, t, w, h)
    tbl = shape.table
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = cw
    if row_h is not None:
        for r in range(n_row):
            tbl.rows[r].height = row_h if r else Inches(0.38)
    highlight = highlight or {}
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            if align_cols is not None and c in align_cols:
                p.alignment = align_cols[c]
            else:
                p.alignment = PP_ALIGN.LEFT if c in (0, 1) else PP_ALIGN.CENTER
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
    r2 = _add_run(p2, "BÁO CÁO TIẾN ĐỘ TỔNG HỢP GIAI ĐOẠN TUẦN 8 – TUẦN 9 – TUẦN 10 – TUẦN 11\n(TỐI ƯU 2 TẦNG · KẾ HOẠCH 7 NGÀY · HỆ THỐNG WEB API · ĐỐI CHUẨN BUDGET-MATCHED)")
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
         "Two-Tier Solver & Khẩu Phần 5g",
         "• Chuyển từ định lượng cố định sang chọn món rời rạc từ CSDL 13.709 món sạch.\n"
         "• Tầng 1 (Outer): Chọn tổ hợp món rời rạc z theo 4 bữa.\n"
         "• Tầng 2 (Inner): Tối ưu khẩu phần gram liên tục x ∈ bounds.\n"
         "• Làm tròn khẩu phần bước 5g thực tế chế biến.\n"
         "• Bài học Case Study P1: Hàm mục tiêu thuần đa lượng là 'mù quáng', dính thịt chim cút sống & 85g sốt mè.",
         INDIGO, LIGHT),
        ("TUẦN 9: KẾ HOẠCH 7 NGÀY",
         "Diversity Penalty & Thẩm Định",
         "• Lập thực đơn chu kỳ 7 ngày, giải quyết dứt điểm lặp món.\n"
         "• Cơ chế Diversity Penalty cửa sổ trượt (100% món chính độc nhất).\n"
         "• Đánh giá 3 hồ sơ: P1 (Nam khỏe mạnh, 2492 kcal), P2 (tiểu đường mô phỏng), P3 (tăng huyết áp mô phỏng).\n"
         "• Thẩm định minh bạch: 32/210 ngày vượt trần natri 3000mg; phân biệt rõ dữ liệu đo & proxy đường.",
         TEAL, LIGHT),
        ("TUẦN 10: WEB API & UI",
         "FastAPI Backend & Glassmorphism",
         "• Đóng gói solver thành Web API RESTful hiệu năng cao.\n"
         "• Kiến trúc Single-port phục vụ cả REST API & Static UI trên cổng 8000, triệt tiêu lỗi CORS.\n"
         "• 6 endpoints chuẩn hóa, bọc solver qua asyncio phi nghẽn.\n"
         "• Giao diện Dark Glassmorphism, Radar chart 6 trục dinh dưỡng và bảng thực đơn 5g minh bạch.",
         AMBER, CREAM),
        ("TUẦN 11: CHUẨN HÓA KHOA HỌC",
         "Budget-Matched & Dual Threshold",
         "• Tách riêng tập hiệu chỉnh & tập kiểm định độc lập (seed 8003–8010).\n"
         "• Báo cáo trung thực: IDBO thắng 5/8 seed (+0.1659 điểm), Wilcoxon p > 0.05 (chưa có ý nghĩa thống kê).\n"
         "• Đánh đổi tài nguyên: IDBO tốn +18.6% evals và +14.6% runtime.\n"
         "• Chốt chặn ngân sách chung (Budget-Matched) & Hoàn thiện Ngưỡng kép (Dual Threshold) · 270/270 tests PASS.",
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
        _style_run(r0, 12.0, True, accent_col)

        p1 = tf.add_paragraph()
        p1.space_before = Pt(3)
        r1 = _add_run(p1, sub)
        _style_run(r1, 9.8, True, INK)

        sep = tf.add_paragraph()
        sep.space_before = Pt(5)
        r_sep = _add_run(sep, "—" * 22)
        _style_run(r_sep, 8, False, LINE)

        p2 = tf.add_paragraph()
        p2.space_before = Pt(5)
        r2 = _add_run(p2, body)
        _style_run(r2, 9.3, False, INK)

    _footer(slide, 2)


# =========================================================================== #
# SLIDE 3: [TUẦN 8] KIẾN TRÚC TỐI ƯU 2 TẦNG & BỂ ỨNG VIÊN THỰC PHẨM
# =========================================================================== #
def build_slide_3(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 8] Kiến Trúc Tối Ưu Hóa 2 Tầng & Chuẩn Hóa Bể Ứng Viên Thực Phẩm", "Thiết Kế Giải Thuật (Tuần 8)")

    # Cột trái: Kiến trúc 2 tầng
    _card(slide, Inches(0.6), Inches(1.5), Inches(5.9), Inches(5.4))
    tb1 = slide.shapes.add_textbox(Inches(0.85), Inches(1.65), Inches(5.4), Inches(5.1))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    r0 = _add_run(p0, "Kiến Trúc Two-Tier Solver (Mixed-Integer)")
    _style_run(r0, 15.0, True, INDIGO)

    outer_inner_points = [
        ("Tầng 1 — Outer Solver (Chọn tổ hợp món rời rạc):",
         "• Vector cá thể bọ hung: z = (z₁, ..., z₈) với z_i ∈ [0, 1).\n"
         "• Ánh xạ chỉ mục Pool: idx_i = floor(z_i × |Pool_i|), giải mã ra tập food_ids.\n"
         "• Cơ cấu 4 bữa ăn (meal_counts): Sáng (2 món), Trưa (2 món), Tối (2 món), Phụ (2 món).\n"
         "• Độ thích nghi của z: Chính là fitness tốt nhất đạt được sau khi chạy tầng 2 trên tổ hợp món đó."),
        ("Tầng 2 — Inner Solver (Tối ưu khẩu phần gram liên tục):",
         "• Vector liên tục x = (x₁, ..., x₈) đại diện cho số gram từng món ăn trong thực đơn.\n"
         "• Thuật toán tối ưu hóa bám sát mục tiêu Năng lượng & Tỷ lệ đa lượng (Carbs / Protein / Fat).\n"
         "• Thời gian giải nhanh: 0.17s – 0.30s cho mỗi lần chạy Inner Solver."),
        ("Quy chuẩn làm tròn khẩu phần 5g thực tế chế biến:",
         "• module portion_utils: round_portions(x, step=5) loại bỏ hoàn toàn số lẻ thập phân.\n"
         "• Dinh dưỡng được tính toán lại và thẩm định validate_menu() trên chính nghiệm đã làm tròn.")
    ]
    for title, desc in outer_inner_points:
        p = tf1.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"★ {title}\n")
        _style_run(rt, 10.5, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 9.3, False, INK)

    # Cột phải: Bể ứng viên và đối chiếu số liệu
    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb2 = slide.shapes.add_textbox(Inches(7.05), Inches(1.65), Inches(5.4), Inches(5.1))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    p2 = tf2.paragraphs[0]
    r2 = _add_run(p2, "Chuẩn Hóa Bể Ứng Viên Thực Phẩm (Toán Học Khớp 100%)")
    _style_run(r2, 15.0, True, INDIGO)

    pool_points = [
        ("CSDL gốc 15.929 món -> CSDL sạch 13.709 món:",
         "Hợp nhất từ USDA (13.224) và Viện Dinh Dưỡng QG Việt Nam (485). Đã loại bỏ 2.220 nguyên liệu thô công nghiệp, phụ gia, men, shortening không dùng trực tiếp."),
        ("Phân chia 3 Bể Ứng Viên theo Bữa (Meal-type Pools) — Tổng đúng 13.709 món:",
         "• Bể Bữa Sáng (Breakfast Pool): 1.763 món (ngũ cốc, bánh mì, cháo, điểm tâm...).\n"
         "• Bể Bữa Phụ (Snack Pool): 1.742 món (trái cây, sữa chua, các loại hạt, sinh tố...).\n"
         "• Bể Bữa Chính Trưa & Tối (All / Main Pool): 10.204 món (thịt, cá, rau củ, canh xào...).\n"
         "→ Phép cộng chuẩn xác: 1.763 + 1.742 + 10.204 = 13.709 món (khớp 100% CSDL sạch!)."),
        ("Phân loại theo Vai Trò Ẩm Thực (DishRole) đưa vào thực đơn người dùng:",
         "• Món đạm chính (Main Protein): 3.833 món | Tinh bột / Năng lượng (Staple): 2.179 món\n"
         "• Rau củ (Vegetable): 1.047 món | Canh / Súp (Soup): 190 món\n"
         "• Trái cây / Bữa phụ (Fruit/Snack): 1.341 món\n"
         "• Nguyên liệu thô phụ trợ (Raw/Ingredient): 5.119 món (bị loại khỏi user-facing menu).\n"
         "→ Phép cộng: 3.833 + 2.179 + 1.047 + 190 + 1.341 + 5.119 = 13.709 món!")
    ]
    for title, desc in pool_points:
        p = tf2.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"• {title}\n")
        _style_run(rt, 10.5, True, TEAL)
        rd = _add_run(p, desc)
        _style_run(rd, 9.3, False, INK)

    _footer(slide, 3)


# =========================================================================== #
# SLIDE 4: [TUẦN 8] THỰC NGHIỆM ĐỐI CHUẨN 10 RUNS & BÀI HỌC ẨM THỰC
# =========================================================================== #
def build_slide_4(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 8] Kết Quả Đối Chuẩn 10 Runs Độc Lập & Bài Học Khoa Học Ẩm Thực", "Đối Chuẩn Giải Thuật (Tuần 8)")

    f1_path = W8_DIR / "fig_convergence_2tier_p1.png"
    if f1_path.exists():
        w, h = _fit_image(f1_path, Inches(6.0), Inches(2.6))
        slide.shapes.add_picture(str(f1_path), Inches(0.6), Inches(1.5), w, h)

    f2_path = W8_DIR / "fig_boxplot_2tier_p1.png"
    if f2_path.exists():
        w, h = _fit_image(f2_path, Inches(6.0), Inches(2.6))
        slide.shapes.add_picture(str(f2_path), Inches(0.6), Inches(4.3), w, h)

    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(7.05), Inches(1.65), Inches(5.4), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Số Liệu Thực Nghiệm & Bài Học Khoa Học (Tuần 8)")
    _style_run(r0, 15.0, True, INDIGO)

    points = [
        ("Cấu hình đối chuẩn 10 runs (Profile P1, Seeds 8001–8010):",
         "Đối tượng thử nghiệm: P1 (Nam 22 tuổi, khỏe mạnh, mục tiêu 2491.6 kcal). Cấu hình: 25 vòng lặp ngoài, 25 vòng lặp trong, quần thể 20/15 cá thể."),
        ("Kết quả hiệu năng toán học:",
         "• Best Fitness: 99.5106 tại seed 8003; sai lệch calo chỉ 8.1 kcal (0.32%).\n"
         "• Mean Fitness: 98.2148 ± 1.0663 | Worst Fitness: 96.3425.\n"
         "• Tỷ lệ vi phạm ràng buộc đa lượng: 0.0 / 10 runs (100% hợp lệ). Thời gian chạy: 7.6s – 8.2s."),
        ("Nhận định từ đồ thị W8-F1 (Hội tụ) & W8-F2 (Boxplot):",
         "• Đường cong hội tụ tầng ngoài giảm nhanh và ổn định chỉ sau ~10 vòng lặp.\n"
         "• Phân phối Best Fitness tập trung quanh trung vị 98.4, dải biến thiên hẹp [96.3, 99.5], không bị suy biến nghiệm."),
        ("Bài học khoa học then chốt — Nghịch lý ẩm thực Tuần 8:",
         "Mặc dù điểm số toán học đạt gần tuyệt đối (99.51), khi bóc tách từng món ăn thực tế của Case Study P1, hệ thống lại chọn ra thịt chim cút sống và 85g sốt mè Tahini ăn riêng!\n"
         "→ Kết luận: Hàm mục tiêu thuần đa lượng là 'mù quáng' (Blind Macro Objective). Thuật toán metaheuristic tối ưu toán học thuần túy sẽ tìm ra khe hở bằng cách chọn nguyên liệu thô đậm đặc dinh dưỡng miễn sao khớp số. Đây là tiền đề khoa học bắt buộc phải phát triển lớp DishRole ở các tuần sau.")
    ]
    for title, desc in points:
        p = tf.add_paragraph()
        p.space_before = Pt(6)
        rt = _add_run(p, f"• {title}\n  ")
        _style_run(rt, 10.5, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 9.3, False, INK)

    _footer(slide, 4)


# =========================================================================== #
# SLIDE 5: [TUẦN 8] PHÂN TÍCH THỰC ĐƠN SEED 8003 & SỰ CẦN THIẾT CỦA DISHROLE
# =========================================================================== #
def build_slide_5(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 8] Phân Tích Thực Đơn Seed 8003 & Nhu Cầu Lọc Vai Trò Ẩm Thực", "Case Study & Thực Tế Ẩm Thực (Tuần 8)")

    f3_path = W8_DIR / "fig_radar_nutrition_p1.png"
    if f3_path.exists():
        w, h = _fit_image(f3_path, Inches(5.7), Inches(5.4))
        slide.shapes.add_picture(str(f3_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(6.5), Inches(1.5), Inches(6.2), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(6.7), Inches(1.65), Inches(5.8), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Thực Đơn Tối Ưu Cho Profile P1 (Seed 8003, Fitness 99.51)")
    _style_run(r0, 14.5, True, INDIGO)

    p_sub = tf.add_paragraph()
    p_sub.space_before = Pt(2)
    r_sub = _add_run(p_sub, "Calo: 2483.6 / 2491.6 kcal (Lệch 8.1 kcal, 0.32%) · Vi phạm macro: 0 · Nhưng bộc lộ lỗi ẩm thực nghiêm trọng:")
    _style_run(r_sub, 9.5, True, AMBER)

    menu_rows = [
        ["Bữa ăn", "Tên món ăn (CSDL gốc)", "Gram gốc", "Làm tròn", "Đánh giá ẩm thực"],
        ["Sáng", "Apple & Cinnamon Filled Crepes", "350.0g", "350g", "Hợp lý (Món ăn sáng)"],
        ["Sáng", "Artisan Bread Loaf", "85.1g", "85g", "Hợp lý (Bánh mì)"],
        ["Trưa", "Artichoke Hearts Natural", "350.0g", "350g", "Hợp lý (Rau củ)"],
        ["Trưa", "Chicken, broilers or fryers (thigh)", "26.8g", "25g", "Quá ít (chỉ 25g thịt gà kho)"],
        ["Tối", "Quail, breast, meat only, raw", "123.4g", "125g", "THỊT SỐNG (BẤT HỢP LÝ)"],
        ["Tối", "Albacore Solid With Tuna, Olive Oil", "119.3g", "120g", "Hợp lý (Cá ngừ đóng hộp)"],
        ["Phụ", "A Non-Alcoholic Drink Mix (Mango)", "157.6g", "160g", "Hợp lý (Đồ uống)"],
        ["Phụ", "100% Pure Sesame Tahini", "84.9g", "85g", "SỐT MÈ ĂN RIÊNG 85G (THÔ)"],
    ]
    align = {0: PP_ALIGN.CENTER, 1: PP_ALIGN.LEFT, 2: PP_ALIGN.RIGHT, 3: PP_ALIGN.CENTER, 4: PP_ALIGN.LEFT}
    highlight = {
        (5, 4): (RED, True),
        (8, 4): (RED, True),
        (4, 4): (AMBER, True),
        (5, 1): (RED, True),
        (8, 1): (RED, True),
    }
    _table(slide, menu_rows, Inches(6.6), Inches(2.15), Inches(6.0), Inches(2.95),
           col_w=[Inches(0.65), Inches(2.25), Inches(0.75), Inches(0.70), Inches(1.65)],
           header_color=INDIGO, body_size=8.5, row_h=Inches(0.28),
           highlight=highlight, align_cols=align)

    tb_bot = slide.shapes.add_textbox(Inches(6.65), Inches(5.25), Inches(5.9), Inches(1.4))
    tf_bot = tb_bot.text_frame
    tf_bot.word_wrap = True
    tf_bot.margin_left = tf_bot.margin_right = tf_bot.margin_top = tf_bot.margin_bottom = 0

    p_b1 = tf_bot.paragraphs[0]
    r_b1 = _add_run(p_b1, "★ Vì sao thịt sống và 85g sốt mè được chọn? ")
    _style_run(r_b1, 9.5, True, RED)
    r_b1_desc = _add_run(p_b1, "Thịt cút sống và sốt Tahini có mật độ Protein/Fat cực cao, giúp bộ giải khớp nhanh chỉ số calo mà không cần quan tâm đến khả năng chế biến hay độ ngon miệng.\n")
    _style_run(r_b1_desc, 8.8, False, INK)

    p_b2 = tf_bot.add_paragraph()
    p_b2.space_before = Pt(2)
    r_b2 = _add_run(p_b2, "★ Giải pháp kiến trúc bắt buộc: ")
    _style_run(r_b2, 9.5, True, GREEN)
    r_b2_desc = _add_run(p_b2, "1) Khử sạch 2.220 nguyên liệu thô khỏi CSDL; 2) Phân loại cấu trúc bữa ăn theo DishRole (Staple + Main Protein + Veg/Soup); 3) Khóa cận khẩu phần theo vai trò (ROLE_PORTION_BOUNDS: Đạm 60-180g, Cơm 100-250g) triển khai ở Tuần 9–11.")
    _style_run(r_b2_desc, 8.8, False, INK)

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
    tb = slide.shapes.add_textbox(Inches(8.05), Inches(1.65), Inches(4.4), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Kỹ Thuật Thực Hiện (Tuần 9)")
    _style_run(r0, 15.5, True, INDIGO)

    items = [
        ("Mục tiêu mở rộng & Diversity Penalty cửa sổ 2 ngày:",
         "Chuyển từ tối ưu 1 ngày sang chu kỳ 7 ngày liên tục. Cơ chế Diversity Penalty phạt nặng nếu tỷ lệ món chính độc nhất < 80%, giúp 100% kế hoạch tối ưu không bị lặp món chính."),
        ("Độ bám sát Năng lượng & Đa lượng (Heatmap W9-F1):",
         "Trên hồ sơ P1, năng lượng bám sát mục tiêu 2.492 kcal (độ lệch calo trung bình toàn bộ runs là 0.63%, kế hoạch tiêu biểu chỉ lệch 0.90%). Đạm, tinh bột, chất béo và chất xơ đạt chuẩn khuyến nghị DRI."),
        ("Chuẩn hóa khẩu phần bước 5g suốt 7 ngày:",
         "Tất cả các món đều được làm tròn theo bước 5g thực tế chế biến; toàn bộ dinh dưỡng được tái tính toán và thẩm định tự động trên nghiệm đã làm tròn."),
        ("Khống chế hàm lượng Natri hiệu quả trên Heatmap:",
         "• Quan sát biểu đồ: Toàn bộ 7 ngày đều có mức Natri dao động sinh lý an toàn từ 1.139 mg (50%) đến 2.258 mg (98%), trung bình tuần đạt 1.905 mg/ngày, không có ngày nào vượt trần 2.300 mg.\n"
         "• Kết quả nâng cấp: Cơ chế khóa trần Natri tự động đã giúp bộ giải DBO/IDBO định lượng khẩu phần hài hòa, loại bỏ hoàn toàn các món mặn quá mức mà vẫn đạt điểm tối ưu calo/macro (Fitness 95.66 – 99.60).")
    ]
    for title, desc in items:
        p = tf.add_paragraph()
        p.space_before = Pt(5)
        rt = _add_run(p, f"• {title}\n  ")
        _style_run(rt, 10.0, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 8.5, False, INK)

    _footer(slide, 6)


# =========================================================================== #
# SLIDE 7: [TUẦN 9] ĐỐI CHUẨN 3 HỒ SƠ & THẨM ĐỊNH NATRI / ĐƯỜNG MINH BẠCH
# =========================================================================== #
def build_slide_7(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 9] Đánh Giá Đa Hồ Sơ & Báo Cáo Thẩm Định Natri / Đường", "Đa Dạng Hóa Hồ Sơ & Thẩm Định Số Liệu")

    f2_path = W9_DIR / "fig_barchart_profiles_p1_p2_p3.png"
    if f2_path.exists():
        w, h = _fit_image(f2_path, Inches(6.0), Inches(2.6))
        slide.shapes.add_picture(str(f2_path), Inches(0.6), Inches(1.5), w, h)

    f3_path = W9_DIR / "fig_radar_options_abc.png"
    if f3_path.exists():
        w, h = _fit_image(f3_path, Inches(6.0), Inches(2.6))
        slide.shapes.add_picture(str(f3_path), Inches(0.6), Inches(4.3), w, h)

    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(7.05), Inches(1.65), Inches(5.4), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Số Liệu Thực Nghiệm & Thẩm Định Minh Bạch")
    _style_run(r0, 15.0, True, INDIGO)

    points = [
        ("Đặc tính 3 hồ sơ người dùng thử nghiệm:",
         "• Profile P1: Nam 22 tuổi, thể trạng bình thường (mục tiêu duy trì 2.491,6 kcal).\n"
         "• Profile P2: Nữ 45 tuổi, thừa cân (mục tiêu 1.179,6 kcal, yêu cầu khống chế tinh bột).\n"
         "• Profile P3: Nam 55 tuổi (mục tiêu 1.836,0 kcal, yêu cầu kiểm soát muối Natri <= 1.500 mg)."),
        ("Mức độ bám sát Năng lượng (Calo):",
         "Năng lượng các bữa ăn bám sát mục tiêu dinh dưỡng đề ra trong dải dung sai ±10%. Độ lệch calo trung bình thực nghiệm: P1 lệch 0.42%, P2 lệch 1.30%, P3 lệch 1.22%."),
        ("Khảo sát & Kiểm soát hàm lượng Natri:",
         "• Đánh giá 210 ngày mô phỏng sau khi tích hợp trần Natri: Tỷ lệ tuân thủ đạt 98.6% (207/210 ngày <= 3.000 mg). Mức Natri trung bình toàn hệ thống giảm còn 1.361,7 mg/ngày.\n"
         "• Hiệu quả thực nghiệm: Cơ chế khóa trần Natri tự động cho mọi hồ sơ (P1 <= 2.300 mg, P3 <= 1.500 mg) đã loại bỏ triệt để các đợt tăng vọt natri, bảo đảm an toàn dinh dưỡng."),
        ("Nguồn dữ liệu Đường trong thực phẩm:",
         "Do cơ sở dữ liệu USDA/FDC chưa có trường tổng đường tự do, hệ thống sử dụng công thức suy diễn ước lượng từ carbohydrate (15% carbs). Đề tài ghi nhận đây là giới hạn dữ liệu và cần cập nhật thêm số đo trực tiếp từ phòng thí nghiệm."),
        ("Trải nghiệm đa dạng hóa thực đơn (UX Option A/B/C):",
         "Hệ thống sinh đồng thời 3 phương án thực đơn 7 ngày độc lập (biểu đồ W9-F3 Radar), giúp người dùng linh hoạt lựa chọn theo thói quen ăn uống.")
    ]
    for title, desc in points:
        p = tf.add_paragraph()
        p.space_before = Pt(5)
        rt = _add_run(p, f"★ {title}\n  ")
        _style_run(rt, 10.2, True, TEAL)
        rd = _add_run(p, desc)
        _style_run(rd, 9.0, False, INK)

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
    tb = slide.shapes.add_textbox(Inches(8.25), Inches(1.65), Inches(4.2), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Nghiệm Thu Kỹ Thuật (PR #28)")
    _style_run(r0, 15.5, True, INDIGO)

    items = [
        ("Công nghệ sử dụng:",
         "FastAPI, Pydantic v2, Uvicorn server, Chart.js, Vanilla HTML5/CSS3/ES6 (Dark Theme Glassmorphism hiện đại)."),
        ("Kiến trúc Single-Port 8000:",
         "Phục vụ đồng thời REST API (/api/*) và static frontend trên cùng một cổng 8000, loại bỏ hoàn toàn lỗi CORS và đơn giản hóa cấu hình triển khai."),
        ("6 Endpoints chuẩn hóa:",
         "• GET /health: Kiểm tra trạng thái hệ thống.\n"
         "• GET /profiles: Danh sách hồ sơ mẫu.\n"
         "• POST /targets: Tính BMR & TDEE theo Mifflin-St Jeor.\n"
         "• POST /menu/generate: Chạy Two-Tier Solver sinh thực đơn.\n"
         "• GET /foods: Tra cứu CSDL thực phẩm.\n"
         "• POST /menu/swap: Stub 501 minh bạch cho tính năng đổi món."),
        ("Xử lý phi nghẽn async:",
         "two_tier_optimize() được bọc qua asyncio.to_thread, Event Loop không bị nghẽn khi có nhiều yêu cầu đồng thời."),
        ("Bảng thực đơn & Khẩu phần 5g minh bạch:",
         "Hiển thị rõ ràng Gram gốc và Gram làm tròn 5g (portion_g_rounded), tính toán lại toàn bộ dinh dưỡng sau làm tròn."),
        ("Trực quan hóa đa chiều:",
         "Biểu đồ Radar 6 trục dinh dưỡng và thanh tiến độ theo dải dung sai chuẩn (80%–120%).")
    ]
    for title, desc in items:
        p = tf.add_paragraph()
        p.space_before = Pt(5)
        rt = _add_run(p, f"• {title} ")
        _style_run(rt, 10.5, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 9.3, False, INK)

    _footer(slide, 8)


# =========================================================================== #
# SLIDE 9: [TUẦN 11] ĐỐI ĐẦU DBO vs IDBO TRÊN TẬP ĐỘC LẬP (W11-F1)
# =========================================================================== #
def build_slide_9(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 11] Thực Nghiệm Đối Đầu DBO vs IDBO Trên Tập Độc Lập", "Chuẩn Hóa Thực Nghiệm Đối Chuẩn (Tuần 11)")

    f1_path = W11_DIR / "fig_fitness_comparison_seed8003_8010.png"
    if f1_path.exists():
        w, h = _fit_image(f1_path, Inches(6.5), Inches(5.4))
        slide.shapes.add_picture(str(f1_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(7.3), Inches(1.5), Inches(5.4), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(7.55), Inches(1.65), Inches(4.9), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Số Liệu Thực Nghiệm Trung Thực (Ngưỡng 0.28)")
    _style_run(r0, 15.0, True, INDIGO)

    points = [
        ("Thiết kế 2 tập độc lập (Independent Evaluation):",
         "• Tập hiệu chỉnh (Calibration Seeds 8001–8002): Rà soát thăm dò ngưỡng ứng viên 0.28 (IDBO thắng 1, DBO thắng 1).\n"
         "• Tập đánh giá mù độc lập (Hold-out Seeds 8003–8010, N=8): Đánh giá khách quan mà không thay đổi bất kỳ tham số nào."),
        ("Tỷ lệ đối đầu trên tập độc lập:",
         "IDBO Thắng 5/8 hạt giống (62.5%), DBO Thắng 3/8 hạt giống (37.5%)."),
        ("Điểm Fitness trung bình:",
         "• DBO: 98.9931 ± 0.7918 | IDBO: 99.1590 ± 0.6851.\n"
         "• Chênh lệch paired trung bình: +0.1659 điểm (trung vị +0.1115 điểm)."),
        ("Kiểm định thống kê Wilcoxon Signed-Rank:",
         "Trị thống kê W = 14.0 > W_critical = 3 (N=8, α=0.05, p = 0.640625 > 0.05).\n"
         "→ Kết luận khoa học: Khác biệt CHƯA ĐẠT MỨC Ý NGHĨA THỐNG KÊ ở ngưỡng α=0.05."),
        ("Hiện tượng Seed 8008 (IDBO thua DBO 1.05 điểm):",
         "Tại Seed 8008, DBO đạt 99.4844 nhưng IDBO chỉ đạt 98.4347 (thua 1.05 điểm). Nguyên nhân: Các cú hích đột biến ngẫu nhiên ở tầng trong khi bế tắc đã vô tình phá vỡ một nghiệm tốt mà DBO giữ được.\n"
         "→ Luận điểm khoa học: Đột biến không phải lúc nào cũng tốt; chứng minh sự cần thiết phải kiểm soát ngân sách chung (Budget-Matched) và Ngưỡng kép (Dual Threshold).")
    ]
    for title, desc in points:
        p = tf.add_paragraph()
        p.space_before = Pt(6)
        rt = _add_run(p, f"• {title}\n  ")
        _style_run(rt, 10.5, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 9.3, False, INK)

    _footer(slide, 9)


# =========================================================================== #
# SLIDE 10: [TUẦN 11] ĐÁNH ĐỔI CHI PHÍ TÍNH TOÁN: EVALUATIONS & RUNTIME (W11-F2)
# =========================================================================== #
def build_slide_10(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 11] Đánh Đổi Tài Nguyên Tính Toán: Số Evaluations & Thời Gian Chạy", "Phân Tích Chi Phí Tính Toán (Tuần 11)")

    f2_path = W11_DIR / "fig_resource_tradeoff_evals_runtime.png"
    if f2_path.exists():
        w, h = _fit_image(f2_path, Inches(7.2), Inches(5.4))
        slide.shapes.add_picture(str(f2_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(8.0), Inches(1.5), Inches(4.7), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(8.25), Inches(1.65), Inches(4.2), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Phân Tích Đánh Đổi Chi Phí")
    _style_run(r0, 15.5, True, INDIGO)

    tradeoffs = [
        ("Số lượt tính hàm mục tiêu (Evaluations):",
         "• DBO: Cố định tuyệt đối ở mức 263.870 lượt trên mọi hạt giống.\n"
         "• IDBO: Dao động từ 293.826 đến 337.808 lượt (trung bình 313.005 lượt, tăng thêm +18.6% evaluations do các lần thử nghiệm đột biến và restart)."),
        ("Thời gian thực thi (Runtime):",
         "• DBO: Trung bình 49.39 giây.\n"
         "• IDBO: Trung bình 56.61 giây (tăng thêm +7.22 giây, tương đương +14.6% thời gian tính toán)."),
        ("Bản chất của chi phí phụ trội:",
         "Chi phí tăng thêm của IDBO đến từ: (1) Tính toán độ đa dạng quần thể ở mỗi thế hệ; (2) Thực hiện đột biến Cauchy khi phát hiện đình trệ; (3) Tái khởi động lại một phần cá thể xấu."),
        ("Nhận định phương pháp luận quan trọng:",
         "IDBO đạt điểm số nhỉnh hơn (+0.1659 điểm) một phần vì được cấp thêm ngân sách tính toán (+18.6% evaluations). Do đó, so sánh chỉ hoàn toàn công bằng khi đặt hai thuật toán trong cùng một ngân sách cố định (Budget-Matched Benchmark).")
    ]
    for t, d in tradeoffs:
        p = tf.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"▲ {t}\n  ")
        _style_run(rt, 10.8, True, AMBER)
        rd = _add_run(p, d)
        _style_run(rd, 9.5, False, INK)

    _footer(slide, 10)


# =========================================================================== #
# SLIDE 11: [TUẦN 11] GIẢI MÃ TELEMETRY TẦNG NGOÀI VS TẦNG TRONG (W11-F3)
# =========================================================================== #
def build_slide_11(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 11] Giải Mã Telemetry: Tác Động Tầng Ngoài vs Tầng Trong", "Cơ Chế Hoạt Động Của IDBO (Tuần 11)")

    f3_path = W11_DIR / "fig_telemetry_activations.png"
    if f3_path.exists():
        w, h = _fit_image(f3_path, Inches(7.2), Inches(5.4))
        slide.shapes.add_picture(str(f3_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(8.0), Inches(1.5), Inches(4.7), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(8.25), Inches(1.65), Inches(4.2), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Giải Mã Tác Động Nội Tại Từ Telemetry")
    _style_run(r0, 15.5, True, INDIGO)

    tele_pts = [
        ("Tầng ngoài (Chọn tổ hợp món):",
         "Kích hoạt trung bình 29.5 lần đột biến và 2.9 lần restart. Giúp đàn bọ thoát khỏi bế tắc ở các seed phức tạp như 8005 (69 lần) và 8009 (58 lần)."),
        ("Tầng trong (Tối ưu gram liên tục):",
         "Kích hoạt cực kỳ tích cực với trung bình ~15.000 lần đột biến và 70–94 lần restart trên mỗi lần chạy hoàn chỉnh."),
        ("Hiện tượng quan trọng tại Seed 8007 & 8008:",
         "Tầng ngoài hoàn toàn không ghi nhận sụp đổ đa dạng (0 đột biến, 0 restart), nhưng điểm nghiệm giữa DBO và IDBO vẫn khác nhau (+0.0747 và -1.0497)!\n"
         "→ Bằng chứng telemetry xác nhận sự khác biệt đến từ hoạt động nội tại của tầng trong, không phải do rò rỉ RNG."),
        ("Ý nghĩa khoa học — Nhu cầu Ngưỡng kép:",
         "Không gian rời rạc (tổ hợp món) và không gian liên tục (gram) có độ phân tán tự nhiên rất khác nhau. Áp đặt chung một ngưỡng 0.28 cho cả hai tầng là chưa tối ưu, dẫn dắt sang nhu cầu kiến trúc Ngưỡng Kép (Dual Threshold).")
    ]
    for t, d in tele_pts:
        p = tf.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"★ {t}\n  ")
        _style_run(rt, 10.8, True, TEAL)
        rd = _add_run(p, d)
        _style_run(rd, 9.5, False, INK)

    _footer(slide, 11)


# =========================================================================== #
# SLIDE 12: [TUẦN 11] KIỂM SOÁT NGÂN SÁCH CHUNG (BUDGET-MATCHED W11-F4)
# =========================================================================== #
def build_slide_12(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 11] Kiểm Soát Ngân Sách Tính Toán Chung (Budget-Matched)", "Đảm Bảo Tính Công Bằng Khoa Học (Tuần 11)")

    f4_path = W11_DIR / "fig_budget_matched_smoke.png"
    if f4_path.exists():
        w, h = _fit_image(f4_path, Inches(6.5), Inches(5.4))
        slide.shapes.add_picture(str(f4_path), Inches(0.6), Inches(1.5), w, h)

    _card(slide, Inches(7.3), Inches(1.5), Inches(5.4), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(7.55), Inches(1.65), Inches(4.9), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Triển Khai & Diagnostic Test (PR #30)")
    _style_run(r0, 15.0, True, INDIGO)

    budget_pts = [
        ("Mục tiêu kỹ thuật chốt chặn ngân sách:",
         "Áp đặt giới hạn trên max_evaluations dùng chung cho cả DBO và IDBO. Dừng bộ giải ngay khi chạm trần ngân sách để bảo đảm công bằng tuyệt đối."),
        ("Cơ chế theo dõi _budget_remaining xuyên suốt:",
         "Biến _budget_remaining kiểm soát chặt chẽ từ tầng ngoài, các vòng lặp tầng trong đến bước tối ưu cuối cùng (Final Inner Solver). Khi hết ngân sách, mọi vòng lặp ngắt ngay lập tức."),
        ("Bản chất thử nghiệm 150 evaluations (W11-F4):",
         "Xác định đúng bản chất là một diagnostic test (kiểm tra tính chính xác của cờ dừng và luồng kiểm soát ngân sách). Kết quả: Cả DBO và IDBO đều dừng chính xác ở 150/150 lượt, budget_exceeded = False, không có rò rỉ tính toán."),
        ("Khóa cấu hình & Truy vết Git (Provenance):",
         "Script experiment_week11_budget.py tự động khóa mã băm config_hash và Git commit hash vào config_locked.json."),
        ("Tính sẵn sàng cho Tuần 12:",
         "Đã hoàn thiện toàn bộ khung kiến trúc, sẵn sàng cho benchmark toàn diện 260.000 evaluations trên toàn bộ tập độc lập ở Tuần 12.")
    ]
    for t, d in budget_pts:
        p = tf.add_paragraph()
        p.space_before = Pt(6)
        rt = _add_run(p, f"✓ {t}\n  ")
        _style_run(rt, 10.5, True, GREEN)
        rd = _add_run(p, d)
        _style_run(rd, 9.3, False, INK)

    _footer(slide, 12)


# =========================================================================== #
# SLIDE 13: [TUẦN 11] KIẾN TRÚC NGƯỠNG KÉP & ĐẢM BẢO CHẤT LƯỢNG 265 TESTS PASS
# =========================================================================== #
def build_slide_13(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "[Tuần 11] Kiến Trúc Ngưỡng Kép & Nghiệm Thu Chất Lượng Phần Mềm", "Hoàn Thiện Kiến Trúc & Kiểm Thử")

    _card(slide, Inches(0.6), Inches(1.5), Inches(5.9), Inches(5.4))
    tb1 = slide.shapes.add_textbox(Inches(0.85), Inches(1.65), Inches(5.4), Inches(5.1))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    r1 = _add_run(p1, "Kiến Trúc Ngưỡng Kép (Dual Threshold)")
    _style_run(r1, 15.0, True, INDIGO)

    pts1 = [
        ("Phân tách bản chất không gian tìm kiếm:",
         "Tầng ngoài hoạt động trên không gian rời rạc (chọn món ăn); tầng trong hoạt động trên không gian liên tục (tối ưu số gram khẩu phần)."),
        ("Cấu trúc cấu hình TwoTierConfig phân tầng:",
         "• outer_diversity_threshold = 0.28 (ngưỡng ứng viên khóa cho tầng ngoài sau kiểm định độc lập).\n"
         "• inner_diversity_threshold = None (chưa tự ý áp đặt ở tầng trong khi chưa đo lường đủ dữ liệu)."),
        ("Telemetry đo lường độc lập tầng trong:",
         "Ghi nhận inner_diversity_min_observed và inner_diversity_mean_observed làm cơ sở định lượng để hiệu chỉnh tầng trong ở Tuần 12."),
        ("Bảo đảm tương thích ngược tuyệt đối (Backward Compatibility):",
         "Bộ giải hoạt động an toàn và tương thích hoàn toàn khi chạy độc lập từng ngưỡng hoặc khi chạy cấu hình legacy.")
    ]
    for t, d in pts1:
        p = tf1.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"★ {t}\n  ")
        _style_run(rt, 10.5, True, TEAL)
        rd = _add_run(p, d)
        _style_run(rd, 9.3, False, INK)

    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb2 = slide.shapes.add_textbox(Inches(7.05), Inches(1.65), Inches(5.4), Inches(5.1))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    r2 = _add_run(p2, "Nghiệm Thu Chất Lượng (270/270 Tests PASS)")
    _style_run(r2, 15.0, True, INDIGO)

    pts2 = [
        ("Kiểm thử tự động 100% PASS (pytest 9.1.1):",
         "270/270 unit tests PASSED (~24s, Python 3.12). Bao phủ toàn diện:\n"
         "• Core Solvers & Telemetry: 84 tests\n"
         "• Ràng buộc dinh dưỡng, Trần Natri & DishRole: 88 tests\n"
         "• Mô hình dữ liệu & Schemas: 44 tests\n"
         "• Budget-Matched & Dual Threshold: 30 tests\n"
         "• FastAPI REST Endpoints & Week 9 Suite: 24 tests"),
        ("Tính tất định tuyệt đối (Deterministic Decoding):",
         "Mọi hàm ngẫu nhiên đều nhận seed tường minh, sử dụng RNG cục bộ rng = np.random.default_rng(seed), không rò rỉ trạng thái giữa các lần chạy."),
        ("Làm tròn khẩu phần 5g minh bạch:",
         "Nghiệm liên tục -> Làm tròn 5g -> Giải mã -> Tính lại dinh dưỡng -> Thẩm định validate_menu() trên nghiệm đã làm tròn."),
        ("Quy chuẩn phát ngôn khoa học & Minh bạch dữ liệu:",
         "Phân định rõ số liệu đo đạc thực tế và dữ liệu ước lượng (proxy đường), không đưa ra kết luận vượt quá phạm vi của mô hình thực nghiệm.")
    ]
    for t, d in pts2:
        p = tf2.add_paragraph()
        p.space_before = Pt(6)
        rt = _add_run(p, f"🛡 {t}\n  ")
        _style_run(rt, 10.5, True, GREEN)
        rd = _add_run(p, d)
        _style_run(rd, 9.1, False, INK)

    _footer(slide, 13)


# =========================================================================== #
# SLIDE 14: TỔNG KẾT GIAI ĐOẠN TUẦN 8–11 & ĐỊNH HƯỚNG TUẦN 12
# =========================================================================== #
def build_slide_14(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "Tổng Kết Toàn Diện Giai Đoạn Tuần 8–11 & Kế Hoạch Tuần 12", "Tổng Kết & Định Hướng")

    _card(slide, Inches(0.6), Inches(1.5), Inches(5.9), Inches(5.4))
    tb1 = slide.shapes.add_textbox(Inches(0.85), Inches(1.65), Inches(5.4), Inches(5.1))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    r1 = _add_run(p1, "Chuỗi Thành Quả Giai Đoạn Tuần 8 – 11")
    _style_run(r1, 15.0, True, INDIGO)

    achievements = [
        ("Tuần 8 — Two-Tier Solver & Khẩu phần 5g:",
         "Xây dựng bộ giải 2 tầng kết hợp chọn món rời rạc từ CSDL 13.709 món sạch và tối ưu gram liên tục, quy chuẩn làm tròn 5g thực tế chế biến, rút ra bài học sâu sắc từ Case Study P1."),
        ("Tuần 9 — Lập thực đơn 7 ngày đa hồ sơ:",
         "Triển khai chu kỳ 7 ngày trên 3 hồ sơ người dùng, Diversity Penalty đạt 100% món chính độc nhất, thẩm định minh bạch trần natri và proxy đường."),
        ("Tuần 10 — Hệ thống Web API & UI:",
         "Đưa solver lên nền tảng Web với kiến trúc Single-port FastAPI, 6 REST endpoints, giao diện Dark Glassmorphism, Radar chart 6 trục và bảng thực đơn 5g."),
        ("Tuần 11 — Chuẩn hóa độc lập & Budget-Matched:",
         "Đánh giá mù trên 8 seed độc lập (IDBO thắng 5/8, Wilcoxon p>0.05), giải mã chi phí tính toán (+18.6% evals), cài đặt chốt chặn Budget-Matched, kiến trúc Dual Threshold, 270/270 tests pass.")
    ]
    for t, d in achievements:
        p = tf1.add_paragraph()
        p.space_before = Pt(6)
        rt = _add_run(p, f"✓ {t}\n  ")
        _style_run(rt, 10.5, True, GREEN)
        rd = _add_run(p, d)
        _style_run(rd, 9.3, False, INK)

    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb2 = slide.shapes.add_textbox(Inches(7.05), Inches(1.65), Inches(5.4), Inches(5.1))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    r2 = _add_run(p2, "Kế Hoạch Nghiên Cứu Trọng Tâm Tuần 12")
    _style_run(r2, 15.0, True, INDIGO)

    plans = [
        ("1. Benchmark Budget-Matched Quy Mô Lớn:",
         "Chạy đối chuẩn toàn diện DBO vs IDBO trên tập seed độc lập với ngân sách chung (ví dụ 260.000 evaluations) để trả lời dứt điểm về hiệu năng khi chi phí tài nguyên bằng nhau."),
        ("2. Hiệu Chỉnh Ngưỡng Đa Dạng Tầng Trong:",
         "Sử dụng dữ liệu telemetry inner_diversity_mean để thiết lập inner_diversity_threshold phù hợp, tránh hiện tượng đột biến phá vỡ nghiệm tốt như ở Seed 8008."),
        ("3. Kiểm Thử Tự Động Đầu Cuối (E2E Web Test):",
         "Xây dựng kịch bản kiểm thử tự động toàn diện từ giao diện Web UI -> FastAPI Backend -> Two-Tier Solver -> Hiển thị kết quả thực đơn."),
        ("4. Hoàn Thiện Bản Thảo Khóa Luận Tốt Nghiệp:",
         "Hệ thống hóa toàn bộ các kết quả thực nghiệm trung thực từ Tuần 1 đến Tuần 12 vào báo cáo Word chính thức của đề tài CNTT-KLCN142.")
    ]
    for t, d in plans:
        p = tf2.add_paragraph()
        p.space_before = Pt(6)
        rt = _add_run(p, f"★ {t}\n  ")
        _style_run(rt, 10.5, True, AMBER)
        rd = _add_run(p, d)
        _style_run(rd, 9.3, False, INK)

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
