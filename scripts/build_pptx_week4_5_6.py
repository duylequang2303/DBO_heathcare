"""Dựng slide báo cáo tuần 4-5-6 (DBO / IDBO) từ số liệu thực nghiệm chuẩn xác.

Cấu trúc trình chiếu khoa học:
- Bìa báo cáo & Tổng quan toàn diện
- Phần A: Tuần 4 — DBO gốc trên 6 hàm benchmark (Thiết lập -> Bảng Mean -> 8 Slide biểu đồ -> Tổng kết)
- Phần B: Tuần 5-6 — Thuật toán cải tiến IDBO (Thiết lập -> Sơ đồ giải thuật -> Tần suất kích hoạt -> 9 Slide biểu đồ -> So sánh đối chứng -> Phân tích chi phí -> Đánh giá toàn diện -> Kế hoạch Tuần 7)

Usage:
    python scripts/build_pptx_week4_5_6.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Slide_Tuan_4_5_6_DBO_IDBO.pptx"
W4 = ROOT / "experiments" / "week4"
W56 = ROOT / "experiments" / "week5_6"

# --------------------------------------------------------------------------- #
# Bảng màu chuẩn học thuật cao cấp
# --------------------------------------------------------------------------- #
INDIGO = RGBColor(0x1B, 0x2A, 0x4A)      # Xanh Navy đậm chủ đạo
INDIGO2 = RGBColor(0x2D, 0x3E, 0x63)     # Xanh Navy phụ
AMBER = RGBColor(0xD9, 0x82, 0x2B)       # Cam Vàng điểm nhấn
TEAL = RGBColor(0x1D, 0x6F, 0x6F)        # Xanh Teal giai đoạn 2
GREEN = RGBColor(0x21, 0x7A, 0x4B)       # Xanh lá tích cực
RED = RGBColor(0xB8, 0x32, 0x28)         # Đỏ cảnh báo / điểm nghẽn
INK = RGBColor(0x1E, 0x24, 0x30)         # Đen chữ chính
MUTED = RGBColor(0x5A, 0x64, 0x78)       # Xám ghi chữ phụ
LIGHT = RGBColor(0xF5, 0xF7, 0xFB)       # Nền thẻ sáng
LINE = RGBColor(0xD3, 0xDB, 0xEA)        # Đường viền ngăn cách
WHITE = RGBColor(0xFF, 0xFF, 0xFF)       # Trắng tinh
CREAM = RGBColor(0xFD, 0xF6, 0xEB)       # Nền kem ghi chú
CARD_BORDER = RGBColor(0xE2, 0xE8, 0xF0) # Viền thẻ trang nhã

FONT = "Calibri"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


# --------------------------------------------------------------------------- #
# Helper Functions
# --------------------------------------------------------------------------- #
def _style_run(run, size, bold, color, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = FONT
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", FONT)


def _rect(slide, l, t, w, h, color, rounded=False, line_color=None, line_width=1.0):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, l, t, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if line_color is not None:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(line_width)
    else:
        shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def _text(slide, l, t, w, h, runs, size=16, bold=False, color=INK,
          align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.0,
          space_after=0):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    if isinstance(runs, str):
        paras = [[(runs, {})]]
    elif runs and isinstance(runs[0], tuple):
        paras = [runs]
    else:
        paras = runs
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        if isinstance(para, str):
            para = [(para, {})]
        for chunk in para:
            text, opts = chunk if isinstance(chunk, tuple) else (chunk, {})
            run = p.add_run()
            run.text = text
            _style_run(run, opts.get("size", size), opts.get("bold", bold),
                       opts.get("color", color), opts.get("italic", False))
    return box


def _header(slide, title, kicker, accent):
    _rect(slide, 0, 0, SLIDE_W, Inches(0.14), accent)
    _text(slide, Inches(0.55), Inches(0.30), Inches(12.23), Inches(0.26),
          kicker, size=11.5, bold=True, color=accent)
    _text(slide, Inches(0.55), Inches(0.58), Inches(12.23), Inches(0.52),
          title, size=24, bold=True, color=INDIGO)
    _rect(slide, Inches(0.55), Inches(1.14), Inches(12.23), Pt(1.2), LINE)


def _footer(slide, label, page, total):
    _rect(slide, Inches(0.55), Inches(7.04), Inches(12.23), Pt(1.0), LINE)
    _text(slide, Inches(0.55), Inches(7.11), Inches(9.5), Inches(0.3),
          label, size=9.5, color=MUTED)
    _text(slide, Inches(10.5), Inches(7.11), Inches(2.28), Inches(0.3),
          f"{page} / {total}", size=9.5, bold=True, color=MUTED,
          align=PP_ALIGN.RIGHT)


def _fit(path, box_w, box_h):
    with Image.open(path) as im:
        iw, ih = im.size
    box_aspect = (box_w / 914400) / (box_h / 914400)
    aspect = iw / ih
    if aspect > box_aspect:
        w = box_w
        h = int(box_w / aspect)
    else:
        h = box_h
        w = int(box_h * aspect)
    return w, h


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _page_number(total):
    state = {"n": 0}

    def nxt():
        state["n"] += 1
        return state["n"]

    def count():
        return state["n"]

    nxt.count = count
    return nxt


# --------------------------------------------------------------------------- #
# Slide Builders
# --------------------------------------------------------------------------- #
def cover(prs, n, total):
    s = _blank(prs)
    _rect(s, 0, 0, SLIDE_W, SLIDE_H, INDIGO)
    _rect(s, 0, 0, SLIDE_W, Inches(0.18), AMBER)
    
    # Header tổ chức
    _text(s, Inches(0.9), Inches(0.70), Inches(11.5), Inches(0.35),
          "TRƯỜNG ĐẠI HỌC CÔNG THƯƠNG TP. HỒ CHÍ MINH — KHOA CÔNG NGHỆ THÔNG TIN",
          size=13, bold=True, color=RGBColor(0x9F, 0xB0, 0xCE))
    
    # Tag mã đề tài
    _rect(s, Inches(0.9), Inches(1.15), Inches(0.08), Inches(0.30), AMBER)
    _text(s, Inches(1.1), Inches(1.13), Inches(11), Inches(0.30),
          "KHÓA LUẬN TỐT NGHIỆP CỬ NHÂN CNTT · MÃ ĐỀ TÀI: CNTT-KLCN142",
          size=12.5, bold=True, color=AMBER)
    
    # Tiêu đề chính (tách các khối để đảm bảo không bao giờ đè lên nhau)
    _text(s, Inches(0.9), Inches(1.60), Inches(11.5), Inches(0.95),
          "BÁO CÁO KẾT QUẢ THỰC NGHIỆM THUẬT TOÁN DBO VÀ IDBO",
          size=28, bold=True, color=WHITE)
    
    _text(s, Inches(0.9), Inches(2.65), Inches(11.5), Inches(0.40),
          "Đánh giá hiệu năng và tính ổn định trên 6 hàm benchmark chuẩn liên tục",
          size=18, color=RGBColor(0xDD, 0xE5, 0xF5))
    
    _text(s, Inches(0.9), Inches(3.15), Inches(11.5), Inches(0.35),
          "Giai đoạn nghiên cứu & tối ưu thuật toán: Tuần 4 và Tuần 5–6 (Học kỳ 1, 2025–2026)",
          size=14, color=RGBColor(0xC9, 0xD5, 0xEA))
    
    _rect(s, Inches(0.9), Inches(3.60), Inches(2.5), Pt(2.5), AMBER)
    
    # Khung thông tin đề tài & nhóm
    info_box = [
        [("Đề tài: ", {"bold": True, "color": WHITE}),
         ("Hệ thống đề xuất thực đơn dinh dưỡng cá nhân hóa dựa trên thuật toán IDBO", {})],
        [("Giảng viên hướng dẫn: ", {"bold": True, "color": WHITE}),
         ("ThS. Đinh Nguyễn Trọng Nghĩa", {})],
        [("Nhóm sinh viên thực hiện: ", {"bold": True, "color": WHITE}),
         ("Lê Quang Duy (2001230123) · Đặng Nguyễn Minh Đăng (2001230175) · Hồ Trung Cương (2001230070)",
          {"bold": True, "color": RGBColor(0xFF, 0xEE, 0xCC)})],
    ]
    _text(s, Inches(0.9), Inches(4.10), Inches(11.5), Inches(1.6),
          info_box, size=14.5, color=RGBColor(0xC9, 0xD5, 0xEA), line_spacing=1.28)
    
    # Ghi chú dữ liệu
    _text(s, Inches(0.9), Inches(6.65), Inches(11.5), Inches(0.4),
          "Quy mô thực nghiệm: 1.620 lượt chạy độc lập (540 DBO + 1.080 DBO & IDBO) · M = 30 seed · dim = 10, 30, 50",
          size=12, color=RGBColor(0x9F, 0xB0, 0xCE))
    n()


def summary(prs, n, total):
    s = _blank(prs)
    _header(s, "Tổng quan thực nghiệm Tuần 4–6 & Phân công nhiệm vụ",
            "TỔNG QUAN NGHIÊN CỨU", INDIGO)

    # 4 Thẻ KPI chính
    kpis = [
        ("6", "Hàm benchmark chuẩn", "3 đơn điệu (Unimodal) + 3 đa cực trị (Multimodal)", INDIGO),
        ("1.620", "Lượt chạy độc lập", "540 DBO (tuần 4) + 1.080 DBO/IDBO (tuần 5-6)", TEAL),
        ("18 / 18", "Cặp cấu hình Hòa", "IDBO bảo toàn chất lượng DBO gốc (chênh lệch < 1%)", GREEN),
        ("+0,028%", "Tăng chi phí gọi hàm", "Bảo toàn triệt để tài nguyên tính toán (chỉ ~4 evals/run)", AMBER),
    ]
    for i, (num, lab, sub, col) in enumerate(kpis):
        l = Inches(0.55 + i * 3.11)
        _rect(s, l, Inches(1.35), Inches(2.93), Inches(1.32), LIGHT, rounded=True, line_color=LINE)
        _rect(s, l, Inches(1.35), Inches(0.08), Inches(1.32), col)
        _text(s, l + Inches(0.20), Inches(1.45), Inches(2.65), Inches(0.45),
              num, size=24, bold=True, color=col)
        _text(s, l + Inches(0.20), Inches(1.95), Inches(2.65), Inches(0.28),
              lab, size=12.5, bold=True, color=INK)
        _text(s, l + Inches(0.20), Inches(2.25), Inches(2.65), Inches(0.35),
              sub, size=10, color=MUTED, line_spacing=1.05)

    rows = [
        ["Giai đoạn", "Mô hình & Phương pháp", "Kết quả thực nghiệm chính", "Phân công trách nhiệm"],
        ["Tuần 4",
         "DBO gốc (Xue & Shen, 2023)\n• 4 hành vi sinh tồn bọ hung\n• 6 hàm benchmark, dim 10/30/50, M=30",
         "• Cài đặt chuẩn xác 100%, hội tụ sâu tiệm cận 0\n• 50D Rastrigin/Griewank đạt nghiệm 0 tuyệt đối\n• Rosenbrock là thách thức tự nhiên (~5,6 / 26,2 / 46,6)",
         "• Lê Quang Duy: Thiết kế khung DBO & tích hợp\n• Hồ Trung Cương: Cài đặt 4 hành vi sinh tồn\n• Đặng Nguyễn Minh Đăng: Benchmark & Runner"],
        ["Tuần 5–6",
         "IDBO cải tiến (Improved DBO)\n• Giám sát độ đa dạng quần thể (Diversity)\n• Kích hoạt Perturbation & Random Restart",
         "• 18/18 cấu hình Hòa theo ngưỡng 1% (Mean)\n• Bảo toàn nghiệm, không làm chậm hội tụ tự nhiên\n• Thời gian thực thi tăng 15–20% do đánh giá lại cá thể",
         "• Lê Quang Duy: Tích hợp module IDBO\n• Hồ Trung Cương: Cài đặt Diversity & Restart\n• Đặng Nguyễn Minh Đăng: Thí nghiệm so sánh"],
    ]
    align_summary = {0: PP_ALIGN.CENTER, 1: PP_ALIGN.LEFT, 2: PP_ALIGN.LEFT, 3: PP_ALIGN.LEFT}
    table(s, rows, Inches(0.55), Inches(2.88), Inches(12.23), Inches(3.95),
          col_w=[Inches(1.4), Inches(3.6), Inches(4.3), Inches(2.93)],
          header_color=INDIGO, body_size=11, row_h=Inches(1.45), align_cols=align_summary)
    _footer(s, "Tổng quan đề tài", n(), total)


def divider(prs, n, total, tag, title, subtitle, accent, footer_label):
    s = _blank(prs)
    _rect(s, 0, 0, SLIDE_W, SLIDE_H, accent)
    _rect(s, 0, 0, Inches(0.28), SLIDE_H, AMBER)
    _text(s, Inches(1.1), Inches(2.2), Inches(11), Inches(0.5),
          tag, size=18, bold=True, color=AMBER)
    _text(s, Inches(1.1), Inches(2.8), Inches(11), Inches(1.2),
          title, size=38, bold=True, color=WHITE)
    _text(s, Inches(1.1), Inches(4.15), Inches(10.8), Inches(0.8),
          subtitle, size=17, color=RGBColor(0xCF, 0xDA, 0xEE))
    n()


def setup_slide(prs, n, total, title, kicker, accent, params, who, note,
                footer_label):
    s = _blank(prs)
    _header(s, title, kicker, accent)
    
    # Cột thiết lập tham số
    _rect(s, Inches(0.55), Inches(1.4), Inches(6.15), Inches(4.65), LIGHT,
          rounded=True, line_color=LINE)
    _text(s, Inches(0.85), Inches(1.6), Inches(5.5), Inches(0.35),
          "THÔNG SỐ CẤU HÌNH THỰC NGHIỆM", size=12.5, bold=True, color=accent)
    y = 1.98
    for k, v in params:
        _text(s, Inches(0.85), Inches(y), Inches(2.2), Inches(0.35),
              k, size=12, bold=True, color=INK)
        _text(s, Inches(3.05), Inches(y), Inches(3.45), Inches(0.35),
              v, size=12, color=INDIGO2)
        y += 0.44

    # Cột phân công trách nhiệm
    _rect(s, Inches(6.95), Inches(1.4), Inches(5.83), Inches(4.65), WHITE,
          rounded=True, line_color=LINE)
    _text(s, Inches(7.25), Inches(1.6), Inches(5.2), Inches(0.35),
          "PHÂN CÔNG TRÁCH NHIỆM & NGUỒN DỮ LIỆU", size=12.5, bold=True, color=accent)
    y = 1.98
    for name, task in who:
        _text(s, Inches(7.25), Inches(y), Inches(5.25), Inches(0.48),
              [(name + "\n", {"bold": True, "color": INDIGO, "size": 12.5}),
               (task, {"color": MUTED, "size": 11.5})], line_spacing=1.05)
        y += 0.65
        
    _rect(s, Inches(7.25), Inches(3.95), Inches(5.25), Pt(1.0), LINE)
    _text(s, Inches(7.25), Inches(4.15), Inches(5.25), Inches(1.7),
          [[("Ghi chú phương pháp luận:\n", {"bold": True, "color": accent, "size": 11.5})],
           [(note, {"size": 11, "color": INK})]], line_spacing=1.15)
           
    _footer(s, footer_label, n(), total)


def table(slide, rows, l, t, w, h, col_w, header_color, body_size=11.5,
          row_h=None, highlight=None, header_size=12, align_cols=None):
    n_row, n_col = len(rows), len(rows[0])
    shape = slide.shapes.add_table(n_row, n_col, l, t, w, h)
    tbl = shape.table
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = cw
    if row_h is not None:
        for r in range(n_row):
            tbl.rows[r].height = row_h if r else Inches(0.48)
    highlight = highlight or {}
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
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


def image_slide(prs, n, total, title, kicker, accent, png, remark,
                footer_label, tag=None):
    s = _blank(prs)
    _header(s, title, kicker, accent)
    
    # Khung ảnh chính
    box_l, box_t = Inches(0.55), Inches(1.30)
    box_w, box_h = Inches(12.23), Inches(4.55)
    w, h = _fit(png, box_w, box_h)
    left = int(box_l + (box_w - w) / 2)
    top = int(box_t + (box_h - h) / 2)
    s.shapes.add_picture(str(png), left, top, width=w, height=h)
    
    if tag:
        _rect(s, Inches(0.55), Inches(1.28), Inches(2.2), Inches(0.32),
              accent, rounded=True)
        _text(s, Inches(0.55), Inches(1.28), Inches(2.2), Inches(0.32),
              tag, size=10.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
              anchor=MSO_ANCHOR.MIDDLE)
              
    # Khung nhận xét tinh tế
    _rect(s, Inches(0.55), Inches(5.95), Inches(12.23), Inches(0.96), LIGHT,
          rounded=True, line_color=LINE)
    _text(s, Inches(0.80), Inches(6.05), Inches(11.75), Inches(0.78),
          [[("💡 Quan sát then chốt:  ", {"bold": True, "color": accent, "size": 12.5})],
           [(remark, {"size": 12, "color": INK})]], line_spacing=1.12)
           
    _footer(s, footer_label, n(), total)


def bullets_slide(prs, n, total, title, kicker, accent, items, footer_label,
                  size=14):
    s = _blank(prs)
    _header(s, title, kicker, accent)
    box = s.shapes.add_textbox(Inches(0.7), Inches(1.50), Inches(11.95), Inches(5.2))
    tf = box.text_frame
    tf.word_wrap = True
    for i, (head, body) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(14)
        dot = p.add_run()
        dot.text = "▪  "
        _style_run(dot, size, True, accent)
        if head:
            rh = p.add_run()
            # Ensure clean colon and space separation
            head_clean = head.strip()
            if not head_clean.endswith(":"):
                head_clean += ":"
            rh.text = head_clean + "  "
            _style_run(rh, size, True, INDIGO)
        rb = p.add_run()
        rb.text = body.strip()
        _style_run(rb, size, False, INK)
    _footer(s, footer_label, n(), total)


def flowchart_slide(prs, n, total):
    """Slide 17: Vẽ sơ đồ kiến trúc IDBO hoàn chỉnh bằng vector shapes."""
    s = _blank(prs)
    _header(s, "Sơ đồ giải thuật IDBO — Cơ chế kiểm soát đa dạng & Thoát bẫy",
            "KIẾN TRÚC THUẬT TOÁN", TEAL)

    # ──────────────────────────────────────────────────────────────────────────
    # CỘT TRÁI: FLOWCHART VECTOR (x = 0.55 -> 7.8)
    # ──────────────────────────────────────────────────────────────────────────
    _rect(s, Inches(0.55), Inches(1.35), Inches(7.35), Inches(5.55), LIGHT,
          rounded=True, line_color=LINE)

    # 1. Bắt đầu
    _rect(s, Inches(2.3), Inches(1.48), Inches(3.8), Inches(0.44), INDIGO, rounded=True)
    _text(s, Inches(2.3), Inches(1.48), Inches(3.8), Inches(0.44),
          "Bắt đầu vòng lặp t (t = 1 → max_iter)", size=11, bold=True,
          color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Mũi tên 1 -> 2
    _text(s, Inches(3.7), Inches(1.92), Inches(1.0), Inches(0.20), "↓", size=13, bold=True,
          color=MUTED, align=PP_ALIGN.CENTER)

    # 2. 4 hành vi DBO
    _rect(s, Inches(1.6), Inches(2.14), Inches(5.2), Inches(0.52), INDIGO2, rounded=True)
    _text(s, Inches(1.6), Inches(2.14), Inches(5.2), Inches(0.52),
          "Thực thi 4 hành vi DBO gốc:\nLăn phân (Rolling) · Sinh sản · Kiếm ăn · Cướp đoạt",
          size=10.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Mũi tên 2 -> 3
    _text(s, Inches(3.7), Inches(2.66), Inches(1.0), Inches(0.20), "↓", size=13, bold=True,
          color=MUTED, align=PP_ALIGN.CENTER)

    # 3. Đo Diversity
    _rect(s, Inches(1.4), Inches(2.88), Inches(5.6), Inches(0.54), TEAL, rounded=True)
    _text(s, Inches(1.4), Inches(2.88), Inches(5.6), Inches(0.54),
          "Đo độ đa dạng chuẩn hóa của quần thể:\nDiversity(t) = (1 / D) × ∑ [ std(X_:,d) / (ub_d − lb_d) ]",
          size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Mũi tên 3 -> 4
    _text(s, Inches(3.7), Inches(3.42), Inches(1.0), Inches(0.20), "↓", size=13, bold=True,
          color=MUTED, align=PP_ALIGN.CENTER)

    # 4. Điều kiện 1: Diversity < 1e-3?
    _rect(s, Inches(2.2), Inches(3.64), Inches(4.0), Inches(0.48), CREAM,
          rounded=True, line_color=AMBER, line_width=1.5)
    _text(s, Inches(2.2), Inches(3.64), Inches(4.0), Inches(0.48),
          "Điều kiện: Diversity < 10⁻³ ?", size=11, bold=True,
          color=AMBER, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Nhánh KHÔNG (Diversity >= 1e-3) -> sang phải
    _text(s, Inches(6.25), Inches(3.66), Inches(1.5), Inches(0.22), "Không (≥ 10⁻³) →",
          size=9.5, bold=True, color=GREEN)
    _rect(s, Inches(4.6), Inches(4.25), Inches(3.1), Inches(0.68), WHITE,
          rounded=True, line_color=GREEN, line_width=1.2)
    _text(s, Inches(4.6), Inches(4.25), Inches(3.1), Inches(0.68),
          "BẢO TOÀN DBO GỐC:\nKhông can thiệp ngẫu nhiên\n→ Chuyển sang vòng lặp (t + 1)",
          size=9.5, bold=True, color=GREEN, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Nhánh CÓ (Diversity < 1e-3) -> xuống
    _text(s, Inches(1.5), Inches(4.14), Inches(1.5), Inches(0.20), "Có (< 10⁻³) ↓",
          size=9, bold=True, color=RED)

    # 5. Điều kiện 2: Stagnation >= 25?
    _rect(s, Inches(0.75), Inches(4.40), Inches(3.5), Inches(0.48), CREAM,
          rounded=True, line_color=RED, line_width=1.5)
    _text(s, Inches(0.75), Inches(4.40), Inches(3.5), Inches(0.48),
          "Kiểm tra trì trệ (Stagnation):\nSố vòng không đổi nghiệm ≥ 25 ?",
          size=9.5, bold=True, color=RED, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Mũi tên từ Điều kiện 2 xuống 2 cơ chế
    _text(s, Inches(0.85), Inches(4.94), Inches(1.2), Inches(0.20), "Không (< 25) ↓",
          size=8.5, bold=True, color=AMBER)
    _text(s, Inches(2.85), Inches(4.94), Inches(1.2), Inches(0.20), "Có (≥ 25) ↓",
          size=8.5, bold=True, color=RED)

    # Cơ chế 1: Perturbation
    _rect(s, Inches(0.75), Inches(5.20), Inches(2.9), Inches(0.66), WHITE,
          rounded=True, line_color=AMBER, line_width=1.2)
    _text(s, Inches(0.75), Inches(5.20), Inches(2.9), Inches(0.66),
          "GAUSSIAN PERTURBATION:\nBơm nhiễu Gauss vào 20% cá thể\n(Trừ cá thể Elite tốt nhất)",
          size=9, bold=True, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Cơ chế 2: Restart
    _rect(s, Inches(3.85), Inches(5.20), Inches(3.85), Inches(0.66), WHITE,
          rounded=True, line_color=RED, line_width=1.2)
    _text(s, Inches(3.85), Inches(5.20), Inches(3.85), Inches(0.66),
          "RANDOM RESTART:\nTái khởi tạo 25% cá thể tệ nhất\ntrong [lb, ub] (Trừ Elite)",
          size=9, bold=True, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Đánh giá lại
    _rect(s, Inches(0.75), Inches(6.08), Inches(6.95), Inches(0.38), INDIGO, rounded=True)
    _text(s, Inches(0.75), Inches(6.08), Inches(6.95), Inches(0.38),
          "Đánh giá lại hàm mục tiêu cho các cá thể bị can thiệp & Cập nhật Best Fitness",
          size=9.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # ──────────────────────────────────────────────────────────────────────────
    # CỘT PHẢI: GIẢI THÍCH NGUYÊN LÝ HOẠT ĐỘNG (x = 8.1 -> 12.78)
    # ──────────────────────────────────────────────────────────────────────────
    _rect(s, Inches(8.1), Inches(1.35), Inches(4.68), Inches(5.55), WHITE,
          rounded=True, line_color=LINE)
    _rect(s, Inches(8.1), Inches(1.35), Inches(4.68), Inches(0.55), TEAL, rounded=True)
    _rect(s, Inches(8.1), Inches(1.70), Inches(4.68), Inches(0.20), TEAL)
    _text(s, Inches(8.3), Inches(1.45), Inches(4.28), Inches(0.35),
          "NGUYÊN LÝ HOẠT ĐỘNG CỦA IDBO", size=13, bold=True, color=WHITE)

    points = [
        ("1. Không xáo trộn vô ích (Zero Interference):\n",
         "Khi Diversity ≥ 10⁻³, IDBO không can thiệp, chạy đúng 100% cơ chế DBO gốc. Đảm bảo tốc độ hội tụ tự nhiên không bị suy giảm."),
        ("2. Phát hiện sớm nguy cơ co cụm quần thể:\n",
         "Bộ đo Diversity chuẩn hóa theo biên [lb, ub] giúp phát hiện chính xác thời điểm bầy bọ hung tập trung quá sát nhau trước khi rơi vào bẫy cực trị."),
        ("3. Can thiệp 2 cấp độ có điều kiện:\n",
         "• Cấp 1 (Chưa trì trệ): Bơm nhiễu Gauss rung lắc nhẹ để cá thể tiếp tục tìm kiếm cục bộ.\n"
         "• Cấp 2 (Trì trệ ≥ 25 vòng): Tái sinh ngẫu nhiên 25% cá thể kém nhất khắp không gian tìm kiếm để mở đường thoát bẫy toàn diện."),
        ("4. Bảo toàn cá thể Elite tuyệt đối:\n",
         "Nghiệm tốt nhất tìm thấy (n_elite = 1) luôn được bảo vệ nguyên vẹn, ngăn chặn nguy cơ làm mất nghiệm tối ưu toàn cục.")
    ]
    y_p = 2.05
    for h_txt, b_txt in points:
        _text(s, Inches(8.35), Inches(y_p), Inches(4.2), Inches(1.0),
              [(h_txt, {"bold": True, "color": INDIGO, "size": 11.5}),
               (b_txt, {"color": INK, "size": 10.5})], line_spacing=1.12)
        y_p += 1.15

    _footer(s, "Tuần 5–6 · Sơ đồ thuật toán IDBO", n(), total)


def conclusion_cards(prs, n, total):
    """Slide 30: 4 Thẻ tổng kết đánh giá toàn diện Tuần 4-6."""
    s = _blank(prs)
    _header(s, "Tổng kết đánh giá thực nghiệm Tuần 4 – 6 (DBO & IDBO)",
            "ĐÁNH GIÁ KHOA HỌC TOÀN DIỆN", TEAL)

    cards_data = [
        ("1. CHUẨN XÁC & ĐẦY ĐỦ",
         INDIGO,
         [("Cài đặt chuẩn lý thuyết:\n", True, INDIGO),
          ("Thuật toán DBO gốc phản ánh chính xác bài báo của Xue & Shen (2023), vượt qua 100% 128 unit tests.\n\n", False, INK),
          ("Thực nghiệm quy mô lớn:\n", True, INDIGO),
          ("Tổng cộng 1.620 lượt chạy thực nghiệm độc lập (540 DBO + 1.080 DBO & IDBO) trên 6 hàm chuẩn và 3 mức chiều (10, 30, 50D).", False, INK)]),

        ("2. BẢO TOÀN CHẤT LƯỢNG",
         TEAL,
         [("18 / 18 cấu hình Hòa:\n", True, TEAL),
          ("IDBO đạt kết quả tối ưu tương đương DBO gốc trên mọi hàm mục tiêu (sai khác Mean Fitness < 1%).\n\n", False, INK),
          ("Không phá vỡ hội tụ:\n", True, TEAL),
          ("Đồ thị hội tụ (Convergence) và phân bố sai số (Boxplot) hoàn toàn trùng khít, chứng minh cơ chế ngẫu nhiên không làm nhiễu loạn nghiệm.", False, INK)]),

        ("3. TỐI ƯU TÀI NGUYÊN",
         AMBER,
         [("Kích hoạt thông minh:\n", True, AMBER),
          ("Chỉ can thiệp khi Diversity < 10⁻³ và Stagnation ≥ 25. Trên 15/18 cấu hình, cơ chế hoàn toàn ở trạng thái nghỉ.\n\n", False, INK),
          ("Tiết kiệm hàm mục tiêu:\n", True, AMBER),
          ("Số lần gọi hàm (Evals) chỉ tăng 0,028% (trung bình thêm ~4 evals/run), bảo toàn tối đa năng lực xử lý.", False, INK)]),

        ("4. KHOA HỌC TRUNG THỰC",
         GREEN,
         [("Minh bạch số liệu 100%:\n", True, GREEN),
          ("Báo cáo trung thực kết quả hòa trên benchmark trơn; không cố tình phóng đại 'IDBO vượt trội DBO'.\n\n", False, INK),
          ("Định vị đúng giá trị:\n", True, GREEN),
          ("Benchmark liên tục là bước đệm kiểm chứng an toàn; sức mạnh thực tế của IDBO sẽ phát huy tối đa ở không gian thực đơn rời rạc Tuần 7.", False, INK)]),
    ]

    for i, (title, color, runs) in enumerate(cards_data):
        l = Inches(0.55 + i * 3.11)
        _rect(s, l, Inches(1.4), Inches(2.93), Inches(5.4), WHITE, rounded=True, line_color=LINE)
        _rect(s, l, Inches(1.4), Inches(2.93), Inches(0.52), color, rounded=True)
        _rect(s, l, Inches(1.70), Inches(2.93), Inches(0.22), color)
        _text(s, l + Inches(0.15), Inches(1.48), Inches(2.65), Inches(0.35),
              title, size=11.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        
        y_text = Inches(2.1)
        formatted_runs = [(t, {"bold": b, "color": c}) for (t, b, c) in runs]
        _text(s, l + Inches(0.18), y_text, Inches(2.57), Inches(4.5),
              formatted_runs, size=11, line_spacing=1.18)

    _footer(s, "Tuần 5–6 · Tổng kết đánh giá", n(), total)


def roadmap_week7(prs, n, total):
    """Slide 31: Kế hoạch Tuần 7 — Chuyển giao sang bài toán thực đơn."""
    s = _blank(prs)
    _rect(s, 0, 0, SLIDE_W, SLIDE_H, INDIGO)
    _rect(s, 0, 0, Inches(0.25), SLIDE_H, AMBER)

    _text(s, Inches(0.9), Inches(0.55), Inches(11.5), Inches(0.35),
          "KẾ HOẠCH BƯỚC TIẾP THEO (GIAI ĐOẠN 3)", size=12.5, bold=True, color=AMBER)
    _text(s, Inches(0.9), Inches(0.90), Inches(11.5), Inches(0.55),
          "Tuần 7: Tích hợp IDBO vào bài toán tối ưu thực đơn dinh dưỡng",
          size=26, bold=True, color=WHITE)
    _rect(s, Inches(0.9), Inches(1.55), Inches(2.5), Pt(2.5), AMBER)

    columns = [
        ("1. ADAPTER KHẨU PHẦN",
         "Biểu diễn nghiệm & Chuyển đổi",
         AMBER,
         [("Biểu diễn nghiệm liên tục:\n", True),
          ("Vector x chứa khẩu phần gram [25, 350]g cho 8 món ăn trong ngày (sum meal_counts = 8).\n\n", False),
          ("Adapter hàm mục tiêu:\n", True),
          ("objective(x) = -evaluate(Menu) để tương thích tiêu chí minimize của DBO/IDBO.", False)]),

        ("2. RÀNG BUỘC DINH DƯỠNG",
         "Không gian 15.929 món ăn",
         TEAL,
         [("CSDL thực phẩm sạch:\n", True),
          ("Khai thác 15.929 món đã chuẩn hóa về năng lượng, protein, carb, fat, fiber, sodium.\n\n", False),
          ("Sampler & Ràng buộc:\n", True),
          ("Cố định food_ids hợp lệ theo từng bữa ăn (Sáng, Trưa, Tối, Phụ), phạt vi phạm vi chất và bệnh lý.", False)]),

        ("3. THỰC NGHIỆM ĐỐI CHỨNG",
         "Kiểm chứng trên Profile P1",
         GREEN,
         [("Kịch bản thử nghiệm:\n", True),
          ("Hồ sơ mẫu P1 (Duy, 22t, 65kg, duy trì cân nặng, 2.492 kcal) với n_agents=10, max_iter=200.\n\n", False),
          ("Đánh giá ưu thế IDBO:\n", True),
          ("Chứng minh cơ chế Diversity và Restart giúp bọ hung thoát bẫy cục bộ trong ma trận thực đơn rời rạc.", False)]),
    ]

    for i, (title, sub, col, items) in enumerate(columns):
        l = Inches(0.9 + i * 3.9)
        _rect(s, l, Inches(1.85), Inches(3.65), Inches(4.5), RGBColor(0x23, 0x33, 0x54),
              rounded=True, line_color=RGBColor(0x3B, 0x4D, 0x73))
        _rect(s, l, Inches(1.85), Inches(3.65), Inches(0.55), col, rounded=True)
        _rect(s, l, Inches(2.20), Inches(3.65), Inches(0.20), col)
        
        _text(s, l + Inches(0.15), Inches(1.93), Inches(3.35), Inches(0.4),
              title, size=12.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        _text(s, l + Inches(0.15), Inches(2.48), Inches(3.35), Inches(0.3),
              sub, size=11, bold=True, color=AMBER, align=PP_ALIGN.CENTER)

        y_p = Inches(2.85)
        _text(s, l + Inches(0.2), y_p, Inches(3.25), Inches(3.4),
              [(t, {"bold": b, "color": WHITE if b else RGBColor(0xCF, 0xD9, 0xEB), "size": 11})
               for t, b in items], line_spacing=1.18)

    _text(s, Inches(0.9), Inches(6.58), Inches(11.5), Inches(0.4),
          "Chi tiết phân công nhiệm vụ và mã nguồn thực hiện: xem docs/TASK_WEEK7.md",
          size=13, bold=True, color=AMBER)
    n()


# --------------------------------------------------------------------------- #
# Main Build Routine
# --------------------------------------------------------------------------- #
def build():
    pngs = [
        W4 / "fig_convergence_dim10.png",
        W4 / "fig_convergence_dim30.png",
        W4 / "fig_convergence_dim50.png",
        W4 / "fig_convergence_multidim.png",
        W4 / "fig_boxplot_dim10.png",
        W4 / "fig_boxplot_dim30.png",
        W4 / "fig_boxplot_dim50.png",
        W4 / "fig_boxplot_multidim.png",
        W56 / "fig_idbo_flowchart.png",
        W56 / "fig_convergence_dim10.png",
        W56 / "fig_convergence_dim30.png",
        W56 / "fig_convergence_dim50.png",
        W56 / "fig_boxplot_dim10.png",
        W56 / "fig_boxplot_dim30.png",
        W56 / "fig_boxplot_dim50.png",
        W56 / "fig_diversity_dim10.png",
        W56 / "fig_diversity_dim30.png",
        W56 / "fig_diversity_dim50.png",
    ]
    flowchart = W56 / "fig_idbo_flowchart.png"
    if not flowchart.exists() and OUT.exists():
        import zipfile
        try:
            with zipfile.ZipFile(OUT, "r") as z:
                if "ppt/media/image9.png" in z.namelist():
                    flowchart.write_bytes(z.read("ppt/media/image9.png"))
        except Exception:
            pass

    missing = [str(p) for p in pngs if not p.exists()]
    if missing:
        print("[LỖI] Thiếu PNG:\n  " + "\n  ".join(missing), file=sys.stderr)
        sys.exit(1)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    total = 31
    n = _page_number(total)

    # 1. Bìa & 2. Tổng quan
    cover(prs, n, total)
    summary(prs, n, total)

    # ================= PHẦN A — TUẦN 4 =================
    divider(prs, n, total, "GIAI ĐOẠN 1",
            "Tuần 4 — Kiểm chứng thuật toán DBO gốc",
            "Đánh giá hiệu năng và tính ổn định trên 6 hàm benchmark chuẩn liên tục, "
            "không gian dim = 10, 30, 50, quy mô M = 30 lượt chạy độc lập.",
            INDIGO, "Tuần 4")

    # 4. Thiết lập Tuần 4
    setup_slide(
        prs, n, total,
        "Thông số cấu hình DBO gốc & Phân công nhiệm vụ",
        "THIẾT LẬP THỰC NGHIỆM", INDIGO,
        params=[
            ("Thuật toán", "Dung Beetle Optimizer gốc (Xue & Shen, 2023)"),
            ("Không gian thử nghiệm", "6 hàm chuẩn: 3 đơn điệu + 3 đa cực trị"),
            ("Số chiều tìm kiếm", "dim = 10, 30, 50"),
            ("Kích thước quần thể", "n_agents = 30 cá thể bọ hung"),
            ("Số vòng lặp tối đa", "max_iter = 500 vòng"),
            ("Số lần lặp độc lập", "M = 30 lần chạy (seed 0 → 29)"),
            ("Tổng số lượt chạy", "6 hàm × 3 dim × 30 runs = 540 lượt chạy"),
            ("Tiêu chí đánh giá", "Cực tiểu hóa (Minimize) — tiệm cận giá trị 0"),
        ],
        who=[
            ("Lê Quang Duy — Trưởng nhóm",
             "Thiết kế kiến trúc DBO, module hóa vòng lặp và tích hợp"),
            ("Hồ Trung Cương",
             "Cài đặt 4 hành vi sinh tồn (lăn phân, sinh sản, kiếm ăn, cướp đoạt)"),
            ("Đặng Nguyễn Minh Đăng",
             "Cài đặt bộ 6 hàm benchmark toán học và tự động hóa thực nghiệm"),
        ],
        note="Bộ hàm thử nghiệm bao gồm: Sphere, Schwefel 2.22, Rosenbrock (đơn điệu); "
             "Rastrigin, Ackley, Griewank (đa cực trị). "
             "Dữ liệu gốc được lưu trữ chi tiết tại experiments/week4/*.csv.",
        footer_label="Tuần 4 · Thiết lập thực nghiệm")

    # 5. Bảng MEAN DBO Tuần 4
    s = _blank(prs)
    _header(s, "Kết quả tối ưu trung bình (Mean Fitness) của DBO gốc",
            "KẾT QUẢ THỰC NGHIỆM", INDIGO)
    rows = [
        ["Hàm mục tiêu", "dim = 10", "dim = 30", "dim = 50", "Đặc điểm hội tụ & Phân tích"],
        ["Sphere", "3,49e-153", "2,06e-158", "5,70e-168", "Hội tụ sâu tiệm cận 0 tuyệt đối — Cài đặt chuẩn xác"],
        ["Schwefel 2.22", "6,70e-82", "3,60e-87", "4,18e-82", "Hội tụ sâu ở mọi số chiều — Tìm kiếm cục bộ cực mạnh"],
        ["Rosenbrock", "5,61", "26,23", "46,65", "Thách thức do thung lũng cong — Giá trị tỉ lệ thuận số chiều"],
        ["Rastrigin", "2,74", "4,85", "0", "Đa cực trị: chiều 50 đạt tuyệt đối 0 trên 100% runs (30/30 seed)"],
        ["Ackley", "4,44e-16", "4,44e-16", "4,44e-16", "Đạt giới hạn sai số dấu phẩy động (machine epsilon), độc lập số chiều"],
        ["Griewank", "0,0349", "0", "0", "Chiều 10 kẹt cực trị nhẹ; chiều 30 và 50 giải quyết triệt để về 0"],
    ]
    align_s5 = {0: PP_ALIGN.LEFT, 1: PP_ALIGN.CENTER, 2: PP_ALIGN.CENTER, 3: PP_ALIGN.CENTER, 4: PP_ALIGN.LEFT}
    table(s, rows, Inches(0.55), Inches(1.4), Inches(12.23), Inches(4.35),
          col_w=[Inches(2.1), Inches(1.85), Inches(1.85), Inches(1.85), Inches(4.58)],
          header_color=INDIGO, body_size=12, row_h=Inches(0.60),
          highlight={(3, 4): (RED, True), (4, 3): (GREEN, True), (6, 2): (GREEN, True), (6, 3): (GREEN, True)},
          align_cols=align_s5)
    
    _rect(s, Inches(0.55), Inches(5.95), Inches(12.23), Inches(0.96), LIGHT,
          rounded=True, line_color=LINE)
    _text(s, Inches(0.80), Inches(6.05), Inches(11.75), Inches(0.78),
          [[("💡 Đánh giá tổng quát:  ", {"bold": True, "color": AMBER, "size": 12.5})],
           [("DBO giải quyết xuất sắc 5/6 bài toán benchmark (tiệm cận và đạt 0 tuyệt đối). "
             "Rosenbrock là điểm nghẽn điển hình của các giải thuật bầy đàn do thung lũng parabol hẹp, "
             "phản ánh hoàn toàn chính xác đặc tính tự nhiên của DBO gốc mà không có sai lệch mã nguồn.",
             {"size": 12, "color": INK})]], line_spacing=1.12)
    _footer(s, "Tuần 4 · Bảng kết quả Mean Fitness", n(), total)

    # 6-13: Các slide hình ảnh Tuần 4
    image_slide(prs, n, total, "Đặc tính hội tụ của DBO trên không gian 10 chiều (dim = 10)",
                "ĐỒ THỊ HỘI TỤ (CONVERGENCE)", INDIGO,
                W4 / "fig_convergence_dim10.png",
                "Sphere và Schwefel đạt mức hội tụ sâu từ 1e-80 đến 1e-150. "
                "Ackley chạm sàn sai số dấu phẩy động 4,44e-16 sau ~100 vòng lặp đầu tiên. "
                "Rosenbrock hội tụ nhanh về vùng đáy phẳng ~5,6 rồi dừng lại do địa hình thung lũng hẹp.",
                "Tuần 4 · Hội tụ dim = 10", tag="6 Hàm Benchmark · dim = 10")

    image_slide(prs, n, total, "Đặc tính hội tụ của DBO trên không gian 30 chiều (dim = 30)",
                "ĐỒ THỊ HỘI TỤ (CONVERGENCE)", INDIGO,
                W4 / "fig_convergence_dim30.png",
                "Griewank đạt nghiệm tối ưu tuyệt đối 0 (đường cong log đứt đoạn khi về 0). "
                "Rastrigin có 29/30 seed tìm kiếm tối ưu rất tốt, chỉ 1/30 seed bị kẹt cục bộ ở ~115 kéo lệch giá trị trung bình. "
                "Rosenbrock duy trì mức nghiệm trung bình ~26,23.",
                "Tuần 4 · Hội tụ dim = 30", tag="6 Hàm Benchmark · dim = 30")

    image_slide(prs, n, total, "Đặc tính hội tụ của DBO trên không gian 50 chiều (dim = 50)",
                "ĐỒ THỊ HỘI TỤ (CONVERGENCE)", INDIGO,
                W4 / "fig_convergence_dim50.png",
                "Cả Rastrigin và Griewank đạt nghiệm 0 tuyệt đối trên 100% số lần chạy (30/30 runs). "
                "Điều này chứng minh khả năng mở rộng không gian tìm kiếm đa cực trị của DBO cực kỳ mạnh mẽ ở số chiều lớn. "
                "Rosenbrock hội tụ ổn định quanh mức 46,65.",
                "Tuần 4 · Hội tụ dim = 50", tag="6 Hàm Benchmark · dim = 50")

    image_slide(prs, n, total, "So sánh đường cong hội tụ DBO chồng 3 mức chiều (10, 30, 50D)",
                "ĐỒ THỊ HỘI TỤ ĐA CHIỀU", INDIGO,
                W4 / "fig_convergence_multidim.png",
                "Trực quan hóa sự tác động của số chiều lên tốc độ tìm kiếm: ở Sphere, chiều cao cần nhiều vòng lặp hơn để gom quần thể; "
                "trong khi ở Rastrigin và Griewank, số chiều lớn (50D) lại giúp thuật toán tránh bẫy cục bộ tốt hơn nhờ không gian lăn phân rộng mở.",
                "Tuần 4 · Hội tụ đa chiều", tag="Đối sánh 10D vs 30D vs 50D")

    image_slide(prs, n, total, "Phân bố sai số nghiệm DBO qua biểu đồ Boxplot (dim = 10)",
                "PHÂN BỐ NGHIỆM (BOXPLOT)", INDIGO,
                W4 / "fig_boxplot_dim10.png",
                "Ackley co lại thành một vạch ngang duy nhất (30/30 runs cùng giá trị 4,44e-16), minh chứng độ ổn định tuyệt đối. "
                "Sphere và Schwefel có hộp sát tiệm cận 0 với phương sai cực bé. "
                "Rosenbrock có dải tứ phân vị rất hẹp (5,3 đến 5,7).",
                "Tuần 4 · Boxplot dim = 10", tag="Phân bố 30 runs · dim = 10")

    image_slide(prs, n, total, "Phân bố sai số nghiệm DBO qua biểu đồ Boxplot (dim = 30)",
                "PHÂN BỐ NGHIỆM (BOXPLOT)", INDIGO,
                W4 / "fig_boxplot_dim30.png",
                "Griewank hoàn toàn không còn hộp do toàn bộ 30 runs đều đạt 0. "
                "Rastrigin xuất hiện 1 ngoại lai (outlier) ở mức ~115 (giải thích cho std = 21). "
                "Rosenbrock có phân bố hộp tập trung chặt chẽ quanh giá trị 26,2.",
                "Tuần 4 · Boxplot dim = 30", tag="Phân bố 30 runs · dim = 30")

    image_slide(prs, n, total, "Phân bố sai số nghiệm DBO qua biểu đồ Boxplot (dim = 50)",
                "PHÂN BỐ NGHIỆM (BOXPLOT)", INDIGO,
                W4 / "fig_boxplot_dim50.png",
                "Cả Rastrigin và Griewank đều không xuất hiện trên thang đo log do toàn bộ kết quả đạt 0 tuyệt đối. "
                "Sphere có phương sai std = 0 trên máy tính do sai số underflow dấu phẩy động (đều tiệm cận 1e-168). "
                "Hộp Rosenbrock dao động ổn định trong khoảng 46 đến 47.",
                "Tuần 4 · Boxplot dim = 50", tag="Phân bố 30 runs · dim = 50")

    image_slide(prs, n, total, "So sánh phân bố sai số Boxplot chồng 3 mức chiều (10, 30, 50D)",
                "PHÂN BỐ NGHIỆM ĐA CHIỀU", INDIGO,
                W4 / "fig_boxplot_multidim.png",
                "Thể hiện rõ quy luật: các hàm đa cực trị (Rastrigin, Griewank) cải thiện độ ổn định khi tăng số chiều; "
                "ngược lại hàm thung lũng Rosenbrock có sai số trung vị tăng tịnh tiến theo số chiều (5,6 → 26,2 → 46,6).",
                "Tuần 4 · Boxplot đa chiều", tag="Đối sánh phân bố 3 mức chiều")

    # 14. Kết luận Tuần 4
    bullets_slide(
        prs, n, total, "Tổng kết đánh giá hiệu năng DBO gốc ở Tuần 4",
        "ĐÁNH GIÁ GIAI ĐOẠN 1", INDIGO,
        items=[
            ("Cài đặt chuẩn xác 100% theo bài báo gốc:",
             "Kết quả thực nghiệm trên 6 hàm toán học khớp hoàn toàn với công bố của Xue & Shen (2023), đạt mức tối ưu sâu trên Sphere, Schwefel, Ackley, Griewank."),
            ("Khả năng tối ưu đa cực trị xuất sắc ở chiều cao:",
             "Trên các địa hình gồ ghề nhiều bẫy như Rastrigin và Griewank ở dim=50, quần thể bọ hung khám phá không gian hiệu quả và đạt nghiệm 0 tuyệt đối trên 100% runs."),
            ("Đặc tính thung lũng hẹp là giới hạn tự nhiên của DBO:",
             "Hàm Rosenbrock có sai số tăng tuyến tính theo số chiều (~5,6 ở 10D → ~46,6 ở 50D). Đây là bài toán thách thức chung của các giải thuật bầy đàn do đáy phẳng cong hẹp."),
            ("Nền tảng vững chắc cho giai đoạn cải tiến IDBO:",
             "Mã nguồn được module hóa rõ ràng giữa thuật toán và bài toán đánh giá, sẵn sàng để bổ sung cơ chế kiểm soát đa dạng quần thể ở Tuần 5–6."),
        ],
        footer_label="Tuần 4 · Tổng kết giai đoạn 1")

    # ================= PHẦN B — TUẦN 5-6 =================
    divider(prs, n, total, "GIAI ĐOẠN 2",
            "Tuần 5–6 — Thuật toán cải tiến IDBO",
            "Tích hợp cơ chế kiểm soát đa dạng quần thể (Diversity), Gaussian Perturbation và "
            "Random Restart; so sánh đối chứng toàn diện với DBO gốc trên 1.080 lượt chạy.",
            TEAL, "Tuần 5–6")

    # 16. Thiết lập Tuần 5-6
    setup_slide(
        prs, n, total,
        "Cơ chế cải tiến IDBO & Cấu hình thí nghiệm đối chứng",
        "THIẾT LẬP CẢI TIẾN", TEAL,
        params=[
            ("Kế thừa nền tảng", "Giữ nguyên 4 hành vi sinh tồn và giao diện optimize()"),
            ("Kiểm soát đa dạng", "Tính chỉ số Diversity sau mỗi vòng lặp"),
            ("Ngưỡng kích hoạt", "Diversity < 10⁻³ (phát hiện quần thể co cụm)"),
            ("Cơ chế 1 (Perturbation)", "Bơm nhiễu Gauss vào 20% cá thể khi chưa trễ"),
            ("Cơ chế 2 (Random Restart)", "Tái sinh ngẫu nhiên 25% cá thể tệ nhất trong [lb, ub]"),
            ("Điều kiện Restart", "Độ trễ trì trệ Stagnation ≥ 25 vòng liên tiếp"),
            ("Bảo toàn Elite", "Cá thể tốt nhất (n_elite = 1) luôn được bảo vệ tuyệt đối"),
            ("Quy mô đối chứng", "2 thuật toán × 6 hàm × 3 dim × 30 runs = 1.080 lượt"),
        ],
        who=[
            ("Lê Quang Duy — Trưởng nhóm",
             "Tích hợp kiến trúc IDBO, bảo toàn giao diện gọi thuật toán"),
            ("Hồ Trung Cương",
             "Cài đặt bộ đo Diversity, cơ chế Perturbation và Random Restart"),
            ("Đặng Nguyễn Minh Đăng",
             "Chạy thực nghiệm đối chứng DBO vs IDBO, thu thập số liệu CSV"),
        ],
        note="Thí nghiệm so sánh theo giao thức Fixed-Iteration (cùng số cá thể n_agents=30, "
             "max_iter=500, cùng bộ hạt giống seed ngẫu nhiên). "
             "Quy ước Hòa nếu chênh lệch tương đối giữa Mean IDBO và DBO < 1%.",
        footer_label="Tuần 5–6 · Thiết lập cải tiến")

    # 17. Sơ đồ IDBO (Flowchart Vector)
    flowchart_slide(prs, n, total)

    # 18. Tần suất kích hoạt
    s = _blank(prs)
    _header(s, "Tần suất kích hoạt cơ chế Perturbation và Random Restart",
            "KẾT QUẢ KÍCH HOẠT", TEAL)
    rows = [
        ["Hàm mục tiêu", "dim = 10 (Perturb / Restart)", "dim = 30", "dim = 50", "Đặc điểm kích hoạt cơ chế"],
        ["Sphere", "0 / 0,53", "0 / 0,07", "0 / 0,07", "Quần thể co cụm nhanh → Kích hoạt restart trung bình 0,53 lần/run"],
        ["Schwefel 2.22", "0 / 0,20", "0 / 0,03", "0 / 0,07", "Kích hoạt restart nhẹ ở 10D khi quần thể hội tụ tiệm cận 0"],
        ["Rosenbrock", "0 / 0", "0,10 / 0", "0,07 / 0", "Chỉ kích hoạt perturb thăm dò (0,10 lần ở 30D và 0,07 lần ở 50D)"],
        ["Rastrigin", "0 / 0", "0 / 0", "0 / 0", "Độ đa dạng tự nhiên rất cao (~0,15) → Hoàn toàn không kích hoạt (0,00)"],
        ["Ackley", "0 / 0", "0 / 0", "0 / 0", "Hội tụ ổn định → Không kích hoạt ngoài ý muốn (0,00)"],
        ["Griewank", "0 / 0", "0 / 0,03", "0 / 0,10", "Không gian phẳng ở chiều cao → Kích hoạt restart nhẹ ở 50D (0,10)"],
    ]
    align_s18 = {0: PP_ALIGN.LEFT, 1: PP_ALIGN.CENTER, 2: PP_ALIGN.CENTER, 3: PP_ALIGN.CENTER, 4: PP_ALIGN.LEFT}
    table(s, rows, Inches(0.55), Inches(1.4), Inches(12.23), Inches(4.35),
          col_w=[Inches(2.1), Inches(2.6), Inches(1.85), Inches(1.85), Inches(3.83)],
          header_color=TEAL, body_size=11.5, row_h=Inches(0.60),
          highlight={(1, 1): (RED, True), (3, 2): (AMBER, True), (4, 1): (GREEN, False), (5, 1): (GREEN, False)},
          align_cols=align_s18)
    
    _rect(s, Inches(0.55), Inches(5.95), Inches(12.23), Inches(0.96), LIGHT,
          rounded=True, line_color=LINE)
    _text(s, Inches(0.80), Inches(6.05), Inches(11.75), Inches(0.78),
          [[("💡 Phân tích cơ chế tự động:  ", {"bold": True, "color": AMBER, "size": 12.5})],
           [("Trên 15/18 cấu hình, cơ chế ngẫu nhiên ở trạng thái nghỉ (0/0). "
             "Cơ chế chỉ can thiệp khi quần thể thực sự co cụm (Sphere 10D đạt 0,53 lần restart/run). "
             "Điều này chứng minh IDBO hoạt động có chọn lọc, không gây xáo trộn vô ích trên các hàm hội tụ tốt.",
             {"size": 12, "color": INK})]], line_spacing=1.12)
    _footer(s, "Tuần 5–6 · Tần suất kích hoạt cơ chế", n(), total)

    # 19-27: Các slide hình ảnh Tuần 5-6
    image_slide(prs, n, total, "So sánh đường cong hội tụ DBO vs IDBO (dim = 10)",
                "SO SÁNH HỘI TỤ (CONVERGENCE)", TEAL,
                W56 / "fig_convergence_dim10.png",
                "Đường màu cam (IDBO) chồng khít lên đường màu xanh (DBO) trên cả 6 hàm. "
                "IDBO không làm giảm tốc độ hội tụ tự nhiên của DBO gốc. "
                "Ở Sphere 10D dù có restart 0,53 lần/run nhưng chất lượng nghiệm cuối cùng vẫn được bảo toàn xuất sắc.",
                "Tuần 5–6 · Hội tụ dim = 10", tag="DBO vs IDBO · dim = 10")

    image_slide(prs, n, total, "So sánh đường cong hội tụ DBO vs IDBO (dim = 30)",
                "SO SÁNH HỘI TỤ (CONVERGENCE)", TEAL,
                W56 / "fig_convergence_dim30.png",
                "Quá trình hội tụ của hai thuật toán hoàn toàn đồng pha. "
                "Griewank cùng về 0 tuyệt đối; Rosenbrock cùng dừng ở mức ~26,23. "
                "IDBO không làm phân rã cấu trúc nghiệm của DBO.",
                "Tuần 5–6 · Hội tụ dim = 30", tag="DBO vs IDBO · dim = 30")

    image_slide(prs, n, total, "So sánh đường cong hội tụ DBO vs IDBO (dim = 50)",
                "SO SÁNH HỘI TỤ (CONVERGENCE)", TEAL,
                W56 / "fig_convergence_dim50.png",
                "Ở số chiều lớn (50D), cả hai thuật toán tiếp tục duy trì mức nghiệm tuyệt đối 0 trên Rastrigin và Griewank. "
                "Ackley chạm sàn sai số dấu phẩy động 4,44e-16. Kết quả đối chứng giữa hai thuật toán là tương đương hoàn toàn.",
                "Tuần 5–6 · Hội tụ dim = 50", tag="DBO vs IDBO · dim = 50")

    image_slide(prs, n, total, "So sánh phân bố sai số nghiệm Boxplot giữa DBO và IDBO (dim = 10)",
                "SO SÁNH PHÂN BỐ (BOXPLOT)", TEAL,
                W56 / "fig_boxplot_dim10.png",
                "Từng cặp hộp xanh (DBO) và cam (IDBO) đặt cạnh nhau có trung vị, tứ phân vị và các điểm ngoại lai trùng khớp nhau. "
                "Đây là bằng chứng trực quan rõ ràng nhất khẳng định IDBO không làm biến động phân bố nghiệm của DBO.",
                "Tuần 5–6 · Boxplot dim = 10", tag="Hộp trái: DBO | Hộp phải: IDBO")

    image_slide(prs, n, total, "So sánh phân bố sai số nghiệm Boxplot giữa DBO và IDBO (dim = 30)",
                "SO SÁNH PHÂN BỐ (BOXPLOT)", TEAL,
                W56 / "fig_boxplot_dim30.png",
                "Hai hộp Rosenbrock đặt khít nhau ở mức ~26,2. "
                "Rastrigin có cùng đúng 1 điểm ngoại lai lớn do dùng chung bộ seed ngẫu nhiên độc lập. "
                "Không có bất kỳ hàm nào cho thấy sự suy giảm tính ổn định.",
                "Tuần 5–6 · Boxplot dim = 30", tag="Hộp trái: DBO | Hộp phải: IDBO")

    image_slide(prs, n, total, "So sánh phân bố sai số nghiệm Boxplot giữa DBO và IDBO (dim = 50)",
                "SO SÁNH PHÂN BỐ (BOXPLOT)", TEAL,
                W56 / "fig_boxplot_dim50.png",
                "Toàn bộ 6 hàm ở chiều 50 tiếp tục duy trì phân bố tương đương tuyệt đối: "
                "Rastrigin và Griewank đạt 0 trên cả hai thuật toán; Rosenbrock cùng đạt trung vị 46,6. "
                "Kết luận đối chứng: Hòa 18/18 cấu hình.",
                "Tuần 5–6 · Boxplot dim = 50", tag="Hộp trái: DBO | Hộp phải: IDBO")

    image_slide(prs, n, total, "Biến thiên độ đa dạng quần thể (Diversity) của IDBO (dim = 10)",
                "ĐỘ ĐA DẠNG QUẦN THỂ (DIVERSITY)", TEAL,
                W56 / "fig_diversity_dim10.png",
                "Hàm Rastrigin (đường đỏ) giữ độ đa dạng tự nhiên rất cao ~0,15, nằm cách xa ngưỡng 10⁻³ nên không kích hoạt can thiệp. "
                "Hàm Sphere (đường xanh) giảm dần về sát ngưỡng rồi nhích lên hình răng cưa từ vòng ~350, minh chứng cơ chế Restart hoạt động chính xác.",
                "Tuần 5–6 · Diversity dim = 10", tag="Sphere (đơn điệu) vs Rastrigin (đa cực)")

    image_slide(prs, n, total, "Biến thiên độ đa dạng quần thể (Diversity) của IDBO (dim = 30)",
                "ĐỘ ĐA DẠNG QUẦN THỂ (DIVERSITY)", TEAL,
                W56 / "fig_diversity_dim30.png",
                "Ở 30 chiều, không gian tìm kiếm rộng lớn hơn khiến quần thể tự nhiên duy trì sự phân tán tốt hơn; "
                "Sphere giảm chậm hơn so với dim 10 (tần suất restart giảm từ 0,53 xuống 0,07 lần/run). "
                "Rastrigin vẫn duy trì đa dạng cao ổn định.",
                "Tuần 5–6 · Diversity dim = 30", tag="Độ đa dạng trên không gian 30D")

    image_slide(prs, n, total, "Biến thiên độ đa dạng quần thể (Diversity) của IDBO (dim = 50)",
                "ĐỘ ĐA DẠNG QUẦN THỂ (DIVERSITY)", TEAL,
                W56 / "fig_diversity_dim50.png",
                "Xu hướng ở dim 50 đồng nhất với dim 30: cơ chế IDBO ở trạng thái nghỉ trên hầu hết các hàm mục tiêu. "
                "Điều này lý giải một cách khoa học tại sao kết quả của IDBO tương đương DBO trên bộ benchmark này: "
                "không phải do lỗi thuật toán mà do bài toán trơn chưa cần kích hoạt cơ chế thoát bẫy.",
                "Tuần 5–6 · Diversity dim = 50", tag="Độ đa dạng trên không gian 50D")

    # 28. Bảng so sánh MEAN DBO vs IDBO
    s = _blank(prs)
    _header(s, "So sánh kết quả tối ưu trung bình (Mean Fitness) giữa DBO và IDBO",
            "SO SÁNH ĐỐI CHỨNG", TEAL)
    rows = [
        ["Hàm mục tiêu", "dim = 10 (DBO vs IDBO)", "dim = 30 (DBO vs IDBO)", "dim = 50 (DBO vs IDBO)", "Kết luận so sánh"],
        ["Sphere", "3,49e-153 | 3,49e-153", "2,06e-158 | 2,06e-158", "5,70e-168 | 5,70e-168", "Hòa (3/3 cấu hình)"],
        ["Schwefel 2.22", "6,70e-82 | 6,70e-82", "3,60e-87 | 3,60e-87", "4,18e-82 | 4,18e-82", "Hòa (3/3 cấu hình)"],
        ["Rosenbrock", "5,611 | 5,611", "26,23 | 26,23", "46,65 | 46,65", "Hòa (3/3 cấu hình)"],
        ["Rastrigin", "2,741 | 2,741", "4,847 | 4,847", "0 | 0", "Hòa (3/3 cấu hình)"],
        ["Ackley", "4,44e-16 | 4,44e-16", "4,44e-16 | 4,44e-16", "4,44e-16 | 4,44e-16", "Hòa (3/3 cấu hình)"],
        ["Griewank", "0,0349 | 0,0349", "0 | 0", "0 | 0", "Hòa (3/3 cấu hình)"],
    ]
    align_s28 = {0: PP_ALIGN.LEFT, 1: PP_ALIGN.CENTER, 2: PP_ALIGN.CENTER, 3: PP_ALIGN.CENTER, 4: PP_ALIGN.CENTER}
    table(s, rows, Inches(0.55), Inches(1.4), Inches(12.23), Inches(4.35),
          col_w=[Inches(2.1), Inches(2.8), Inches(2.8), Inches(2.8), Inches(1.73)],
          header_color=TEAL, body_size=11.5, row_h=Inches(0.60),
          highlight={(r, 4): (GREEN, True) for r in range(1, 7)},
          align_cols=align_s28)
    
    _rect(s, Inches(0.55), Inches(5.95), Inches(12.23), Inches(0.96), LIGHT,
          rounded=True, line_color=LINE)
    _text(s, Inches(0.80), Inches(6.05), Inches(11.75), Inches(0.78),
          [[("💡 Đánh giá khoa học khách quan:  ", {"bold": True, "color": AMBER, "size": 12.5})],
           [("Trên toàn bộ 18/18 cấu hình thực nghiệm (6 hàm × 3 mức chiều), IDBO và DBO đều đạt kết quả Hòa (chênh lệch Mean < 1%). "
             "Kết quả này khẳng định IDBO bảo toàn tuyệt đối chất lượng nghiệm của DBO gốc, không làm giảm tốc độ hội tụ "
             "và kiểm soát rủi ro phân rã nghiệm thành công 100%.",
             {"size": 12, "color": INK})]], line_spacing=1.12)
    _footer(s, "Tuần 5–6 · Bảng đối chứng DBO vs IDBO", n(), total)

    # 29. Phân tích chi phí tính toán & Lý do hòa
    bullets_slide(
        prs, n, total, "Đánh giá chi phí tính toán & Bản chất tương đương nghiệm",
        "PHÂN TÍCH CHUYÊN SÂU", TEAL,
        items=[
            ("Thời gian thực thi tăng trong mức cho phép (15–20%):",
             "Thời gian chạy của IDBO tăng nhẹ (ví dụ Sphere 10D từ 0,27s lên 0,32s/run). Nguyên nhân hoàn toàn do thuật toán phải đánh giá lại hàm mục tiêu khi có cá thể bị can thiệp."),
            ("Tiết kiệm triệt để số lần đánh giá hàm mục tiêu (Evals):",
             "Thuật toán DBO gốc tiêu thụ cố định 15.030,0 evals. IDBO chỉ tiêu thụ trung bình từ 15.030,0 đến 15.034,3 evals (tăng cao nhất vỏn vẹn 4,3 evals/run ở Sphere 10D, tương đương mức tăng 0,028% — gần như bằng 0)."),
            ("Cơ chế kích hoạt có điều kiện hoạt động chuẩn xác:",
             "Do chỉ can thiệp khi Diversity < 10⁻³ và Stagnation ≥ 25, quần thể bọ hung trên các hàm hội tụ tốt không bị xáo trộn vô ích, tránh lãng phí năng lực tính toán."),
            ("Định vị giá trị thực tế cho bài toán Tuần 7:",
             "Kết quả Hòa trên benchmark liên tục là hoàn toàn hợp lý vì DBO vốn đã giải quyết rất tốt các hàm này. Sức mạnh thoát bẫy cực trị của IDBO sẽ phát huy tối đa ở không gian rời rạc phức tạp của bài toán thực đơn dinh dưỡng."),
        ],
        footer_label="Tuần 5–6 · Phân tích chi phí tính toán")

    # 30. Kết luận 4 thẻ
    conclusion_cards(prs, n, total)

    # 31. Kế hoạch Tuần 7 (Roadmap)
    roadmap_week7(prs, n, total)

    used = n.count()
    if used != total:
        print(f"[CẢNH BÁO] Số slide tạo ra = {used}, cấu hình total = {total}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"[OK] Đã xuất thành công: {OUT}  ({used} slides, {len(pngs)} PNG)")


if __name__ == "__main__":
    build()
