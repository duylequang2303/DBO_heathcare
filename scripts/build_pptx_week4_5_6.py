"""Xay slide tuan 4-5-6: moi PNG mot slide + chu thich, bang chi con mean.

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
from pptx.oxml.ns import nsmap
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Slide_Tuan_4_5_6_DBO_IDBO.pptx"
W4 = ROOT / "experiments" / "week4"
W56 = ROOT / "experiments" / "week5_6"

NAVY = RGBColor(0x1B, 0x36, 0x5D)
ORANGE = RGBColor(0xC4, 0x5C, 0x26)
TEAL = RGBColor(0x2A, 0x6F, 0x6F)
GOLD = RGBColor(0xC9, 0xA2, 0x27)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x1F, 0x29, 0x37)
MUTED = RGBColor(0x5B, 0x67, 0x75)
LIGHT = RGBColor(0xF4, 0xF7, 0xFA)
CREAM = RGBColor(0xFF, 0xF8, 0xE7)
ROW_ALT = RGBColor(0xEE, 0xF3, 0xF8)
GREEN = RGBColor(0x1F, 0x7A, 0x4D)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def _set_run_font(run, size, bold=False, color=INK, name="Calibri"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", name)


def _fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def _textbox(slide, l, t, w, h, text, size=18, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    try:
        tf._txBody.bodyPr.set("anchor", {MSO_ANCHOR.TOP: "t", MSO_ANCHOR.MIDDLE: "ctr", MSO_ANCHOR.BOTTOM: "b"}.get(anchor, "t"))
    except Exception:
        pass
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    _set_run_font(run, size, bold, color)
    return box


def _add_bar(slide, color=NAVY, height=Inches(0.92)):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, height)
    _fill(bar, color)
    acc = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, height, SLIDE_W, Inches(0.06))
    _fill(acc, ORANGE)
    return height + Inches(0.06)


def _footer(slide, page, total):
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.22), SLIDE_W, Inches(0.28))
    _fill(line, NAVY)
    _textbox(slide, Inches(0.4), Inches(7.22), Inches(10), Inches(0.28),
             "CNTT-KLCN142  |  DBO / IDBO  |  Tuan 4-5-6  |  dim = 10, 30, 50  |  M = 30",
             size=11, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    _textbox(slide, Inches(11.4), Inches(7.22), Inches(1.6), Inches(0.28),
             f"{page} / {total}", size=11, bold=True, color=WHITE, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)


def _title(slide, text, subtitle=None):
    top = _add_bar(slide)
    _textbox(slide, Inches(0.4), Inches(0.18), Inches(12.5), Inches(0.55),
             text, size=26, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    if subtitle:
        _textbox(slide, Inches(0.4), Inches(0.58), Inches(12.5), Inches(0.28),
                 subtitle, size=13, color=RGBColor(0xD7, 0xE3, 0xF4))
    return top


def _fit_image(path: Path, box_w, box_h):
    with Image.open(path) as im:
        iw, ih = im.size
    box_w_in = box_w / 914400
    box_h_in = box_h / 914400
    aspect = iw / ih
    box_aspect = box_w_in / box_h_in
    if aspect > box_aspect:
        w = box_w
        h = int(box_w / aspect)
    else:
        h = box_h
        w = int(box_h * aspect)
    return w, h


def _caption(slide, text, top=Inches(6.22), height=Inches(0.95)):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.35), top, Inches(12.65), height)
    _fill(box, CREAM)
    box.line.color.rgb = GOLD
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18)
    tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.08)
    tf.margin_bottom = Inches(0.06)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    _set_run_font(run, 13, False, INK)


def _image_slide(prs, title, png: Path, caption: str, page, total, subtitle=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _title(slide, title, subtitle)
    box_l, box_t = Inches(0.4), Inches(1.12)
    box_w, box_h = Inches(12.53), Inches(5.00)
    w, h = _fit_image(png, box_w, box_h)
    left = int(box_l + (box_w - w) / 2)
    top = int(box_t + (box_h - h) / 2)
    slide.shapes.add_picture(str(png), left, top, width=w, height=h)
    _caption(slide, caption)
    _footer(slide, page, total)
    return slide


def _bullets(slide, items, l, t, w, h, size=16):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = 0
        p.space_after = Pt(8)
        run = p.add_run()
        run.text = item
        _set_run_font(run, size, False, INK)
    return box


def _card(slide, l, t, w, h, title, body, color=NAVY):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    _fill(shp, WHITE)
    shp.line.color.rgb = color
    head = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, Inches(0.42))
    _fill(head, color)
    _textbox(slide, l + Inches(0.12), t, w - Inches(0.2), Inches(0.42),
             title, size=14, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    _textbox(slide, l + Inches(0.14), t + Inches(0.48), w - Inches(0.28), h - Inches(0.55),
             body, size=13, color=INK)


def _table(slide, rows, l, t, w, h, col_w=None, header_color=NAVY):
    n_row, n_col = len(rows), len(rows[0])
    tbl_shape = slide.shapes.add_table(n_row, n_col, l, t, w, h)
    tbl = tbl_shape.table
    if col_w:
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = cw
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c > 0 else PP_ALIGN.LEFT
            run = p.add_run()
            run.text = str(val)
            is_header = r == 0
            _set_run_font(run, 12 if is_header else 12, bold=is_header or c == 0,
                          color=WHITE if is_header else INK)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            fill = header_color if is_header else (ROW_ALT if r % 2 == 0 else WHITE)
            cell.fill.solid()
            cell.fill.fore_color.rgb = fill
    return tbl_shape


def build():
    missing = []
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
    for p in pngs:
        if not p.exists():
            missing.append(str(p))
    if missing:
        print("[ERROR] Thieu PNG:\n  " + "\n  ".join(missing), file=sys.stderr)
        sys.exit(1)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    total = 34
    page = 0

    def n():
        nonlocal page
        page += 1
        return page

    # 1 cover
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    _fill(bg, NAVY)
    acc = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.22), SLIDE_H)
    _fill(acc, ORANGE)
    _textbox(s, Inches(0.7), Inches(1.5), Inches(12), Inches(0.4),
             "CNTT-KLCN142  ·  Khoa luan CNTT  ·  2025-2026", size=16, color=GOLD)
    _textbox(s, Inches(0.7), Inches(2.0), Inches(12), Inches(1.6),
             "DBO va IDBO tren ham benchmark\nSlide giai thich hinh + bang (Tuan 4, 5, 6)",
             size=32, bold=True, color=WHITE)
    _textbox(s, Inches(0.7), Inches(4.0), Inches(12), Inches(1.2),
             "De tai: He thong de xuat thuc don dinh duong ca nhan hoa bang IDBO\n"
             "GVHD: ThS. Dinh Nguyen Trong Nghia\n"
             "Nhom: Le Quang Duy · Dang Nguyen Minh Dang · Ho Trung Cuong",
             size=16, color=RGBColor(0xD7, 0xE3, 0xF4))
    _textbox(s, Inches(0.7), Inches(6.4), Inches(12), Inches(0.5),
             "Cach dung slide: moi hinh co khung vang phia duoi — doc khung do truoc khi nhin so.",
             size=14, color=WHITE)
    n()

    # 2 muc luc
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Ban do slide — doc theo thu tu nay")
    _card(s, Inches(0.4), Inches(1.3), Inches(4.0), Inches(5.4),
          "PHAN A · Tuan 4",
          "DBO goc la gi?\n\nBang MEAN 6 ham x 3 dim\n(khong nhe 18 dong best/std/worst)\n\n8 hinh hoi tu + boxplot\nmoi hinh kem 3-4 cau chu thich\n\nKet luan: cai dat DBO dung",
          NAVY)
    _card(s, Inches(4.65), Inches(1.3), Inches(4.0), Inches(5.4),
          "PHAN B · Tuan 5-6",
          "IDBO them 2 co che khi quan the sup\n\nSo do + bang perturb/restart\n\n10 hinh: hoi tu / box / diversity\nDBO (xanh) vs IDBO (cam)\n\nKet luan: hai thuat toan hoa",
          ORANGE)
    _card(s, Inches(8.9), Inches(1.3), Inches(4.0), Inches(5.4),
          "Quy uoc doc hinh",
          "Truc Y log: duong xuong = tot hon (minimize).\n\nDuong trung binh cua 30 lan chay, khong phai 1 seed.\n\nBoxplot: hop = 50% giua; cham tron = outlier.\n\nBang chi hien MEAN. So day du nam o CSV.",
          TEAL)
    _footer(s, n(), total)

    # 3 protocol
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Protocol — nho 6 so nay la du", "Khong dung dim=2. Khong so sanh equal-budget.")
    rows = [
        ["Tham so", "Gia tri", "Y nghia ngan"],
        ["Thuat toan", "Tuan 4: DBO   |   Tuan 5-6: DBO vs IDBO", "Cung n_agents, max_iter, seed"],
        ["6 ham", "Sphere, Schwefel 2.22, Rosenbrock, Rastrigin, Ackley, Griewank", "3 don dieu + 3 da cuc tri"],
        ["dim", "10, 30, 50", "So bien can toi uu"],
        ["n_agents / max_iter / M", "30 / 500 / 30", "Quan the, vong lap, so lan lap lai"],
        ["Tong run", "Tuan 4: 540     Tuan 5-6: 1080", "6x3x30  va  2x6x3x30"],
        ["Chieu toi uu", "Minimize  (gan 0 = tot)", "Doi dau khi sang fitness thuc don tuan 7"],
    ]
    _table(s, rows, Inches(0.4), Inches(1.25), Inches(12.5), Inches(4.6),
           col_w=[Inches(2.6), Inches(5.5), Inches(4.4)])
    _caption(s, "Hoa DBO vs IDBO neu |mean_IDBO - mean_DBO| / max(|mean_DBO|, 1e-30) < 1%. So sanh fixed-iteration, IDBO duoc phep goi them objective khi perturb/restart.",
             top=Inches(6.05), height=Inches(1.05))
    _footer(s, n(), total)

    # 4 six functions
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "6 ham benchmark — nho 1 cau moi ham")
    cards = [
        (NAVY, "Sphere  (don dieu)", "Bat toi thieu o 0. DBO dung se hoi tu rat sau (1e-150...). Neu khong xuong: code sai."),
        (NAVY, "Schwefel 2.22", "Don dieu, cong thuc |x1|+|x2|+...  Cung phai ve gan 0."),
        (ORANGE, "Rosenbrock", "Thung lung hep. DBO dung o ~5.6 (10D), ~26 (30D), ~47 (50D) — KHONG ve 0."),
        (TEAL, "Rastrigin  (da cuc)", "Nhieu ho cuc bo. 10D mean ~2.74; 50D ve 0 ca 30/30 run."),
        (TEAL, "Ackley", "Da cuc. Moi dim = 4.441e-16 (san may, khong the nho hon)."),
        (TEAL, "Griewank", "10D mean ~0.035 (con sot cuc bo); 30D va 50D = 0."),
    ]
    for i, (col, title, body) in enumerate(cards):
        r, c = divmod(i, 3)
        _card(s, Inches(0.4 + c * 4.25), Inches(1.25 + r * 2.85), Inches(4.05), Inches(2.65), title, body, col)
    _footer(s, n(), total)

    # 5 DBO 4 behaviors
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Tuan 4 — DBO goc: 4 hanh vi (Xue & Shen 2023)", "Chua cai tien. Chua thuc don.")
    _card(s, Inches(0.4), Inches(1.3), Inches(6.2), Inches(2.5),
          "Ball-rolling + dancing",
          "Cuon phan ve phia tot nhat. Gap vat can thi nhay (tan theta) de doi huong. Nhom ~20% quan the.",
          NAVY)
    _card(s, Inches(6.8), Inches(1.3), Inches(6.1), Inches(2.5),
          "Reproduction",
          "Vung de trung co dan quanh best. Sinh ca the con gan nghiem tot. Nhom ~20%.",
          TEAL)
    _card(s, Inches(0.4), Inches(4.0), Inches(6.2), Inches(2.5),
          "Foraging",
          "Bo nho di kiem an; vung tim kiem co dan theo vong lap. Nhom ~7/30.",
          ORANGE)
    _card(s, Inches(6.8), Inches(4.0), Inches(6.1), Inches(2.5),
          "Thieving",
          "Bo trom bam quanh best toan cuc (nhieu Gaussian). Nhom con lai ~11/30.",
          GOLD)
    _footer(s, n(), total)

    # 6 table mean DBO
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Bang MEAN DBO — chi 1 so moi o", "Nho hon = tot hon. Day du best/std/worst nam o experiments/week4/dbo_benchmark_summary.csv")
    rows = [
        ["Ham", "dim 10", "dim 30", "dim 50", "Doc so nay nhu the nao"],
        ["Sphere", "3.49e-153", "2.06e-158", "5.70e-168", "Hoi tu rat sau — cai dat dung"],
        ["Schwefel 2.22", "6.70e-82", "3.60e-87", "4.18e-82", "Cung ve gan 0"],
        ["Rosenbrock", "5.61", "26.23", "46.65", "Kho; ~ dim  (khong ve 0)"],
        ["Rastrigin", "2.74", "4.85", "0", "50D: 30/30 run ve 0"],
        ["Ackley", "4.44e-16", "4.44e-16", "4.44e-16", "San may, moi dim giong nhau"],
        ["Griewank", "0.0349", "0", "0", "10D con sot; 30/50D het"],
    ]
    _table(s, rows, Inches(0.35), Inches(1.25), Inches(12.6), Inches(5.0),
           col_w=[Inches(2.1), Inches(1.8), Inches(1.8), Inches(1.8), Inches(5.1)])
    _footer(s, n(), total)

    # 7 how to read convergence
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Cach doc hinh hoi tu (truoc khi xem 4 slide sau)")
    items = [
        "Moi khung = 1 ham. 6 khung: Sphere, Schwefel, Rosenbrock (hang tren) · Rastrigin, Ackley, Griewank (hang duoi).",
        "Truc X = vong lap 0 → 500. Truc Y = best fitness TRUNG BINH 30 seed, thang LOG (moi vach la gap 10, 100, 1000 lan).",
        "Duong XUONG = thuat toan dang tot len. Duong nam ngang = da dung (khong cai thien them).",
        "Gia tri 0 khong ve duoc tren log → doan cuoi Griewank/Rastrigin 50D co the 'mat tich' — do ve 0, khong phai loi ve.",
        "Slide sau: dim 10, roi 30, roi 50, roi 3 duong chong len nhau. Doc caption vang duoi moi hinh.",
    ]
    _bullets(s, items, Inches(0.6), Inches(1.5), Inches(12), Inches(5.2), size=18)
    _footer(s, n(), total)

    _image_slide(
        prs, "Tuan 4 · Hoi tu DBO  dim=10",
        W4 / "fig_convergence_dim10.png",
        "Dim 10 de nhat. Sphere/Schwefel xuong 1e-80 den 1e-150. Ackley dung o 4.4e-16 tu vong ~100. Rosenbrock dung ~5-6 (thung lung). Rastrigin/Griewank giam nhung chua ve 0 — con cuc bo.",
        n(), total, "6 subplot, 1 duong DBO, trung binh 30 run, truc Y log",
    )
    _image_slide(
        prs, "Tuan 4 · Hoi tu DBO  dim=30",
        W4 / "fig_convergence_dim30.png",
        "Dim 30 kho hon. Sphere van xuong rat sau. Rosenbrock dung ~26 (gap ~dim). Griewank dim 30 ve 0 (tot hon dim 10 — dac trung ham nay). Rastrigin mean ~4.85, std lon vi 1-2 seed ket o cuc bo.",
        n(), total, "Cung 6 ham, cung M=30, chi doi so chieu",
    )
    _image_slide(
        prs, "Tuan 4 · Hoi tu DBO  dim=50",
        W4 / "fig_convergence_dim50.png",
        "Dim 50. Rastrigin va Griewank ve 0 SOM (duong dut doan vi log(0)). Ackley van 4.44e-16. Rosenbrock ~47. Ket luan: DBO khong vo o chieu cao; ham da cuc con de hon Rosenbrock.",
        n(), total, "Day la chieu kho nhat trong protocol",
    )
    _image_slide(
        prs, "Tuan 4 · Chong 3 chieu tren 1 hinh",
        W4 / "fig_convergence_multidim.png",
        "Xanh=10, cam=30, tim=50. Sphere: 50D (tim) xuong SAU hon 10D — binh thuong vi span lon, std chua chuan hoa. Rosenbrock: 50D nam cao nhat (~47), 10D thap nhat (~5.6). Rastrigin/Griewank: chi duong tim (50D) rot thang xuong 0.",
        n(), total, "Doc tung ham: 3 duong = 3 dim, khong phai 3 thuat toan",
    )

    # how to read boxplot
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Cach doc boxplot (4 slide hinh ke tiep)")
    items = [
        "Moi hop = 30 so best_fitness (1 so / seed). Khong phai duong hoi tu.",
        "Gach den giua hop = trung vi. Hop = 50% run nam trong khoang nay. Rau = phan con lai (khong ke outlier).",
        "Cham tron = outlier: seed tu (Rastrigin 10D co 3 cham ~10-17; Sphere co vai seed te hon mean 1e-151).",
        "Hop MONG / gach nam ngang (Ackley) = 30/30 run ra CUNG mot so → thuat toan on dinh.",
        "Truc Y log: hop nam THAP hon = tot hon. So sanh hop, dung so sanh 1 cham outlier.",
    ]
    _bullets(s, items, Inches(0.6), Inches(1.5), Inches(12), Inches(5.2), size=18)
    _footer(s, n(), total)

    _image_slide(
        prs, "Tuan 4 · Boxplot DBO  dim=10",
        W4 / "fig_boxplot_dim10.png",
        "Ackley: mot gach — 30 run = 4.44e-16. Rosenbrock: hop chat 5.3-5.7, 1 outlier ~9. Rastrigin: hop sat 0 nhung 3 outlier keo mean len 2.74. Sphere/Schwefel: hop o 1e-80..1e-180, vai outlier te hon — van cuc tot.",
        n(), total,
    )
    _image_slide(
        prs, "Tuan 4 · Boxplot DBO  dim=30",
        W4 / "fig_boxplot_dim30.png",
        "Rosenbrock hop rat chat quanh 26 (on dinh nhung lech xa 0). Rastrigin: hop thap nhung 1 outlier ~115 keo mean len 4.85 va std 21 — day la ham 'te nhat' ve do on dinh. Griewank: 0 het.",
        n(), total,
    )
    _image_slide(
        prs, "Tuan 4 · Boxplot DBO  dim=50",
        W4 / "fig_boxplot_dim50.png",
        "Rastrigin 50D = 0 het (hop bien mat tren log). Griewank = 0. Rosenbrock hop quanh 46-47. Sphere std=0 trong CSV vi underflow float — 30 run deu sieu nho, khong phai 'khong phan tan'.",
        n(), total,
    )
    _image_slide(
        prs, "Tuan 4 · Boxplot chong 3 dim",
        W4 / "fig_boxplot_multidim.png",
        "Moi ham 3 hop (10/30/50). Rosenbrock: hop di LEN theo dim (5 → 26 → 47) — day la ham kho theo chieu. Ackley: 3 gach trung nhau. Griewank: chi dim 10 con hop, 30/50 ve 0.",
        n(), total, "Dung de nhin xu huong theo so chieu, khong de so tung seed",
    )

    # takeaway week 4
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Tuan 4 — 4 cau ket luan (de bao ve)")
    items = [
        "DBO cai dat dung: Sphere 10D mean 3.49e-153, tot hon random hang 10^150 lan.",
        "Don dieu: Sphere/Schwefel ok; Rosenbrock la ham 'thua' — mean bam ~dim, khong ve 0.",
        "Da cuc: Ackley dat san may moi dim. Griewank 30/50D ve 0. Rastrigin 10/30D con outlier.",
        "Tuan 5-6 khong sua 4 hanh vi. IDBO chi them perturb/restart KHI diversity < 1e-3.",
    ]
    _bullets(s, items, Inches(0.6), Inches(1.5), Inches(12), Inches(5.0), size=20)
    _footer(s, n(), total)

    # week 5-6 intro
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Tuan 5-6 — IDBO: DBO + 2 co che khi quan the sup", "Khong doi 4 hanh vi. Khong doi optimize(objective, dim, lb, ub, seed).")
    _card(s, Inches(0.4), Inches(1.3), Inches(6.2), Inches(5.4),
          "1. Random perturbation",
          "Khi nao: diversity < 1e-3 VA chua du 25 vong dung (chua restart).\n\nLam gi: nhiu Gauss len ~20% agent, KHONG dung elite tot nhat.\n\nBien do: 0.1*(ub-lb) giam dan theo vong lap.\n\nMuc dich: lay quan the ra khoi diem dung, khong pha nghiem tot.",
          ORANGE)
    _card(s, Inches(6.8), Inches(1.3), Inches(6.1), Inches(5.4),
          "2. Random restart",
          "Khi nao: diversity < 1e-3 VA best dung yen 25 vong.\n\nLam gi: 25% agent TE NHAT khoi tao lai deu trong [lb, ub]. Elite giu.\n\nMot vong: restart HOAC perturb, khong ca hai.\n\nLuu y: goi them objective → n_evaluations IDBO >= DBO (15030).",
          TEAL)
    _footer(s, n(), total)

    _image_slide(
        prs, "Tuan 5-6 · So do IDBO sau moi vong DBO",
        W56 / "fig_idbo_flowchart.png",
        "Doc tu tren xuong: 4 hanh vi DBO → do diversity. Neu diversity >= 1e-3: bo qua, sang vong sau (da so vong la nhanh nay). Neu < 1e-3: hoi stagnation >= 25? Co → restart 25% te nhat. Khong → perturb Gauss. Roi danh gia lai agent vua doi.",
        n(), total, "Elite (n_elite=1) khong bao gio bi sua",
    )

    # perturb table
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Bang perturb / restart — IDBO (trung binh 30 run)", "0 = co che khong kip kich hoat vi diversity chua xuong 1e-3")
    rows = [
        ["Ham", "dim10 pert / restart", "dim30", "dim50", "Doc"],
        ["Sphere", "0  /  0.53", "0 / 0.07", "0 / 0.07", "10D restart nhieu nhat"],
        ["Schwefel 2.22", "0  /  0.20", "0 / 0.03", "0 / 0.07", "Restart nhe"],
        ["Rosenbrock", "0  /  0", "0.10 / 0", "0.07 / 0", "Chi perturb, khong restart"],
        ["Rastrigin", "0  /  0", "0 / 0", "0 / 0", "Diversity khong sup"],
        ["Ackley", "0  /  0", "0 / 0", "0 / 0", "Dung som, van rai"],
        ["Griewank", "0  /  0", "0 / 0.03", "0 / 0.10", "50D restart nhe"],
    ]
    _table(s, rows, Inches(0.3), Inches(1.22), Inches(12.7), Inches(5.0),
           col_w=[Inches(2.2), Inches(2.6), Inches(2.2), Inches(2.2), Inches(3.5)])
    _footer(s, n(), total)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Cach doc hinh DBO vs IDBO")
    items = [
        "Duong dut XANH = DBO. Duong CAM = IDBO. Neu 2 duong de len nhau = HOA (chenh < 1%).",
        "Hinh hoi tu: neu cam nam DUOI xanh = IDBO tot hon (minimize). Hinh tuan nay hai duong chong khit.",
        "Boxplot: 2 hop canh nhau. Hop giong nhau = phan bo best_fitness khong doi.",
        "Diversity: chi ve IDBO. Duong dut 1e-3 = nguong kich hoat. Sphere (xanh la) xuong gan nguong roi nhich len = restart/perturb. Rastrigin (do) nam cao ~0.1 = khong kich hoat.",
        "Khong viet 'IDBO tot hon' neu bang mean hoa. IDBO khong pha chat luong DBO — do la ket luan dung.",
    ]
    _bullets(s, items, Inches(0.6), Inches(1.45), Inches(12), Inches(5.2), size=17)
    _footer(s, n(), total)

    _image_slide(
        prs, "Tuan 5-6 · Hoi tu DBO vs IDBO  dim=10",
        W56 / "fig_convergence_dim10.png",
        "Cam de len xanh o MOI ham — hai thuat toan di cung mot duong. Sphere van xuong 1e-150. Ackley dung 4.4e-16 tu vong 100. IDBO khong lam cham hoi tu, cung khong bung ra tot hon tren benchmark lien tuc nay.",
        n(), total, "F1  ·  6 subplot  ·  Y log  ·  M=30",
    )
    _image_slide(
        prs, "Tuan 5-6 · Hoi tu DBO vs IDBO  dim=30",
        W56 / "fig_convergence_dim30.png",
        "Van chong khit. Rosenbrock dung ~26 ca hai. Griewank ve 0. Rastrigin con 'duoi' ngang ~5 vi outlier. Khong co ham nao IDBO rot xuong duoi DBO ro.",
        n(), total,
    )
    _image_slide(
        prs, "Tuan 5-6 · Hoi tu DBO vs IDBO  dim=50",
        W56 / "fig_convergence_dim50.png",
        "Rastrigin/Griewank ve 0 (log dut). Ackley san may. Rosenbrock ~47. Van hoa. Chieu cao khong lam IDBO lech khoi DBO.",
        n(), total,
    )
    _image_slide(
        prs, "Tuan 5-6 · Boxplot DBO vs IDBO  dim=10",
        W56 / "fig_boxplot_dim10.png",
        "Tung cap hop xanh/cam GAN NHU GIONG NHAU (median, rau, outlier). Ackley: 2 gach trung. Rastrigin: cung 3 outlier. Day la bang chung truc quan rang IDBO khong doi phan bo ket qua.",
        n(), total, "F2  ·  hop trai = DBO, hop phai = IDBO",
    )
    _image_slide(
        prs, "Tuan 5-6 · Boxplot DBO vs IDBO  dim=30",
        W56 / "fig_boxplot_dim30.png",
        "Rosenbrock 2 hop trung ~26. Rastrigin van 1 outlier lon (ca DBO lan IDBO, vi cung seed). Griewank 0. Khong co hop cam thap hon xanh mot cach he thong.",
        n(), total,
    )
    _image_slide(
        prs, "Tuan 5-6 · Boxplot DBO vs IDBO  dim=50",
        W56 / "fig_boxplot_dim50.png",
        "Rastrigin/Griewank 0 het. Sphere/Schwefel van sieu nho. Rosenbrock hop cam/xanh trung 46-47. Ket luan boxplot: 18 cap (ham, dim) deu hoa.",
        n(), total,
    )
    _image_slide(
        prs, "Tuan 5-6 · Diversity IDBO  dim=10",
        W56 / "fig_diversity_dim10.png",
        "DO = Rastrigin: diversity dung ~0.15, CAO hon nguong 1e-3 → perturb/restart = 0 (khop bang). XANH LA = Sphere: giam dan, gan 1e-3 roi NHICH LEN (rang cua) tu vong ~350 = restart 0.53 lan/run. Nguong dut khong bi vuot xuong duoi lau.",
        n(), total, "F3  ·  chi IDBO  ·  Sphere (don dieu) vs Rastrigin (da cuc)",
    )
    _image_slide(
        prs, "Tuan 5-6 · Diversity IDBO  dim=30",
        W56 / "fig_diversity_dim30.png",
        "Sphere van giam nhung restart chi 0.07 (it hon dim 10). Rastrigin van cao, khong kich hoat. Dim lon → quan the kho sap het vao 1 diem hon dim 10, nen co che ngau nhien it duoc goi.",
        n(), total,
    )
    _image_slide(
        prs, "Tuan 5-6 · Diversity IDBO  dim=50",
        W56 / "fig_diversity_dim50.png",
        "Giong dim 30: Rastrigin khong sup. Sphere/Griewank restart rat thua (0.07 / 0.10). Co che IDBO 'ngu' tren da so ham — do do ket qua trung DBO la hop ly, khong phai bug.",
        n(), total,
    )

    # comparison table
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Bang so sanh MEAN — 6 ham, 3 dim, cot Thang", "Nguong hoa 1%. Fitness minimize. Day du 36 dong o CSV.")
    rows = [
        ["Ham / dim", "10 DBO | IDBO", "30 DBO | IDBO", "50 DBO | IDBO", "Thang"],
        ["Sphere", "3.49e-153 | 3.49e-153", "2.06e-158 | 2.06e-158", "5.70e-168 | 5.70e-168", "hoa 3/3"],
        ["Schwefel", "6.70e-82 | 6.70e-82", "3.60e-87 | 3.60e-87", "4.18e-82 | 4.18e-82", "hoa 3/3"],
        ["Rosenbrock", "5.611 | 5.611", "26.23 | 26.23", "46.65 | 46.65", "hoa 3/3"],
        ["Rastrigin", "2.741 | 2.741", "4.847 | 4.847", "0 | 0", "hoa 3/3"],
        ["Ackley", "4.44e-16 | 4.44e-16", "4.44e-16 | 4.44e-16", "4.44e-16 | 4.44e-16", "hoa 3/3"],
        ["Griewank", "0.0349 | 0.0349", "0 | 0", "0 | 0", "hoa 3/3"],
    ]
    _table(s, rows, Inches(0.25), Inches(1.22), Inches(12.8), Inches(5.05),
           col_w=[Inches(1.9), Inches(3.15), Inches(3.15), Inches(3.15), Inches(1.45)])
    _footer(s, n(), total)

    # 5 answers
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "5 cau bao ve — tra loi ngan, co so")
    items = [
        "Unimodal: IDBO KHONG lam xau DBO. Sphere/Schwefel/Rosenbrock hoa 9/9 o mean (nguong 1%).",
        "Multimodal: IDBO thang 0/9 o mean. Rastrigin/Ackley/Griewank hoa tuyet doi, ke ca outlier.",
        "Dim 50 van hoi tu. Ham 'te' ve on dinh: Rastrigin 30D (std 21 vi 1 seed ~115). Khong phai IDBO gay ra.",
        "F3: Rastrigin KHONG tut xuong 1e-3. Sphere dim 10 tut gan nguong roi nhich — dung la restart (0.53).",
        "Thoi gian dim 10: IDBO cham hon DBO ~15-20% (vi du Sphere 0.27s → 0.32s). Doi bang so eval them (15030 → 15034).",
    ]
    _bullets(s, items, Inches(0.55), Inches(1.35), Inches(12.2), Inches(5.4), size=17)
    _footer(s, n(), total)

    # conclusion + week 7
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _title(s, "Ket luan 3 tuan + viec tuan 7")
    _card(s, Inches(0.4), Inches(1.25), Inches(4.05), Inches(5.4),
          "Da chot",
          "DBO goc dung tren 6 ham, dim 10/30/50, M=30.\n\nIDBO khong pha baseline.\n\nPerturb/restart chi thuc su kich hoat khi quan the sap (chu yeu Sphere 10D).\n\nSo lieu CSV = nguon su that, khong bia.",
          NAVY)
    _card(s, Inches(4.65), Inches(1.25), Inches(4.05), Inches(5.4),
          "Khong noi qua",
          "Khong noi 'IDBO tot hon DBO'.\n\nKhong so sanh equal-evaluation-budget.\n\nKhong dung dim=2.\n\nRosenbrock chua giai; do la han che DBO goc, khong phai loi code.",
          ORANGE)
    _card(s, Inches(8.9), Inches(1.25), Inches(4.05), Inches(5.4),
          "Tuan 7",
          "Gan fitness thuc don vao optimize().\n\nIDBO chi toi uu khau phan x (dim=8, 25-350 g). food_ids chon truoc.\n\nobjective(x) = -evaluate(menu) vi DBO minimize.\n\nM=10, max_iter=200, profile P1.",
          TEAL)
    _footer(s, n(), total)

    # end
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    _fill(bg, NAVY)
    acc = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.22), SLIDE_H)
    _fill(acc, ORANGE)
    _textbox(s, Inches(0.7), Inches(2.4), Inches(12), Inches(1.2),
             "Het phan hinh tuan 4-5-6", size=32, bold=True, color=WHITE)
    _textbox(s, Inches(0.7), Inches(3.8), Inches(12), Inches(1.5),
             "File: docs/Slide_Tuan_4_5_6_DBO_IDBO.pptx\n"
             "18 PNG da nhung trong slide. Bang chi MEAN. CSV goc khong commit.\n"
             "Phan cong tuan 7: docs/TASK_WEEK7.md",
             size=16, color=RGBColor(0xD7, 0xE3, 0xF4))
    n()

    if page != total:
        print(f"[WARN] page={page} total={total} — cap nhat footer total neu lech")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"[OK] {OUT}  ({page} slides, {len(pngs)} PNG)")


if __name__ == "__main__":
    build()
