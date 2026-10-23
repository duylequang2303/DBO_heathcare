"""Dựng slide báo cáo Tuần 11 (Chuẩn hóa thực nghiệm DBO/IDBO, Budget-Matched & Tích hợp Web UI).

Đề tài: CNTT-KLCN142 — Trường Đại học Công Thương TP.HCM (HUIT)
Thực hiện: Nhóm nghiên cứu DBO Healthcare (Lê Quang Duy, Hồ Trung Cương, Đặng Nguyễn Minh Đăng).

Cấu trúc trình chiếu 8 slide khoa học, đầy đủ hình ảnh minh chứng thực tế:
- Slide 1: Bìa báo cáo tổng quan Tuần 11
- Slide 2: Nghiệm thu Web API & Giao diện Trực quan hóa Dinh dưỡng (Kèm hình Radar W11-F5)
- Slide 3: Đối đầu DBO vs IDBO trên Tập Độc Lập Seed 8003–8010 (Kèm hình W11-F1)
- Slide 4: Đánh đổi Chi phí Tính toán: Evaluations & Runtime (Kèm hình W11-F2)
- Slide 5: Phân tích Telemetry: Kích hoạt Tầng Ngoài vs Tầng Trong (Kèm hình W11-F3)
- Slide 6: Kiểm soát Ngân sách Chung: Budget-Matched Benchmark (Kèm hình W11-F4)
- Slide 7: Hoàn thiện Kiến trúc Ngưỡng Kép (Dual Diversity Threshold)
- Slide 8: Đảm bảo Chất lượng Mã nguồn (253/253 tests PASS & Tuân thủ AGENTS.md)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "slides"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PPTX = OUT_DIR / "Slide_Bao_Cao_Tuan_11_DBO_IDBO.pptx"

FIG_DIR = ROOT / "experiments" / "ablation_dbo_idbo"

# --------------------------------------------------------------------------- #
# Bảng màu chuẩn học thuật
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

FONT = "Calibri"
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


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


def _header(slide, title_text, category_text):
    """Header chuẩn học thuật: Thẻ phân loại + Tiêu đề slide."""
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

    # Đường kẻ phân cách
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.32), Inches(12.133), Pt(1.5))
    line.fill.solid()
    line.fill.fore_color.rgb = LINE
    line.line.color.rgb = LINE


def _footer(slide, current_page, total_pages=8):
    """Footer chuẩn: Mã đề tài + Số trang."""
    foot_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(7.05), Inches(12.133), Pt(1))
    foot_line.fill.solid()
    foot_line.fill.fore_color.rgb = LINE
    foot_line.line.color.rgb = LINE

    tb = slide.shapes.add_textbox(Inches(0.6), Inches(7.12), Inches(9.0), Inches(0.3))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    r = _add_run(p, "CNTT-KLCN142 — Đề xuất thực đơn dinh dưỡng cá nhân hóa bằng DBO/IDBO | Báo cáo Tuần 11")
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


# =========================================================================== #
# SLIDE 1: BÌA BÁO CÁO
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
    p1.space_before = Pt(14)
    r1 = _add_run(p1, "Tối Ưu Hóa Thực Đơn Dinh Dưỡng Cá Nhân Hóa\nBằng Thuật Toán DBO và IDBO")
    _style_run(r1, 30, True, WHITE)

    p2 = tf.add_paragraph()
    p2.space_before = Pt(14)
    r2 = _add_run(p2, "BÁO CÁO TIẾN ĐỘ TUẦN 11 — CHUẨN HÓA THỰC NGHIỆM ĐỘC LẬP,\nĐÁNH GIÁ BUDGET-MATCHED & TÍCH HỢP HỆ THỐNG WEB API")
    _style_run(r2, 16, True, RGBColor(0x6E, 0xC5, 0xC5))

    p3 = tf.add_paragraph()
    p3.space_before = Pt(28)
    r3 = _add_run(p3, "Sinh viên thực hiện:\n"
                      "• Lê Quang Duy (2001210356) — Nhóm trưởng (Thống kê, Báo cáo & Phân tích)\n"
                      "• Hồ Trung Cương (2001215682) — Phụ trách Budget-Matched & Dual Threshold\n"
                      "• Đặng Nguyễn Minh Đăng (2001230175) — Phụ trách Web/API & Trải nghiệm Người dùng\n\n"
                      "Thời gian: Tháng 10/2026 | Bộ môn: Kỹ thuật Dữ liệu & Trí tuệ Nhân tạo")
    _style_run(r3, 13, False, RGBColor(0xE2, 0xE8, 0xF0))


# =========================================================================== #
# SLIDE 2: NGHIỆM THU WEB API & GIAO DIỆN TRỰC QUAN HÓA (W11-F5)
# =========================================================================== #
def build_slide_2(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "Nghiệm Thu Hệ Thống Web API & Trực Quan Hóa Dinh Dưỡng", "Hệ Thống Thực Nghiệm")

    # Cột trái: Hình Radar Chart thực tế sinh từ API
    f5_path = FIG_DIR / "fig_web_radar_nutrition_p1.png"
    if f5_path.exists():
        w, h = _fit_image(f5_path, Inches(5.6), Inches(5.4))
        slide.shapes.add_picture(str(f5_path), Inches(0.6), Inches(1.5), w, h)

    # Cột phải: Báo cáo kỹ thuật ĐÃ LÀM GÌ, DÙNG GÌ
    _card(slide, Inches(6.5), Inches(1.5), Inches(6.2), Inches(5.4))
    tb = slide.shapes.add_textbox(Inches(6.75), Inches(1.7), Inches(5.7), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = _add_run(p0, "Nghiệm Thu Tính Năng Web / API (PR #28)")
    _style_run(r0, 16, True, INDIGO)

    items = [
        ("Công nghệ sử dụng:", "FastAPI backend, Pydantic v2 validation, Uvicorn server, Chart.js, Vanilla HTML/CSS/JS (Dark Theme Glassmorphism)."),
        ("Kiến trúc Single-Port:", "Phục vụ đồng thời REST API (/api/*) và static frontend trên cổng 8000, triệt tiêu lỗi CORS và độ trễ proxy."),
        ("6 Endpoints chuẩn hóa:", "GET /health, GET /profiles, POST /targets (tính BMR/TDEE), POST /menu/generate (chạy solver 2 tầng), GET /foods, POST /menu/swap (stub 501)."),
        ("Xử lý phi nghẽn (Non-blocking):", "Bao bọc two_tier_optimize() bằng asyncio.to_thread, Event Loop không bị khóa khi tối ưu."),
        ("Tuân thủ quy chuẩn khẩu phần:", "Bảng thực đơn hiển thị minh bạch Gram liên tục và Gram làm tròn bước 5g (portion_g_rounded). Dinh dưỡng được tính toán lại chính xác trên gram làm tròn."),
        ("Trực quan hóa đa chiều (W11-F5):", "Biểu đồ Radar thể hiện tỷ lệ % đạt chuẩn 6 trục dinh dưỡng, đi kèm dải dung sai cho phép (80%–120%).")
    ]
    for title, desc in items:
        p = tf.add_paragraph()
        p.space_before = Pt(7)
        rt = _add_run(p, f"• {title} ")
        _style_run(rt, 12, True, INDIGO2)
        rd = _add_run(p, desc)
        _style_run(rd, 11, False, INK)

    _footer(slide, 2)


# =========================================================================== #
# SLIDE 3: ĐỐI ĐẦU DBO vs IDBO TRÊN TẬP ĐỘC LẬP (W11-F1)
# =========================================================================== #
def build_slide_3(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "Thực Nghiệm Đối Đầu DBO vs IDBO Trên Tập Độc Lập (Seed 8003–8010)", "Đánh Giá Thực Nghiệm")

    # Cột trái: Hình biểu đồ đối đầu
    f1_path = FIG_DIR / "fig_fitness_comparison_seed8003_8010.png"
    if f1_path.exists():
        w, h = _fit_image(f1_path, Inches(6.5), Inches(5.4))
        slide.shapes.add_picture(str(f1_path), Inches(0.6), Inches(1.5), w, h)

    # Cột phải: Bảng số liệu và kết luận khoa học
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

    _footer(slide, 3)


# =========================================================================== #
# SLIDE 4: ĐÁNH ĐỔI CHI PHÍ TÀI NGUYÊN (W11-F2)
# =========================================================================== #
def build_slide_4(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "Đánh Đổi Tài Nguyên Tính Toán: Số Lượt Evaluations & Thời Gian Chạy", "Phân Tích Chi Phí")

    f2_path = FIG_DIR / "fig_resource_tradeoff_evals_runtime.png"
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

    _footer(slide, 4)


# =========================================================================== #
# SLIDE 5: PHÂN TÍCH TELEMETRY TẦNG NGOÀI VS TẦNG TRONG (W11-F3)
# =========================================================================== #
def build_slide_5(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "Giải Mã Telemetry: Hoạt Động Của Tầng Ngoài và Tầng Trong", "Cơ Chế IDBO")

    f3_path = FIG_DIR / "fig_telemetry_activations.png"
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

    _footer(slide, 5)


# =========================================================================== #
# SLIDE 6: KIỂM SOÁT NGÂN SÁCH (BUDGET-MATCHED W11-F4)
# =========================================================================== #
def build_slide_6(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "Kiểm Soát Tính Công Bằng Theo Ngân Sách Tính Toán (Budget-Matched)", "Thiết Kế Mới")

    f4_path = FIG_DIR / "fig_budget_matched_smoke.png"
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

    _footer(slide, 6)


# =========================================================================== #
# SLIDE 7: HOÀN THIỆN KIẾN TRÚC NGƯỠNG KÉP (DUAL THRESHOLD)
# =========================================================================== #
def build_slide_7(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "Hoàn Thiện Kiến Trúc Phân Tách Ngưỡng Đa Dạng Kép (Dual Threshold)", "Hoàn Thiện Kiến Trúc")

    _card(slide, Inches(0.6), Inches(1.5), Inches(5.9), Inches(5.4))
    tb1 = slide.shapes.add_textbox(Inches(0.85), Inches(1.7), Inches(5.4), Inches(5.0))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    r1 = _add_run(p1, "Vấn Đề Của Việc Dùng Chung Một Ngưỡng")
    _style_run(r1, 16, True, INDIGO)

    old_pts = [
        ("Bản chất không gian khác biệt:", "Tầng ngoài hoạt động trên không gian nhị phân/rời rạc (chọn món); tầng trong hoạt động trên không gian liên tục (chọn số gram khẩu phần)."),
        ("Độ đo đa dạng không tương thích:", "Tầng ngoài đo khoảng cách Hamming giữa các vector tổ hợp món; tầng trong đo độ lệch vị trí Euclidean của các cá thể liên tục."),
        ("Hạn chế ở Tuần 10:", "Ép dùng chung diversity_threshold = 0.28 cho cả hai tầng là giải pháp mang tính thử nghiệm tạm thời, chưa tối ưu cho tầng trong."),
        ("Yêu cầu chuẩn hóa:", "Cần phân định độc lập hai tham số điều khiển ngưỡng để tối ưu hóa chuyên biệt.")
    ]
    for t, d in old_pts:
        p = tf1.add_paragraph()
        p.space_before = Pt(8)
        rt = _add_run(p, f"• {t}\n  ")
        _style_run(rt, 12, True, RED)
        rd = _add_run(p, d)
        _style_run(rd, 11, False, INK)

    _card(slide, Inches(6.8), Inches(1.5), Inches(5.9), Inches(5.4))
    tb2 = slide.shapes.add_textbox(Inches(7.05), Inches(1.7), Inches(5.4), Inches(5.0))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    r2 = _add_run(p2, "Kiến Trúc TwoTierConfig Mới (Tuần 11)")
    _style_run(r2, 16, True, INDIGO)

    new_pts = [
        ("outer_diversity_threshold = 0.28:", "Được cố định cho tầng ngoài sau khi đã hiệu chỉnh và kiểm nghiệm độc lập."),
        ("inner_diversity_threshold = None (Mặc định):", "Tuân thủ AGENTS.md, nhóm không tự ý gán giá trị cảm tính khi chưa có dữ liệu đo lường."),
        ("Bổ sung trường đo lường thực tế:", "Thu thập inner_diversity_min_observed và inner_diversity_mean_observed trong từng lần chạy để làm cơ sở hiệu chỉnh."),
        ("Đảm bảo kiểm thử tự động:", "Bổ sung unit test xác nhận việc truyền độc lập 2 ngưỡng vào từng solver con mà không gây xung đột tham số.")
    ]
    for t, d in new_pts:
        p = tf2.add_paragraph()
        p.space_before = Pt(8)
        rt = _add_run(p, f"★ {t}\n  ")
        _style_run(rt, 12, True, TEAL)
        rd = _add_run(p, d)
        _style_run(rd, 11, False, INK)

    _footer(slide, 7)


# =========================================================================== #
# SLIDE 8: ĐẢM BẢO CHẤT LƯỢNG MÃ NGUỒN (253/253 TESTS PASS)
# =========================================================================== #
def build_slide_8(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, "Đảm Bảo Chất Lượng Phần Mềm & Nghiệm Thu Mã Nguồn", "Kỹ Thuật Phần Mềm")

    _card(slide, Inches(0.6), Inches(1.5), Inches(3.8), Inches(5.4))
    tb1 = slide.shapes.add_textbox(Inches(0.85), Inches(1.7), Inches(3.3), Inches(5.0))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    r1 = _add_run(p1, "Kiểm Thử Tự Động")
    _style_run(r1, 16, True, INDIGO)

    p_stat = tf1.add_paragraph()
    p_stat.space_before = Pt(14)
    r_stat = _add_run(p_stat, "253 / 253\nPASSED")
    _style_run(r_stat, 26, True, GREEN)

    p_time = tf1.add_paragraph()
    p_time.space_before = Pt(6)
    r_time = _add_run(p_time, "Thời gian thực thi: 22.59s\npytest v9.1.1 | Python 3.12")
    _style_run(r_time, 11.5, False, MUTED)

    p_cov = tf1.add_paragraph()
    p_cov.space_before = Pt(14)
    r_cov = _add_run(p_cov, "Độ bao phủ kiểm thử:\n"
                            "• Core Solver & Behaviors: 82\n"
                            "• Constraints & Menus: 45\n"
                            "• Culinary Realism & Roles: 36\n"
                            "• Data Loader & Schemas: 42\n"
                            "• Budget Enforcement: 27\n"
                            "• FastAPI Routes & Profile: 21")
    _style_run(r_cov, 11, False, INK)

    _card(slide, Inches(4.7), Inches(1.5), Inches(8.0), Inches(5.4))
    tb2 = slide.shapes.add_textbox(Inches(4.95), Inches(1.7), Inches(7.5), Inches(5.0))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    r2 = _add_run(p2, "Tuân Thủ Bất Biến Nghiệp Vụ (Theo AGENTS.md)")
    _style_run(r2, 16, True, INDIGO)

    invariants = [
        ("Tính tái lập tuyệt đối (Deterministic):", "Mọi thuật toán đều nhận seed rõ ràng và dùng RNG cục bộ (np.random.default_rng(seed)). Cùng seed luôn tạo ra cùng một kết quả chính xác."),
        ("Làm tròn khẩu phần 5g minh bạch:", "Nghiệm liên tục -> Làm tròn khẩu phần 5g -> Giải mã thực đơn -> Tính toán lại dinh dưỡng -> Thẩm định tính khả thi (validate_menu). Không báo cáo fitness nghiệm liên tục nhưng hiển thị thực đơn đã làm tròn khác."),
        ("Minh bạch dữ liệu dinh dưỡng:", "Phân định rõ ràng số liệu đo đạc thực tế và số liệu ước tính (sugar_g_estimated). Không đưa ra tuyên bố y tế lâm sàng hoặc cam kết điều trị."),
        ("Bộ lọc Role-based Bounds:", "Loại trừ hoàn toàn các loại bột sống, shortening, phụ gia khỏi candidate pool trước khi đưa vào giao diện đề xuất cho người dùng.")
    ]
    for t, d in invariants:
        p = tf2.add_paragraph()
        p.space_before = Pt(8)
        rt = _add_run(p, f"🛡 {t}\n  ")
        _style_run(rt, 12, True, INDIGO2)
        rd = _add_run(p, d)
        _style_run(rd, 11, False, INK)

    _footer(slide, 8)


def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    print("Building Week 11 Scientific Presentation Slides...")
    build_slide_1(prs)
    build_slide_2(prs)
    build_slide_3(prs)
    build_slide_4(prs)
    build_slide_5(prs)
    build_slide_6(prs)
    build_slide_7(prs)
    build_slide_8(prs)

    prs.save(str(OUT_PPTX))
    print(f"[SUCCESS] Scientific presentation saved to: {OUT_PPTX}")
    print(f"[METRICS] Total slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
