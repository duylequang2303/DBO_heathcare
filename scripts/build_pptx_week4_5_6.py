"""Dựng slide báo cáo tuần 4-5-6 (DBO / IDBO) từ số liệu CSV.

Cấu trúc mỗi phần: thiết lập (dùng gì, ai làm) -> bảng kết quả -> hình kèm
nhận xét -> kết luận. Mỗi PNG một slide, bảng chỉ hiển thị MEAN.

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
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Slide_Tuan_4_5_6_DBO_IDBO.pptx"
W4 = ROOT / "experiments" / "week4"
W56 = ROOT / "experiments" / "week5_6"

# Bảng màu
INDIGO = RGBColor(0x1F, 0x2A, 0x44)
INDIGO2 = RGBColor(0x30, 0x3E, 0x62)
AMBER = RGBColor(0xE0, 0x94, 0x2E)
TEAL = RGBColor(0x2C, 0x7A, 0x7A)
GREEN = RGBColor(0x2E, 0x7D, 0x5B)
RED = RGBColor(0xB8, 0x43, 0x2A)
INK = RGBColor(0x1C, 0x23, 0x33)
MUTED = RGBColor(0x64, 0x6C, 0x7E)
LIGHT = RGBColor(0xF4, 0xF6, 0xFB)
LINE = RGBColor(0xD8, 0xDF, 0xEC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CREAM = RGBColor(0xFD, 0xF4, 0xE2)
PANEL = RGBColor(0xEC, 0xEF, 0xF6)

FONT = "Calibri"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


# --------------------------------------------------------------------------- #
# Helpers
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


def _rect(slide, l, t, w, h, color, rounded=False, line_color=None):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, l, t, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if line_color is not None:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(1)
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
    _text(slide, Inches(0.55), Inches(0.32), Inches(12.23), Inches(0.28),
          kicker, size=12, bold=True, color=accent)
    _text(slide, Inches(0.55), Inches(0.62), Inches(12.23), Inches(0.5),
          title, size=25, bold=True, color=INDIGO)
    _rect(slide, Inches(0.55), Inches(1.16), Inches(12.23), Pt(1.4), LINE)


def _footer(slide, label, page, total):
    _rect(slide, Inches(0.55), Inches(7.05), Inches(12.23), Pt(1.2), LINE)
    _text(slide, Inches(0.55), Inches(7.12), Inches(9), Inches(0.3),
          label, size=10, color=MUTED)
    _text(slide, Inches(11.0), Inches(7.12), Inches(1.78), Inches(0.3),
          f"{page} / {total}", size=10, bold=True, color=MUTED,
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
# Slide builders
# --------------------------------------------------------------------------- #
def cover(prs, n, total):
    s = _blank(prs)
    _rect(s, 0, 0, SLIDE_W, SLIDE_H, INDIGO)
    _rect(s, 0, 0, SLIDE_W, Inches(0.2), AMBER)
    _rect(s, Inches(0.9), Inches(1.35), Inches(0.08), Inches(0.34), AMBER)
    _text(s, Inches(1.15), Inches(1.32), Inches(11), Inches(0.34),
          "KHÓA LUẬN CỐT CNTT · MÃ ĐỀ TÀI CNTT-KLCN142 · 2025–2026",
          size=14, bold=True, color=AMBER)
    _text(s, Inches(0.9), Inches(2.0), Inches(11.5), Inches(1.5),
          [[("Đánh giá DBO và IDBO\n", {})],
           [("trên bộ hàm benchmark chuẩn", {})]],
          size=40, bold=True, color=WHITE, line_spacing=1.05)
    _rect(s, Inches(0.9), Inches(3.75), Inches(2.2), Pt(3), AMBER)
    _text(s, Inches(0.9), Inches(4.05), Inches(11.5), Inches(0.5),
          "Báo cáo kết quả thực nghiệm · Tuần 4 · Tuần 5–6",
          size=19, color=RGBColor(0xC9, 0xD5, 0xEA))
    _text(s, Inches(0.9), Inches(4.95), Inches(11.5), Inches(1.4),
          [[("Đề tài: Hệ thống đề xuất thực đơn dinh dưỡng cá nhân hóa bằng IDBO", {})],
           [("GVHD: ThS. Đinh Nguyễn Trọng Nghĩa", {})],
           [("Nhóm thực hiện: Lê Quang Duy · Đặng Nguyễn Minh Đăng · Hồ Trung Cương",
             {"bold": True, "color": WHITE})]],
          size=15, color=RGBColor(0xC9, 0xD5, 0xEA), line_spacing=1.25)
    _text(s, Inches(0.9), Inches(6.65), Inches(11.5), Inches(0.4),
          "Nguồn số liệu: 540 lần chạy DBO (tuần 4) + 1.080 lần chạy DBO/IDBO "
          "(tuần 5–6) · M = 30 · dim = 10, 30, 50",
          size=12, color=RGBColor(0x9F, 0xB0, 0xCE))
    n()


def summary(prs, n, total):
    s = _blank(prs)
    _header(s, "Tóm tắt: dùng gì — kết quả — ai làm", "TOÀN CẢNH HAI TUẦN", INDIGO)

    # KPI
    kpis = [
        ("6", "hàm benchmark", "3 đơn điệu + 3 đa cực trị", INDIGO),
        ("1.620", "lần chạy", "540 DBO + 1.080 DBO/IDBO", TEAL),
        ("18", "ô đều HÒA", "IDBO không lệch DBO (1%)", GREEN),
        ("15–20%", "IDBO chậm hơn", "do gọi thêm objective", RED),
    ]
    for i, (num, lab, sub, col) in enumerate(kpis):
        l = Inches(0.55 + i * 3.11)
        _rect(s, l, Inches(1.4), Inches(2.93), Inches(1.28), LIGHT, rounded=True)
        _rect(s, l, Inches(1.4), Inches(0.08), Inches(1.28), col)
        _text(s, l + Inches(0.22), Inches(1.52), Inches(2.6), Inches(0.5),
              num, size=26, bold=True, color=col)
        _text(s, l + Inches(0.22), Inches(2.05), Inches(2.6), Inches(0.3),
              lab, size=13, bold=True, color=INK)
        _text(s, l + Inches(0.22), Inches(2.33), Inches(2.65), Inches(0.3),
              sub, size=10.5, color=MUTED)

    rows = [
        ["", "Dùng gì", "Kết quả chính", "Ai làm"],
        ["Tuần 4", "DBO gốc (4 hành vi), 6 hàm, dim 10/30/50, M=30",
         "Cài đặt đúng; Rosenbrock là điểm yếu (~5,6/26,2/46,6)",
         "Duy — khung; Cương — hành vi; Đăng — benchmark"],
        ["Tuần 5–6", "IDBO = DBO + perturb/restart khi diversity < 1e-3",
         "18/18 ô hòa DBO; IDBO chậm hơn 15–20%",
         "Duy — khung; Cương — cơ chế; Đăng — thí nghiệm"],
    ]
    table(s, rows, Inches(0.55), Inches(2.95), Inches(12.23), Inches(2.9),
          col_w=[Inches(1.5), Inches(3.5), Inches(4.0), Inches(3.23)],
          header_color=INDIGO, body_size=12, row_h=Inches(0.95))
    _footer(s, "Tóm tắt", n(), total)


def divider(prs, n, total, tag, title, subtitle, accent, footer_label):
    s = _blank(prs)
    _rect(s, 0, 0, SLIDE_W, SLIDE_H, accent)
    _rect(s, 0, 0, Inches(0.28), SLIDE_H, AMBER)
    _text(s, Inches(1.1), Inches(2.35), Inches(11), Inches(0.5),
          tag, size=18, bold=True, color=AMBER)
    _text(s, Inches(1.1), Inches(2.95), Inches(11), Inches(1.2),
          title, size=40, bold=True, color=WHITE)
    _text(s, Inches(1.1), Inches(4.25), Inches(10.8), Inches(0.8),
          subtitle, size=17, color=RGBColor(0xCF, 0xDA, 0xEE))
    n()


def setup_slide(prs, n, total, title, kicker, accent, params, who, note,
                footer_label):
    s = _blank(prs)
    _header(s, title, kicker, accent)
    # cột tham số
    _rect(s, Inches(0.55), Inches(1.5), Inches(6.05), Inches(4.5), LIGHT,
          rounded=True)
    _text(s, Inches(0.85), Inches(1.7), Inches(5.5), Inches(0.4),
          "THIẾT LẬP", size=13, bold=True, color=accent)
    y = 2.05
    for k, v in params:
        _text(s, Inches(0.85), Inches(y), Inches(2.15), Inches(0.4),
              k, size=13, bold=True, color=INK)
        _text(s, Inches(2.95), Inches(y), Inches(3.45), Inches(0.4),
              v, size=13, color=INDIGO2)
        y += 0.5
    # cột phân công
    _rect(s, Inches(6.85), Inches(1.5), Inches(5.93), Inches(4.5), WHITE,
          rounded=True, line_color=LINE)
    _text(s, Inches(7.15), Inches(1.7), Inches(5.3), Inches(0.4),
          "PHÂN CÔNG", size=13, bold=True, color=accent)
    y = 2.05
    for name, task in who:
        _text(s, Inches(7.15), Inches(y), Inches(5.3), Inches(0.4),
              [(name + " — ", {"bold": True, "color": INDIGO}),
               (task, {"color": INK})], size=13)
        y += 0.5
    _text(s, Inches(7.15), Inches(3.75), Inches(5.35), Inches(2.0),
          note, size=12, color=MUTED, line_spacing=1.15)
    _footer(s, footer_label, n(), total)


def table(slide, rows, l, t, w, h, col_w, header_color, body_size=12,
          row_h=None, highlight=None, header_size=12.5):
    n_row, n_col = len(rows), len(rows[0])
    shape = slide.shapes.add_table(n_row, n_col, l, t, w, h)
    tbl = shape.table
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = cw
    if row_h is not None:
        for r in range(n_row):
            tbl.rows[r].height = row_h if r else Inches(0.5)
    highlight = highlight or {}
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = Inches(0.1)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
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
    box_l, box_t = Inches(0.55), Inches(1.35)
    box_w, box_h = Inches(12.23), Inches(4.45)
    w, h = _fit(png, box_w, box_h)
    left = int(box_l + (box_w - w) / 2)
    top = int(box_t + (box_h - h) / 2)
    s.shapes.add_picture(str(png), left, top, width=w, height=h)
    if tag:
        badge = _rect(s, Inches(0.55), Inches(1.32), Inches(1.35), Inches(0.34),
                      accent, rounded=True)
        _text(s, Inches(0.55), Inches(1.32), Inches(1.35), Inches(0.34),
              tag, size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
              anchor=MSO_ANCHOR.MIDDLE)
    # khung nhận xét
    _rect(s, Inches(0.55), Inches(5.98), Inches(12.23), Inches(1.02), CREAM,
          rounded=True)
    _rect(s, Inches(0.55), Inches(5.98), Inches(0.09), Inches(1.02), AMBER)
    _text(s, Inches(0.82), Inches(6.08), Inches(11.8), Inches(0.85),
          [[("Nhận xét.  ", {"bold": True, "color": AMBER}), (remark, {})]],
          size=13, color=INK, line_spacing=1.1)
    _footer(s, footer_label, n(), total)


def bullets_slide(prs, n, total, title, kicker, accent, items, footer_label,
                  size=17):
    s = _blank(prs)
    _header(s, title, kicker, accent)
    box = s.shapes.add_textbox(Inches(0.7), Inches(1.65), Inches(11.95),
                               Inches(5.1))
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
            rh.text = head
            _style_run(rh, size, True, INDIGO)
        rb = p.add_run()
        rb.text = body
        _style_run(rb, size, False, INK)
    _footer(s, footer_label, n(), total)


def closing(prs, n, total):
    s = _blank(prs)
    _rect(s, 0, 0, SLIDE_W, SLIDE_H, INDIGO)
    _rect(s, 0, 0, Inches(0.28), SLIDE_H, AMBER)
    _text(s, Inches(1.1), Inches(2.3), Inches(11), Inches(1.0),
          "Kết luận", size=40, bold=True, color=WHITE)
    _rect(s, Inches(1.1), Inches(3.5), Inches(2.0), Pt(3), AMBER)
    _text(s, Inches(1.1), Inches(3.85), Inches(11), Inches(2.4),
          [[("DBO cài đặt đúng và ổn định trên cả 6 hàm, dim 10/30/50.", {})],
           [("IDBO không làm xấu DBO: 18/18 ô hòa, đánh đổi 15–20% thời gian.",
             {})],
           [("Cơ chế ngẫu nhiên gần như không kích hoạt trên benchmark trơn; "
             "giá trị thực nằm ở bài toán thực đơn (tuần 7).", {})]],
          size=19, color=RGBColor(0xD5, 0xDF, 0xF0), line_spacing=1.4)
    _text(s, Inches(1.1), Inches(6.3), Inches(11), Inches(0.4),
          "Tuần 7: gắn fitness thực đơn vào optimize() — xem docs/TASK_WEEK7.md",
          size=14, bold=True, color=AMBER)
    n()


# --------------------------------------------------------------------------- #
# Build
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
    missing = [str(p) for p in pngs if not p.exists()]
    if missing:
        print("[LỖI] Thiếu PNG:\n  " + "\n  ".join(missing), file=sys.stderr)
        sys.exit(1)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    total = 31
    n = _page_number(total)

    cover(prs, n, total)
    summary(prs, n, total)

    # ================= PHẦN A — TUẦN 4 =================
    divider(prs, n, total, "PHẦN A", "Tuần 4 — DBO gốc trên hàm benchmark",
            "Kiểm chứng cài đặt DBO (Xue & Shen, 2023) trên 6 hàm chuẩn, "
            "dim 10/30/50, M = 30 lần chạy.", INDIGO, "Tuần 4")

    setup_slide(
        prs, n, total,
        "Thiết lập thí nghiệm tuần 4", "DÙNG GÌ", INDIGO,
        params=[
            ("Thuật toán", "DBO gốc, 4 hành vi"),
            ("Bộ hàm", "6 hàm: 3 đơn điệu + 3 đa cực trị"),
            ("Số chiều", "dim = 10, 30, 50 (bỏ dim = 2)"),
            ("Quần thể", "n_agents = 30"),
            ("Vòng lặp", "max_iter = 500"),
            ("Số lần lặp lại", "M = 30 seed độc lập"),
            ("Tổng số lần chạy", "6 hàm × 3 dim × 30 = 540"),
            ("Tiêu chí", "minimize — càng gần 0 càng tốt"),
        ],
        who=[
            ("Lê Quang Duy", "khung DBO, vòng lặp chính, tích hợp"),
            ("Hồ Trung Cương", "4 hành vi (ball-rolling, reproduction, "
                               "foraging, thieving)"),
            ("Đặng Nguyễn Minh Đăng", "bộ hàm benchmark + script thí nghiệm"),
        ],
        note="Hàm mục tiêu: Sphere, Schwefel 2.22, Rosenbrock, Rastrigin, "
             "Ackley, Griewank. Dữ liệu gốc: experiments/week4/*.csv",
        footer_label="Tuần 4 · Thiết lập")

    # bảng MEAN DBO
    s = _blank(prs)
    _header(s, "Bảng MEAN DBO — 6 hàm × 3 chiều", "KẾT QUẢ", INDIGO)
    rows = [
        ["Hàm", "dim = 10", "dim = 30", "dim = 50", "Đọc số"],
        ["Sphere", "3,49e-153", "2,06e-158", "5,70e-168", "Hội tụ sâu — cài đặt đúng"],
        ["Schwefel 2.22", "6,70e-82", "3,60e-87", "4,18e-82", "Về gần 0 ở mọi chiều"],
        ["Rosenbrock", "5,61", "26,23", "46,65", "Không về 0 — độ khó tăng theo dim"],
        ["Rastrigin", "2,74", "4,85", "0", "50D: cả 30/30 seed đạt 0"],
        ["Ackley", "4,44e-16", "4,44e-16", "4,44e-16", "Sàn máy tính, mọi dim giống nhau"],
        ["Griewank", "0,0349", "0", "0", "10D còn sót; 30D và 50D hết"],
    ]
    table(s, rows, Inches(0.55), Inches(1.5), Inches(12.23), Inches(4.4),
          col_w=[Inches(2.1), Inches(1.95), Inches(1.95), Inches(1.95),
                 Inches(4.28)],
          header_color=INDIGO, body_size=12.5, row_h=Inches(0.62),
          highlight={(3, 4): (RED, True), (1, 5): (GREEN, False)})
    _text(s, Inches(0.55), Inches(6.15), Inches(12.23), Inches(0.5),
          [[("Nhận xét.  ", {"bold": True, "color": AMBER}),
            ("DBO đạt gần 0 tuyệt đối ở các hàm đơn điệu và Ackley. "
             "Rosenbrock là điểm yếu duy nhất: mean bám ~ số chiều. "
             "Rastrigin bất ổn ở dim 10/30 nhưng đạt 0 tuyệt đối ở dim 50.",
             {})]], size=13.5, color=INK, line_spacing=1.1)
    _footer(s, "Tuần 4 · Kết quả", n(), total)

    image_slide(prs, n, total, "Hội tụ DBO — dim = 10", "HÌNH 1/4", INDIGO,
                W4 / "fig_convergence_dim10.png",
                "Sphere/Schwefel về 1e-80…1e-150; Ackley chạm sàn 4,4e-16 sau "
                "~100 vòng. Rosenbrock dừng ở ~5,6 vì thung lũng hẹp. "
                "Rastrigin/Griewank còn kẹt cực tiểu cục bộ ở chiều thấp.",
                "Tuần 4 · Hội tụ dim 10")

    image_slide(prs, n, total, "Hội tụ DBO — dim = 30", "HÌNH 2/4", INDIGO,
                W4 / "fig_convergence_dim30.png",
                "Rosenbrock tệ hơn dim 10 (≈26, gần bằng số chiều). Griewank "
                "đạt 0 ở dim 30 (tốt hơn dim 10). Rastrigin mean 4,85 nhưng "
                "std 21 — chỉ 1/30 seed kẹt ở ~115 kéo lệch toàn bộ.",
                "Tuần 4 · Hội tụ dim 30")

    image_slide(prs, n, total, "Hội tụ DBO — dim = 50", "HÌNH 3/4", INDIGO,
                W4 / "fig_convergence_dim50.png",
                "Rastrigin và Griewank về 0 trên cả 30/30 seed (đường log đứt "
                "đoạn tại 0). Rosenbrock ≈ 46,6 — càng nhiều chiều càng xa 0. "
                "Ackley vẫn ở sàn máy. DBO mạnh ở hàm đa cực, yếu ở Rosenbrock.",
                "Tuần 4 · Hội tụ dim 50")

    image_slide(prs, n, total, "Hội tụ DBO — chồng 3 chiều", "HÌNH 4/4", INDIGO,
                W4 / "fig_convergence_multidim.png",
                "Rosenbrock tách rõ theo chiều (5,6 → 26 → 46,6). Sphere dim 50 "
                "hội tụ muộn hơn dim 10 vì không gian tìm kiếm rộng hơn — "
                "không phải thuật toán kém đi. Đọc mỗi khung là 3 đường dim, "
                "không phải 3 thuật toán.",
                "Tuần 4 · Hội tụ 3 chiều")

    image_slide(prs, n, total, "Boxplot DBO — dim = 10", "HÌNH 5/8", INDIGO,
                W4 / "fig_boxplot_dim10.png",
                "Ackley là một vạch duy nhất (30/30 seed cùng giá trị) → ổn "
                "định tuyệt đối. Rastrigin có 3 outlier ~10–17. Rosenbrock hộp "
                "chặt 5,3–5,7. Sphere/Schwefel hộp sát 0, vài outlier nhỏ.",
                "Tuần 4 · Boxplot dim 10")

    image_slide(prs, n, total, "Boxplot DBO — dim = 30", "HÌNH 6/8", INDIGO,
                W4 / "fig_boxplot_dim30.png",
                "Rastrigin bất ổn nhất: 1 outlier ~115 kéo std lên 21. "
                "Rosenbrock hộp rất chặt quanh 26 → ổn định nhưng lệch xa 0. "
                "Griewank đạt 0 hoàn toàn.",
                "Tuần 4 · Boxplot dim 30")

    image_slide(prs, n, total, "Boxplot DBO — dim = 50", "HÌNH 7/8", INDIGO,
                W4 / "fig_boxplot_dim50.png",
                "Rastrigin/Griewank hộp biến mất vì giá trị = 0 (thang log). "
                "Rosenbrock quanh 46–47. Sphere std = 0 do underflow float — "
                "cả 30 seed đều siêu nhỏ, không phải mất đa dạng.",
                "Tuần 4 · Boxplot dim 50")

    image_slide(prs, n, total, "Boxplot DBO — chồng 3 chiều", "HÌNH 8/8", INDIGO,
                W4 / "fig_boxplot_multidim.png",
                "Rosenbrock hộp dâng theo số chiều (5 → 26 → 47). Ackley 3 hộp "
                "trùng nhau. Griewank chỉ dim 10 còn hộp. Dùng hình này để thấy "
                "ảnh hưởng của số chiều, không để so từng seed.",
                "Tuần 4 · Boxplot 3 chiều")

    bullets_slide(
        prs, n, total, "Kết luận tuần 4", "NHẬN XÉT", INDIGO,
        items=[
            ("Cài đặt đúng. ",
             "Sphere 10D đạt mean 3,49e-153 — tốt hơn ngẫu nhiên hàng 10^150 lần."),
            ("Điểm yếu duy nhất là Rosenbrock. ",
             "Mean bám theo số chiều (~5,6 / 26,2 / 46,6) và không về 0."),
            ("Rastrigin bất ổn ở chiều thấp. ",
             "1 seed kẹt cực tiểu cục bộ đủ kéo lệch mean; dim 50 thì hết."),
            ("Sẵn sàng sang tuần 5–6. ",
             "Khung đã tách thuật toán ↔ bài toán, không cần sửa khi thêm cơ chế."),
        ],
        footer_label="Tuần 4 · Kết luận")

    # ================= PHẦN B — TUẦN 5-6 =================
    divider(prs, n, total, "PHẦN B", "Tuần 5–6 — IDBO: cải tiến DBO",
            "Thêm hai cơ chế ngẫu nhiên khi quần thể mất đa dạng, rồi so sánh "
            "với DBO gốc trên cùng bộ hàm.", TEAL, "Tuần 5–6")

    setup_slide(
        prs, n, total,
        "IDBO thêm gì so với DBO gốc", "DÙNG GÌ", TEAL,
        params=[
            ("Giữ nguyên", "4 hành vi DBO, chữ ký optimize()"),
            ("Kích hoạt", "khi diversity < 1e-3"),
            ("Cơ chế 1", "Perturb Gauss ~20% agent"),
            ("Cơ chế 2", "Restart 25% agent tệ nhất"),
            ("Điều kiện restart", "stagnation ≥ 25 vòng"),
            ("Elite", "1 cá thể tốt nhất không bị đổi"),
            ("Cấu hình", "n_agents = 30, max_iter = 500, M = 30"),
            ("Tổng số lần chạy", "2 thuật toán × 6 hàm × 3 dim × 30 = 1.080"),
        ],
        who=[
            ("Lê Quang Duy", "khung IDBO, tích hợp vào DBO"),
            ("Hồ Trung Cương", "perturb/restart, đo diversity"),
            ("Đặng Nguyễn Minh Đăng", "thí nghiệm so sánh DBO vs IDBO"),
        ],
        note="So sánh fixed-iteration (cùng n_agents, max_iter, seed). "
             "Hòa nếu |mean_IDBO − mean_DBO| / max(|mean_DBO|, 1e-30) < 1%. "
             "Dữ liệu: experiments/week5_6/*.csv",
        footer_label="Tuần 5–6 · Thiết lập")

    image_slide(prs, n, total, "Sơ đồ IDBO sau mỗi vòng DBO", "THUẬT TOÁN", TEAL,
                W56 / "fig_idbo_flowchart.png",
                "Sau mỗi vòng: đo diversity = mean(std / (ub − lb)). Nếu ≥ 1e-3 "
                "thì bỏ qua (đa số các vòng). Nếu < 1e-3: stagnation ≥ 25 → "
                "restart 25% agent tệ nhất, ngược lại → perturb Gauss. "
                "Elite không bao giờ bị thay đổi.",
                "Tuần 5–6 · Sơ đồ IDBO")

    s = _blank(prs)
    _header(s, "Tần suất kích hoạt perturb / restart", "KẾT QUẢ", TEAL)
    rows = [
        ["Hàm", "dim 10 (pert / restart)", "dim 30", "dim 50", "Đọc"],
        ["Sphere", "0 / 0,53", "0 / 0,07", "0 / 0,07", "10D restart nhiều nhất"],
        ["Schwefel 2.22", "0 / 0,20", "0 / 0,03", "0 / 0,07", "Restart nhẹ"],
        ["Rosenbrock", "0 / 0", "0,10 / 0", "0,07 / 0", "Chỉ perturb"],
        ["Rastrigin", "0 / 0", "0 / 0", "0 / 0", "Diversity không sụp"],
        ["Ackley", "0 / 0", "0 / 0", "0 / 0", "Không kích hoạt"],
        ["Griewank", "0 / 0", "0 / 0,03", "0 / 0,10", "50D restart nhẹ"],
    ]
    table(s, rows, Inches(0.55), Inches(1.5), Inches(12.23), Inches(3.9),
          col_w=[Inches(2.3), Inches(2.9), Inches(2.3), Inches(2.3),
                 Inches(2.43)],
          header_color=TEAL, body_size=12.5, row_h=Inches(0.55),
          highlight={(1, 1): (RED, True)})
    _text(s, Inches(0.55), Inches(5.6), Inches(12.23), Inches(1.0),
          [[("Nhận xét.  ", {"bold": True, "color": AMBER}),
            ("Cơ chế gần như không kích hoạt: 15/18 ô bằng 0. Ngoại lệ đáng kể "
             "là Sphere dim 10 (restart 0,53 lần/run). Rastrigin và Ackley "
             "không bao giờ kích hoạt vì diversity không sụp.", {})]],
          size=13.5, color=INK, line_spacing=1.1)
    _footer(s, "Tuần 5–6 · Kết quả", n(), total)

    image_slide(prs, n, total, "Hội tụ DBO vs IDBO — dim = 10",
                "HÌNH 1/9", TEAL, W56 / "fig_convergence_dim10.png",
                "Đường cam (IDBO) phủ khít xanh (DBO) ở cả 6 hàm. IDBO không "
                "làm chậm hay làm xấu hội tụ. Ở dim 10 cơ chế chỉ chạy ở "
                "Sphere nhưng không tạo khác biệt về mean.",
                "Tuần 5–6 · Hội tụ dim 10")

    image_slide(prs, n, total, "Hội tụ DBO vs IDBO — dim = 30",
                "HÌNH 2/9", TEAL, W56 / "fig_convergence_dim30.png",
                "Vẫn trùng khít. Griewank về 0 ở cả hai. Rosenbrock dừng ≈26 ở "
                "cả hai. Không hàm nào IDBO vượt trội hay thua rõ — khớp với "
                "cột 'Thắng' ở bảng so sánh phía sau.",
                "Tuần 5–6 · Hội tụ dim 30")

    image_slide(prs, n, total, "Hội tụ DBO vs IDBO — dim = 50",
                "HÌNH 3/9", TEAL, W56 / "fig_convergence_dim50.png",
                "Rastrigin/Griewank về 0 (log đứt đoạn). Ackley ở sàn. Không "
                "thay đổi so với DBO. Số chiều cao không làm IDBO lệch khỏi "
                "DBO.",
                "Tuần 5–6 · Hội tụ dim 50")

    image_slide(prs, n, total, "Boxplot DBO vs IDBO — dim = 10",
                "HÌNH 4/9", TEAL, W56 / "fig_boxplot_dim10.png",
                "Từng cặp hộp xanh/cam gần như trùng nhau về trung vị, tứ phân "
                "vị và outlier. Bằng chứng trực quan rằng phân bố best_fitness "
                "không đổi khi thêm cơ chế ngẫu nhiên.",
                "Tuần 5–6 · Boxplot dim 10")

    image_slide(prs, n, total, "Boxplot DBO vs IDBO — dim = 30",
                "HÌNH 5/9", TEAL, W56 / "fig_boxplot_dim30.png",
                "Rosenbrock hai hộp trùng ≈26. Rastrigin cùng 1 outlier lớn ở "
                "cả hai (cùng seed). Không có cặp nào IDBO thấp hơn một cách "
                "hệ thống.",
                "Tuần 5–6 · Boxplot dim 30")

    image_slide(prs, n, total, "Boxplot DBO vs IDBO — dim = 50",
                "HÌNH 6/9", TEAL, W56 / "fig_boxplot_dim50.png",
                "Rastrigin/Griewank biến mất (giá trị 0). Sphere/Schwefel siêu "
                "nhỏ. Kết luận boxplot: 18 cặp (hàm, dim) đều hòa.",
                "Tuần 5–6 · Boxplot dim 50")

    image_slide(prs, n, total, "Diversity IDBO — dim = 10",
                "HÌNH 7/9", TEAL, W56 / "fig_diversity_dim10.png",
                "Rastrigin (đỏ) giữ diversity ~0,15 — cao hơn ngưỡng 1e-3 nên "
                "không kích hoạt. Sphere (xanh) giảm dần tới sát ngưỡng rồi "
                "nhích lên (răng cưa) từ vòng ~350 — chính là restart 0,53 "
                "lần/run trong bảng.",
                "Tuần 5–6 · Diversity dim 10")

    image_slide(prs, n, total, "Diversity IDBO — dim = 30",
                "HÌNH 8/9", TEAL, W56 / "fig_diversity_dim30.png",
                "Sphere vẫn sụp nhưng ít hơn (restart 0,07). Rastrigin vẫn cao, "
                "không kích hoạt. Ở chiều lớn, quần thể khó dồn về một điểm nên "
                "cơ chế ít có dịp chạy.",
                "Tuần 5–6 · Diversity dim 30")

    image_slide(prs, n, total, "Diversity IDBO — dim = 50",
                "HÌNH 9/9", TEAL, W56 / "fig_diversity_dim50.png",
                "Cùng xu hướng dim 30. Cơ chế gần như 'ngủ' trên đa số hàm → "
                "kết quả trùng DBO là hợp lý, không phải lỗi.",
                "Tuần 5–6 · Diversity dim 50")

    s = _blank(prs)
    _header(s, "Bảng so sánh MEAN — cột 'Thắng'", "KẾT QUẢ", TEAL)
    rows = [
        ["Hàm / dim", "10: DBO | IDBO", "30: DBO | IDBO", "50: DBO | IDBO",
         "Thắng"],
        ["Sphere", "3,49e-153 | 3,49e-153", "2,06e-158 | 2,06e-158",
         "5,70e-168 | 5,70e-168", "hòa 3/3"],
        ["Schwefel", "6,70e-82 | 6,70e-82", "3,60e-87 | 3,60e-87",
         "4,18e-82 | 4,18e-82", "hòa 3/3"],
        ["Rosenbrock", "5,611 | 5,611", "26,23 | 26,23", "46,65 | 46,65",
         "hòa 3/3"],
        ["Rastrigin", "2,741 | 2,741", "4,847 | 4,847", "0 | 0", "hòa 3/3"],
        ["Ackley", "4,44e-16 | 4,44e-16", "4,44e-16 | 4,44e-16",
         "4,44e-16 | 4,44e-16", "hòa 3/3"],
        ["Griewank", "0,0349 | 0,0349", "0 | 0", "0 | 0", "hòa 3/3"],
    ]
    table(s, rows, Inches(0.55), Inches(1.5), Inches(12.23), Inches(3.9),
          col_w=[Inches(1.8), Inches(3.05), Inches(3.05), Inches(3.05),
                 Inches(1.28)],
          header_color=TEAL, body_size=12, row_h=Inches(0.55))
    _text(s, Inches(0.55), Inches(5.6), Inches(12.23), Inches(1.0),
          [[("Nhận xét.  ", {"bold": True, "color": AMBER}),
            ("Toàn bộ 18 ô (hàm × dim) đều 'Hòa' theo ngưỡng 1%. Đây là câu "
             "trả lời trung thực: trên benchmark trơn nhẵn, cơ chế ngẫu nhiên "
             "không tạo khác biệt về chất lượng nghiệm.", {})]],
          size=13.5, color=INK, line_spacing=1.1)
    _footer(s, "Tuần 5–6 · Bảng so sánh", n(), total)

    bullets_slide(
        prs, n, total, "Chi phí thời gian & vì sao hai bên hòa",
        "PHÂN TÍCH", TEAL,
        items=[
            ("IDBO chậm hơn 15–20%. ",
             "Ví dụ Sphere dim 10: 0,27s → 0,32s. Nguyên nhân: gọi thêm "
             "objective khi cơ chế kích hoạt (n_evaluations 15.030 → ~15.034)."),
            ("Cơ chế hiếm khi chạy. ",
             "Trên hàm trơn, quần thể DBO đã hội tụ về đúng tối ưu toàn cục, "
             "nên diversity không sụp dưới 1e-3 → perturb/restart bằng 0."),
            ("Vì vậy hai bên hòa. ",
             "Không phải IDBO kém, mà là bài toán benchmark chưa cần đến nó."),
            ("Ý nghĩa cho đề tài. ",
             "Giá trị của IDBO sẽ thể hiện ở bài toán thực đơn (nhiều cực trị, "
             "ràng buộc) — bắt đầu từ tuần 7."),
        ],
        footer_label="Tuần 5–6 · Phân tích")

    bullets_slide(
        prs, n, total, "Kết luận tuần 5–6", "NHẬN XÉT", TEAL,
        items=[
            ("Không làm xấu DBO. ",
             "18/18 ô mean hòa; boxplot và hội tụ đều trùng khít."),
            ("Chi phí chấp nhận được. ",
             "Chậm hơn 15–20%, đổi lại có cơ chế thoát cực tiểu cục bộ khi cần."),
            ("Kích hoạt chủ yếu ở Sphere dim 10. ",
             "Rastrigin/Ackley không kích hoạt; Rosenbrock chỉ perturb."),
            ("Trung thực về kết quả. ",
             "Không tuyên bố 'IDBO tốt hơn'; kết luận đúng là hai thuật toán "
             "tương đương trên benchmark liên tục."),
        ],
        footer_label="Tuần 5–6 · Kết luận")

    closing(prs, n, total)

    used = n.count()
    if used != total:
        print(f"[CẢNH BÁO] số slide = {used}, total cấu hình = {total}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"[OK] {OUT}  ({used} slide, {len(pngs)} PNG)")


if __name__ == "__main__":
    build()
