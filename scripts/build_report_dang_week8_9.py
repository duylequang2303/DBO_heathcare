"""Generate Word report (.docx) for Dang's Week 8-9 Ablation Contribution."""

from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

ROOT = Path(__file__).resolve().parents[1]
OUT_DOCX = ROOT / "docs" / "reports" / "member_contributions" / "Phan_Dang_Tuan8_9_Ablation.docx"

def set_cell_background(cell, color_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_report():
    doc = Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Style definitions
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(30, 41, 59)
    normal_style.paragraph_format.line_spacing = 1.25
    normal_style.paragraph_format.space_after = Pt(4)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_title.add_run("TRƯỜNG ĐẠI HỌC CÔNG THƯƠNG TP. HỒ CHÍ MINH\nKHOA CÔNG NGHỆ THÔNG TIN\n—o0o—\n\n")
    run_sub.font.bold = True
    run_sub.font.size = Pt(11)
    run_sub.font.color.rgb = RGBColor(71, 85, 105)

    run_main = p_title.add_run("BÁO CÁO ĐÓNG GÓP CÁ NHÂN — TUẦN 8 & 9\nCHẨN ĐOÁN THỰC NGHIỆM ABLATION DBO VÀ IDBO\n")
    run_main.font.bold = True
    run_main.font.size = Pt(16)
    run_main.font.color.rgb = RGBColor(15, 23, 42)

    run_project = p_title.add_run("Đề tài: Hệ Thống Đề Xuất Thực Đơn Dinh Dưỡng Cá Nhân Hóa (CNTT-KLCN142)\n")
    run_project.font.italic = True
    run_project.font.size = Pt(12)
    run_project.font.color.rgb = RGBColor(37, 99, 235)

    doc.add_paragraph()

    # Student Info Box
    tbl_info = doc.add_table(rows=4, cols=2)
    tbl_info.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_info.autofit = False

    info_data = [
        ("Sinh viên thực hiện:", "Đặng Nguyễn Minh Đăng"),
        ("Mã số sinh viên (MSSV):", "2001230175"),
        ("Vai trò trong đợt thực nghiệm:", "Phụ trách Controlled Activation & Thực nghiệm Đối chuẩn"),
        ("Phụ trách các giai đoạn:", "Gate 3, Phần D, Phần G, Phần I (Theo KE_HOACH_CHAY_LAI_DBO_IDBO.md)")
    ]

    for idx, (label, val) in enumerate(info_data):
        row = tbl_info.rows[idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.5)
        c1.width = Inches(4.0)
        c0.paragraphs[0].add_run(label).font.bold = True
        c1.paragraphs[0].add_run(val)
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "F8FAFC")
        set_cell_margins(c0, 60, 60, 100, 100)
        set_cell_margins(c1, 60, 60, 100, 100)

    doc.add_paragraph()

    # Section 1
    h1 = doc.add_heading("1. TỔNG QUAN VÀ NHIỆM VỤ ĐƯỢC PHÂN CÔNG", level=1)
    h1.style.font.name = 'Times New Roman'
    h1.style.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "Nhằm làm rõ dứt điểm câu hỏi khoa học cốt lõi từ hội đồng đánh giá và giảng viên hướng dẫn: "
        "'Vì sao DBO và IDBO lại cho kết quả fitness giống hệt nhau trên bài toán tối ưu thực đơn dinh dưỡng hai tầng?', "
        "nhóm nghiên cứu đã ban hành kế hoạch rà soát độc lập KE_HOACH_CHAY_LAI_DBO_IDBO.md. "
        "Trong đó, sinh viên Đặng Nguyễn Minh Đăng được phân công phụ trách độc lập các nội dung:"
    )

    p_tasks = doc.add_paragraph()
    p_tasks.add_run("• Gate 3 — Controlled Activation Sanity Check: ").font.bold = True
    p_tasks.add_run("Thiết lập kịch bản kích hoạt cưỡng bức nhằm xác minh đường dây kết nối (wiring check) từ bộ giải Two-Tier Solver sang thuật toán IDBO, chứng minh không có lỗi lập trình ngăn cản IDBO kích hoạt.\n")
    p_tasks.add_run("• Phần G — Thực nghiệm Đối chuẩn Paired Benchmark (10 Seeds): ").font.bold = True
    p_tasks.add_run("Vận hành và giám sát thực nghiệm đối chuẩn trên 10 paired seeds (8001–8010) qua 3 cấu hình chẩn đoán, tính toán và phân tích các chỉ số thống kê (Mean, Median, Std, Best, Worst, Wilcoxon test).\n")
    p_tasks.add_run("• Phần I — Phân tích Hiện tượng Suy giảm Fitness ở 150 Vòng: ").font.bold = True
    p_tasks.add_run("Giải trình nguyên nhân vì sao Mean Fitness ở cấu hình 150 vòng có xu hướng suy giảm so với 25 vòng, chứng minh vai trò của nhiễu ngẫu nhiên (stochastic objective noise) trong mô hình tối ưu hai tầng.")

    # Section 2
    h2 = doc.add_heading("2. KẾT QUẢ THỰC HIỆN GATE 3: CONTROLLED ACTIVATION SANITY CHECK", level=1)
    h2.style.font.name = 'Times New Roman'
    h2.style.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "Để loại trừ hoàn toàn nghi vấn cho rằng IDBO không kích hoạt là do lỗi truyền tham số hoặc lỗi import, "
        "kịch bản controlled_activation được thiết lập với cấu hình nhạy cao: stagnation_window = 2 vòng, "
        "diversity_threshold = 0.50 (cao hơn độ phân tán tự nhiên của bài toán ~0.25), perturbation_rate = 1.0, restart_rate = 1.0 "
        "trên các hạt giống [8001, 8002, 8003]."
    )

    # Table Controlled Activation
    tbl_ctrl = doc.add_table(rows=4, cols=8)
    tbl_ctrl.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers_ctrl = ["Seed", "Best Fitness", "Runtime (s)", "Outer Pert", "Outer Rest", "Inner Pert Total", "Inner Rest Total", "Kết luận Wiring"]
    
    hdr_row = tbl_ctrl.rows[0]
    for idx, h_text in enumerate(headers_ctrl):
        hdr_row.cells[idx].paragraphs[0].add_run(h_text).font.bold = True
        hdr_row.cells[idx].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_background(hdr_row.cells[idx], "1E293B")
        hdr_row.cells[idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        hdr_row.cells[idx].paragraphs[0].runs[0].font.size = Pt(10)
        set_cell_margins(hdr_row.cells[idx], 80, 80, 80, 80)

    ctrl_rows = [
        ("8001", "99.0062", "36.97", "16", "14", "10,074", "4,426", "PASS (Kích hoạt 100%)"),
        ("8002", "97.6149", "37.40", "16", "14", "10,146", "4,354", "PASS (Kích hoạt 100%)"),
        ("8003", "99.3330", "36.55", "18", "12", "10,074", "4,426", "PASS (Kích hoạt 100%)")
    ]

    for r_idx, r_data in enumerate(ctrl_rows):
        row = tbl_ctrl.rows[r_idx + 1]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(val)
            run.font.size = Pt(10)
            if c_idx == 7:
                run.font.bold = True
                run.font.color.rgb = RGBColor(16, 185, 129)
            set_cell_background(cell, "F8FAFC" if r_idx % 2 == 0 else "FFFFFF")
            set_cell_margins(cell, 60, 60, 80, 80)

    doc.add_paragraph()
    doc.add_paragraph(
        "Kết luận Gate 3: Khi ngưỡng kích hoạt được điều chỉnh phù hợp với không gian bài toán (0.50), "
        "cả hai cơ chế Perturbation và Restart của IDBO đều kích hoạt lập tức và mạnh mẽ (Outer kích hoạt 16-18 lần, "
        "Inner kích hoạt hơn 10.000 lần). Điều này khẳng định 100% đường dây kết nối Two-Tier Solver -> IDBO hoạt động hoàn hảo, "
        "hoàn toàn không có lỗi kỹ thuật."
    )

    # Section 3
    h3 = doc.add_heading("3. THỰC NGHIỆM ĐỐI CHUẨN PAIRED BENCHMARK (10 SEEDS)", level=1)
    h3.style.font.name = 'Times New Roman'
    h3.style.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "Đối chuẩn 10 hạt giống ghép cặp (8001–8010) trên Profile chuẩn P1 (Nam 22 tuổi, 65kg, TDEE=2491.6 kcal) "
        "qua 3 cấu hình chẩn đoán: Baseline (25 vòng), Balanced (100 vòng), và Aggressive (150 vòng)."
    )

    # Table Paired Benchmark
    tbl_bench = doc.add_table(rows=7, cols=9)
    tbl_bench.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers_bench = ["Cấu hình", "Thuật toán", "Mean Fit", "Median", "Std", "Mean Min Div", "Outer Pert", "Outer Rest", "Thắng/Hòa/Thua"]

    hdr_b = tbl_bench.rows[0]
    for idx, h_text in enumerate(headers_bench):
        hdr_b.cells[idx].paragraphs[0].add_run(h_text).font.bold = True
        hdr_b.cells[idx].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_background(hdr_b.cells[idx], "1E293B")
        hdr_b.cells[idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        hdr_b.cells[idx].paragraphs[0].runs[0].font.size = Pt(9.5)
        set_cell_margins(hdr_b.cells[idx], 80, 80, 60, 60)

    bench_data = [
        ("Baseline (25 iters)", "DBO", "98.2148", "98.5367", "1.0663", "0.0000", "0", "0", "10 Hòa (Δ=0.0)"),
        ("Baseline (25 iters)", "IDBO", "98.2148", "98.5367", "1.0663", "0.2603", "0", "0", "10 Hòa (Δ=0.0)"),
        ("Balanced (100 iters)", "DBO", "97.9821", "97.9463", "1.0948", "0.0000", "0", "0", "10 Hòa (Δ=0.0)"),
        ("Balanced (100 iters)", "IDBO", "97.9821", "97.9463", "1.0948", "0.2580", "0", "0", "10 Hòa (Δ=0.0)"),
        ("Aggressive (150 iters)", "DBO", "96.3323", "97.7481", "4.5525", "0.0000", "0", "0", "10 Hòa (Δ=0.0)"),
        ("Aggressive (150 iters)", "IDBO", "96.3323", "97.7481", "4.5525", "0.2554", "0", "0", "10 Hòa (Δ=0.0)")
    ]

    for r_idx, r_data in enumerate(bench_data):
        row = tbl_bench.rows[r_idx + 1]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(val)
            run.font.size = Pt(9.5)
            set_cell_background(cell, "F8FAFC" if (r_idx // 2) % 2 == 0 else "FFFFFF")
            set_cell_margins(cell, 60, 60, 60, 60)

    doc.add_paragraph()
    doc.add_paragraph(
        "Bằng chứng telemetry trực tiếp: Dữ liệu đo lường trực tiếp từ IDBOResult chỉ ra rằng min_diversity thực tế "
        "của quần thể luôn dao động trong mức 0.2554 – 0.2603, với giá trị thấp nhất qua toàn bộ các vòng lặp là 0.2422. "
        "Do 0.2422 luôn lớn hơn rất nhiều so với các ngưỡng kích hoạt lý thuyết (0.001, 0.01, 0.05), điều kiện sụp đổ đa dạng "
        "(diversity < threshold) không bao giờ thỏa mãn (0 collapse events). Vì vậy IDBO vận hành theo mã nguồn DBO gốc, "
        "giải thích thỏa đáng và khách quan vì sao kết quả hai thuật toán hòa 100%."
    )

    # Section 4
    h4 = doc.add_heading("4. PHÂN TÍCH HIỆN TƯỢNG SUY GIẢM FITNESS Ở 150 VÒNG (PHẦN I)", level=1)
    h4.style.font.name = 'Times New Roman'
    h4.style.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "Thực nghiệm ghi nhận Mean Fitness giảm từ 98.2148 (ở 25 vòng) xuống 97.9821 (ở 100 vòng) và giảm mạnh xuống 96.3323 (ở 150 vòng), "
        "đồng thời độ lệch chuẩn tăng gấp hơn 4 lần (từ 1.0663 lên 4.5525, Worst fitness tụt xuống 84.0787 tại Seed 8002). "
        "Dưới góc độ tối ưu hóa mô phỏng (Simulation-Optimization), hiện tượng này được giải trình bởi 3 nguyên nhân kỹ thuật:"
    )

    p_causes = doc.add_paragraph()
    p_causes.add_run("1. Bản chất hàm mục tiêu tầng ngoài là Stochastic (Noisy Landscape): ").font.bold = True
    p_causes.add_run("Giá trị hàm mục tiêu của tầng Outer không được tính giải tích mà được xấp xỉ bằng Inner Solver (ngân sách 25 vòng ngẫu nhiên). Giá trị trả về luôn tồn tại nhiễu ngẫu nhiên ε.\n")
    p_causes.add_run("2. Hiện tượng Overfitting vào Đỉnh Nhiễu (Overfitting to Noisy Peaks): ").font.bold = True
    p_causes.add_run("Khi tăng số vòng lặp Outer từ 25 lên 150, số lần lấy mẫu tăng từ 210 lên 1.510 lần. Do không có bộ lọc nhiễu (noise filtering/re-evaluation), thuật toán bị thu hút vào một tổ hợp món z tình cờ nhận điểm cao ngẫu nhiên tại hạt giống inner cụ thể đó.\n")
    p_causes.add_run("3. Sai lệch trong Pha Tái Đánh Giá Cuối Cùng (Final Evaluation Discrepancy): ").font.bold = True
    p_causes.add_run("Ở bước cuối, nghiệm tốt nhất z* được giải lại khẩu phần với hạt giống chuẩn hóa (seed = base_seed). Nghiệm may mắn ảo bộc lộ sai số và suy giảm điểm số thực tế.")

    # Section 5
    h5 = doc.add_heading("5. TỔNG KẾT ĐÓNG GÓP", level=1)
    h5.style.font.name = 'Times New Roman'
    h5.style.font.color.rgb = RGBColor(15, 23, 42)

    p_summary = doc.add_paragraph()
    p_summary.add_run("• Đã kiểm chứng thành công tính toàn vẹn của mã nguồn IDBO trong Two-Tier Solver qua Gate 3 (Controlled Activation).\n")
    p_summary.add_run("• Đã hoàn thành đối chuẩn 10 paired seeds trên 3 cấu hình thử nghiệm, trích xuất đầy đủ 100% các trường telemetry trực tiếp.\n")
    p_summary.add_run("• Đã xây dựng luận điểm khoa học vững chắc giải thích nguyên nhân suy giảm fitness ở 150 vòng, bảo vệ tính trung thực và chiều sâu học thuật của đề tài.")

    # Signatures
    doc.add_paragraph("\n")
    tbl_sign = doc.add_table(rows=2, cols=2)
    tbl_sign.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_sign.rows[0].cells[0].paragraphs[0].add_run("XÁC NHẬN CỦA NHÓM TRƯỞNG\n(Lê Quang Duy)").font.bold = True
    tbl_sign.rows[0].cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    tbl_sign.rows[0].cells[1].paragraphs[0].add_run("SINH VIÊN BÁO CÁO\n(Đặng Nguyễn Minh Đăng)").font.bold = True
    tbl_sign.rows[0].cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    tbl_sign.rows[1].cells[0].paragraphs[0].add_run("\n\n\n__________________________").font.color.rgb = RGBColor(148, 163, 184)
    tbl_sign.rows[1].cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    tbl_sign.rows[1].cells[1].paragraphs[0].add_run("\n\n\n__________________________").font.color.rgb = RGBColor(148, 163, 184)
    tbl_sign.rows[1].cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT_DOCX))
    print(f"Report saved successfully at: {OUT_DOCX}")

if __name__ == "__main__":
    create_report()
