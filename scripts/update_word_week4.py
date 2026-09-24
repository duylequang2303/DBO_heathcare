import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCX_PATH = ROOT / "docs" / "Bao_Cao_Tuan_4_Cuong.docx"
EXP_DIR = ROOT / "experiments" / "week4"
SUMMARY_CSV = EXP_DIR / "dbo_benchmark_summary.csv"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def update_week4_docx():
    print(f"Loading {DOCX_PATH}...")
    doc = docx.Document(str(DOCX_PATH))
    df_sum = pd.read_csv(SUMMARY_CSV)

    # 1. Cập nhật Bảng 4.1 (Table 1: Tham số cấu hình)
    t1 = doc.tables[1]
    for row in t1.rows:
        cells = [c.text.strip() for c in row.cells]
        if "Số chiều" in cells[0]:
            row.cells[1].text = "10, 30, 50"
        elif "Tổng số lượt chạy" in cells[0]:
            row.cells[1].text = "6 × 3 × 30 = 540 (dims: 10, 30, 50)"

    # 2. Cập nhật Bảng 5.1 (Table 2: Kết quả DBO 18 dòng)
    t2 = doc.tables[2]
    # Xóa các dòng dữ liệu cũ (giữ lại header)
    while len(t2.rows) > 1:
        tr = t2.rows[-1]._tr
        t2._tbl.remove(tr)

    # Thêm 18 dòng dữ liệu mới từ df_sum
    for _, r in df_sum.iterrows():
        row_cells = t2.add_row().cells
        row_cells[0].text = str(r["function"])
        row_cells[1].text = str(r["dim"])
        row_cells[2].text = str(int(r["runs"]))
        row_cells[3].text = f"{r['best']:.4e}"
        row_cells[4].text = f"{r['mean']:.4e}"
        row_cells[5].text = f"{r['std']:.4e}"
        row_cells[6].text = f"{r['worst']:.4e}"
        for c in row_cells:
            for p in c.paragraphs:
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                for run in p.runs:
                    run.font.size = Pt(9.5)
                    run.font.name = "Times New Roman"

    # 3. Cập nhật các đoạn văn bản
    text_updates = {
        68: "Mỗi lần chạy khởi tạo quần thể bằng bộ sinh số ngẫu nhiên NumPy theo seed tương ứng. File dbo_benchmark_runs.csv ghi chi tiết 540 lần chạy; dbo_benchmark_summary.csv tổng hợp best, mean, std và worst cho 18 cấu hình (dims: 10, 30, 50).",
        70: "Thí nghiệm chính thức hoàn thành đầy đủ 540/540 lượt chạy. Bảng 5.1 trình bày chi tiết 18 cấu hình (6 hàm × 3 số chiều: 10, 30, 50), mỗi cấu hình gồm 30 lần chạy độc lập (M = 30).",
        72: "Dưới đây là các đồ thị trực quan hóa kết quả thực nghiệm DBO trên 6 hàm benchmark: Hình W4-F1 biểu diễn đường cong hội tụ đa chiều và Hình W4-F2 biểu diễn biểu đồ hộp (Boxplot) phân bố sai số qua 3 số chiều (10, 30, 50).",
        74: "Hình W4-F1: Đồ thị hội tụ đa chiều của DBO (dims = 10, 30, 50), M = 30",
        76: "Hình W4-F2: Biểu đồ hộp (Boxplot) phân bố best fitness qua các số chiều (dims = 10, 30, 50), M = 30",
        79: "Sphere đạt giá trị mean cực kỳ sát 0 ở cả ba số chiều: 3,4933×10⁻¹⁵³ (10D), 2,0602×10⁻¹⁵⁸ (30D) và 5,7003×10⁻¹⁶⁸ (50D). Giá trị Best tương ứng đạt 1,4553×10⁻²⁰¹, 8,2110×10⁻²¹⁴ và 7,1270×10⁻¹⁹⁸. Do nghiệm tối ưu toàn cục của Sphere là 0, các số liệu này chứng minh DBO hội tụ cực kỳ mạnh mẽ và duy trì độ chính xác cao ngay cả khi tăng lên 50 chiều.",
        80: "Schwefel 2.22 tiếp tục thể hiện độ hội tụ sâu với mean đạt 6,7026×10⁻⁸² (10D), 3,6040×10⁻⁸⁷ (30D) và 4,1842×10⁻⁸² (50D). Ngược lại, hàm thung lũng Rosenbrock cho thấy thử thách rõ rệt khi số chiều tăng cao: mean tăng từ 5,6108 ở 10D lên 26,229 ở 30D và 46,648 ở 50D; best ở 50D đạt 45,866, cách xa so với optimum 0.",
        82: "Rastrigin là hàm đa cực trị với rất nhiều cực tiểu địa phương. Tại 10D, mean đạt 2,7413 (std 4,9053, worst 16,914); tại 30D, mean là 4,8471 (std 21,245, worst 115,56), cho thấy một số lần chạy bị vướng tại các cực trị cục bộ. Tuy nhiên, tại 50D, DBO đạt độ ổn định tuyệt đối với 100% các lần chạy (30/30 runs) đều tìm được nghiệm chính xác 0 (best, mean, std và worst đều bằng 0.0000e+00).",
        83: "Ackley đạt giá trị 4,4409×10⁻¹⁶ (ngưỡng giới hạn sai số dấu phẩy động chuẩn IEEE 754) ở 100% các lần chạy trên cả 3 số chiều 10D, 30D và 50D. Griewank có sai số nhỏ ở 10D (mean 3,4904×10⁻²), nhưng khi số chiều tăng lên 30D và 50D thì 100% số lần chạy đều đạt nghiệm tối ưu tuyệt đối 0.",
        85: "Khi tăng số chiều từ 10 lên 30 và 50, mức độ ảnh hưởng phụ thuộc vào đặc tính hình học của từng hàm. Các hàm cầu và lồi đơn giản (Sphere, Schwefel 2.22, Ackley, Griewank) duy trì khả năng hội tụ tiệm cận 0 rất tốt. Hàm Rosenbrock chịu ảnh hưởng mạnh nhất từ số chiều do đáy thung lũng hẹp và xoắn. Rastrigin ở số chiều lớn (50D) thể hiện sự vượt trội khi tránh bẫy cực trị tốt hơn nhờ cơ chế phân tán của quần thể.",
        86: "Về khả năng hội tụ của Sphere, kết quả thực nghiệm M = 30 khẳng định DBO hội tụ hoàn toàn về lân cận sát 0 của nghiệm tối ưu (10D: mean 3,4933×10⁻¹⁵³, 50D: mean 5,7003×10⁻¹⁶⁸). Quá trình hội tụ diễn ra trơn tru và liên tục giảm theo số vòng lặp như thể hiện trên đồ thị Hình W4-F1.",
        88: "Tuần 4 đã hoàn thành toàn diện baseline DBO gốc trên sáu hàm benchmark với cấu hình chuẩn (30 cá thể, 500 vòng lặp, 30 lần chạy độc lập) trên cả 3 số chiều 10, 30 và 50. Toàn bộ 540 lượt chạy hoàn tất thành công, cung cấp bộ số liệu nền tảng 18 dòng tin cậy để so sánh với thuật toán cải tiến IDBO ở tuần 5–6."
    }

    for idx, text in text_updates.items():
        if idx < len(doc.paragraphs):
            doc.paragraphs[idx].text = text

    # 4. Thay thế hình ảnh tại paragraph 73 và 75
    # Xóa hình cũ tại P73 và P75
    p73 = doc.paragraphs[73]
    p73.text = ""
    run73 = p73.add_run()
    img_conv = str(EXP_DIR / "fig_convergence_multidim.png")
    run73.add_picture(img_conv, width=Inches(6.2))
    p73.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p75 = doc.paragraphs[75]
    p75.text = ""
    run75 = p75.add_run()
    img_box = str(EXP_DIR / "fig_boxplot_multidim.png")
    run75.add_picture(img_box, width=Inches(6.2))
    p75.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 5. Bổ sung các hình chi tiết từng dimension (10, 30, 50) vào cuối mục 5 để tài liệu đầy đủ và trực quan
    # Thêm sau paragraph 76
    p_after_76 = doc.paragraphs[76]
    # Tạo paragraph chèn các hình chi tiết
    p_sub_title = doc.add_paragraph()
    p_sub_title.text = "Chi tiết đường cong hội tụ theo từng số chiều (dim = 10, 30, 50):"
    p_sub_title.runs[0].font.bold = True
    p_sub_title.runs[0].font.size = Pt(11)

    for d in [10, 30, 50]:
        img_d = EXP_DIR / f"fig_convergence_dim{d}.png"
        if img_d.exists():
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.add_run().add_picture(str(img_d), width=Inches(6.0))
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_cap = p_cap.add_run(f"Hình: Chi tiết đường hội tụ 6 hàm benchmark ở dim = {d} (M = 30)")
            r_cap.font.italic = True
            r_cap.font.size = Pt(10)

    # Lưu file
    doc.save(str(DOCX_PATH))
    print(f"[OK] Successfully updated {DOCX_PATH}")

if __name__ == "__main__":
    update_week4_docx()
