import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCX_PATH = ROOT / "docs" / "Phan_Cuong_Tuan5_6_IDBO.docx"
EXP_DIR = ROOT / "experiments" / "week5_6"
EXP_W4 = ROOT / "experiments" / "week4"
SUMMARY_CSV = EXP_DIR / "idbo_vs_dbo_summary.csv"
RUNS_CSV = EXP_DIR / "idbo_vs_dbo_runs.csv"

FUNC_ORDER = ['sphere', 'schwefel_2_22', 'rosenbrock', 'rastrigin', 'ackley', 'griewank']
DIMS_ORDER = [10, 30, 50]

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="2B5C8F"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def update_week5_6_docx():
    print(f"Loading and rebuilding {DOCX_PATH} with protocol order and accurate figures...")
    doc = docx.Document(str(DOCX_PATH))

    df_sum = pd.read_csv(SUMMARY_CSV)
    df_runs = pd.read_csv(RUNS_CSV)

    # 1. Cập nhật đoạn dẫn paragraph 28 và 29
    if len(doc.paragraphs) > 28:
        doc.paragraphs[28].text = "Từ kết quả thực nghiệm toàn diện với M = 30, lọc các lượt chạy của thuật toán IDBO trên 3 số chiều (10, 30, 50), số lần kích hoạt trung bình của random perturbation và random restart theo từng hàm benchmark được tổng hợp như sau:"
        doc.paragraphs[28].runs[0].font.name = "Times New Roman"
    if len(doc.paragraphs) > 29:
        doc.paragraphs[29].text = "Bảng 3.1: Số lần kích hoạt trung bình của Perturbation và Restart (dims: 10, 30, 50; M = 30)"
        doc.paragraphs[29].runs[0].font.name = "Times New Roman"

    # Thay thế hoàn toàn Table 1 bằng table 4 cột mới chuẩn hóa theo protocol
    t1_old = doc.tables[1]
    p_parent = t1_old._tbl.getparent()

    new_t1 = doc.add_table(rows=1, cols=4)
    headers_t1 = ["Hàm benchmark", "Số chiều", "Mean Perturbations", "Mean Restarts"]
    for i, h in enumerate(headers_t1):
        cell = new_t1.rows[0].cells[i]
        cell.text = h
        set_cell_background(cell, "EAECEF")
        set_cell_margins(cell, 60, 60, 80, 80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.bold = True
            r.font.size = Pt(9.5)

    idbo_runs = df_runs[df_runs['algorithm'] == 'idbo']
    for f in FUNC_ORDER:
        for d in DIMS_ORDER:
            sub = idbo_runs[(idbo_runs['function'] == f) & (idbo_runs['dim'] == d)]
            m_pert = sub['n_perturbations'].mean()
            m_rest = sub['n_restarts'].mean()
            r_cells = new_t1.add_row().cells
            r_cells[0].text = f
            r_cells[1].text = str(d)
            r_cells[2].text = f"{m_pert:.4f}"
            r_cells[3].text = f"{m_rest:.4f}"
            for i, c in enumerate(r_cells):
                set_cell_margins(c, 40, 40, 60, 60)
                p = c.paragraphs[0]
                if i == 1:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif i in [2, 3]:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(9.0)

    set_table_borders(new_t1)
    t1_old._tbl.addprevious(new_t1._tbl)
    p_parent.remove(t1_old._tbl)

    if len(doc.paragraphs) > 30:
        doc.paragraphs[30].text = (
            "Nhận xét thống kê kích hoạt: Trên các hàm lồi đơn giản (Sphere, Schwefel 2.22), quần thể co cụm cực kỳ nhanh dẫn đến "
            "diversity giảm sâu dưới 1e-3, kích hoạt cơ chế Restart (cao nhất ở Sphere 10D đạt 0.5333 lần/run). Với Rosenbrock ở 30D và 50D, "
            "cơ chế Random Perturbation được kích hoạt (trung bình 0.1000 và 0.0667 lần/run) để bơm nhiễu thoát thung lũng khi nghiệm bị kẹt "
            "nhưng chưa đủ độ trễ để restart. Các hàm Ackley và Rastrigin duy trì độ phân tán tự nhiên cao nên số lần kích hoạt perturbation "
            "và restart bằng đúng 0.0000, tránh can thiệp lãng phí tài nguyên tính toán."
        )
        for r in doc.paragraphs[30].runs:
            r.font.name = "Times New Roman"

    # Thay thế hoàn toàn Table 2 (Bảng so sánh DBO vs IDBO) bằng bảng 9 cột chuẩn protocol
    t2_old = doc.tables[2]
    p_parent2 = t2_old._tbl.getparent()

    new_t2 = doc.add_table(rows=1, cols=9)
    headers_t2 = ["Hàm", "Dim", "Algo", "Best", "Mean", "Std", "Worst", "Mean Evals", "Thắng (mean)"]
    for i, h in enumerate(headers_t2):
        cell = new_t2.rows[0].cells[i]
        cell.text = h
        set_cell_background(cell, "2B5C8F")
        set_cell_margins(cell, 60, 60, 60, 60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(8.0)

    for f in FUNC_ORDER:
        for d in DIMS_ORDER:
            r_dbo = df_sum[(df_sum['algorithm'] == 'dbo') & (df_sum['function'] == f) & (df_sum['dim'] == d)].iloc[0]
            r_idbo = df_sum[(df_sum['algorithm'] == 'idbo') & (df_sum['function'] == f) & (df_sum['dim'] == d)].iloc[0]

            m_dbo = r_dbo['mean']
            m_idbo = r_idbo['mean']
            denom = max(abs(m_dbo), 1e-30)
            rel_diff = abs(m_idbo - m_dbo) / denom
            if rel_diff < 0.01:
                win_text = "Hòa"
            elif m_idbo < m_dbo:
                win_text = "IDBO"
            else:
                win_text = "DBO"

            for algo_row in [r_dbo, r_idbo]:
                rc = new_t2.add_row().cells
                rc[0].text = str(algo_row['function'])
                rc[1].text = str(algo_row['dim'])
                rc[2].text = str(algo_row['algorithm']).upper()
                rc[3].text = f"{algo_row['best']:.3e}"
                rc[4].text = f"{algo_row['mean']:.3e}"
                rc[5].text = f"{algo_row['std']:.3e}"
                rc[6].text = f"{algo_row['worst']:.3e}"
                rc[7].text = f"{algo_row['mean_n_evaluations']:.1f}"
                rc[8].text = win_text

                bg_col = "F4F7FB" if algo_row['algorithm'] == 'idbo' else "FFFFFF"
                for i, c in enumerate(rc):
                    set_cell_background(c, bg_col)
                    set_cell_margins(c, 25, 25, 40, 40)
                    p = c.paragraphs[0]
                    if i in [1, 2, 8]:
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    elif i in [3, 4, 5, 6, 7]:
                        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    for run in p.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(7.5)

    set_table_borders(new_t2)
    t2_old._tbl.addprevious(new_t2._tbl)
    p_parent2.remove(t2_old._tbl)

    # Cập nhật Mục 5: ĐÁNH GIÁ VÀ KẾT LUẬN
    conclusion_points = [
        "1. Hiệu năng tìm kiếm: Trên 6 hàm benchmark tiêu chuẩn liên tục, cả DBO và IDBO đều đạt hiệu quả giải tối ưu xuất sắc. "
        "Sphere đạt tiệm cận từ 1.455e-201 đến 3.493e-153 ở 10D, Schwefel đạt 6.703e-82 ở 10D, Ackley đạt đúng sai số dấu phẩy động 4.441e-16 ở mọi số chiều, "
        "Griewank đạt nghiệm tối ưu tuyệt đối 0 ở 30D và 50D, Rastrigin đạt tuyệt đối 0 ở 50D trên 100% các lần chạy (30/30 runs); "
        "Rosenbrock có mean ~5.61 (10D), 26.23 (30D), 46.65 (50D). "
        "Kết quả so sánh giữa IDBO và DBO là Hòa trên toàn bộ 18/18 cấu hình, chứng minh IDBO duy trì chất lượng nghiệm tương đương và không phá vỡ ưu thế của DBO gốc.",

        "2. Cơ chế kích hoạt có điều kiện: Random Perturbation và Random Restart trong IDBO hoạt động hoàn toàn tự động theo điều kiện "
        "(chỉ kích hoạt khi Diversity < 10⁻³ và có độ trễ Stagnation ≥ 25). Do đó, thuật toán không gây xáo trộn vô ích, không làm giảm tốc độ hội tụ tự nhiên của DBO: "
        "Sphere 10D đạt mean restart 0.5333 lần/run; Rosenbrock 30D đạt mean perturb 0.1000 lần/run; Ackley và Rastrigin hoàn toàn không kích hoạt ngoài ý muốn (0.0000 lần/run).",

        "3. Chi phí đánh giá hàm mục tiêu: Thuật toán DBO gốc tiêu thụ cố định 15030.0 lần đánh giá hàm (evals). "
        "IDBO chỉ tăng thêm rất ít số lần đánh giá hàm do chỉ đánh giá lại các cá thể bị can thiệp "
        "(Mean Evals trung bình ~15030.0 đến 15034.3 evals, trong đó cao nhất ở Sphere 10D đạt 15034.3 evals, chênh lệch chỉ 4.3 evals/run), hoàn toàn bảo toàn tài nguyên tính toán.",

        "4. Chuẩn bị cho bài toán thực đơn tuần 7: Bài toán xây dựng thực đơn dinh dưỡng cá nhân hóa là bài toán tối ưu tổ hợp đa mục tiêu, "
        "không gian tìm kiếm rời rạc và có rất nhiều ràng buộc phi tuyến (calo, nhóm chất protein/lipid/glucid, natri, bệnh lý tiểu đường, tim mạch). "
        "Trong không gian nghiệm phức tạp này, hiện tượng quần thể bị kẹt cực trị cục bộ hoặc mất đa dạng diễn ra thường xuyên hơn nhiều so với benchmark liên tục. "
        "Cơ chế đo Diversity, Random Perturbation và Random Restart của IDBO đã hoàn thiện và kiểm chứng thành công, sẵn sàng tích hợp trực tiếp vào module gợi ý thực đơn ở tuần 7 "
        "(Lưu ý: Nhiệm vụ này thuộc kế hoạch tuần 7, tuần này chưa triển khai)."
    ]

    # Cập nhật các đoạn văn kết luận ở cuối file
    # Tìm paragraph bắt đầu bằng '5. ĐÁNH GIÁ KẾT QUẢ VÀ KẾT LUẬN'
    sec5_idx = None
    for idx, p in enumerate(doc.paragraphs):
        if "5. ĐÁNH GIÁ" in p.text:
            sec5_idx = idx
            break

    if sec5_idx is not None:
        for i, pt in enumerate(conclusion_points):
            p_target_idx = sec5_idx + 1 + i
            if p_target_idx < len(doc.paragraphs):
                doc.paragraphs[p_target_idx].text = pt
                for r in doc.paragraphs[p_target_idx].runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(10.5)

    # Đảm bảo toàn bộ fonts trong document là Times New Roman và không có chữ 'dim=2'
    for p in doc.paragraphs:
        if "dim=2" in p.text.lower() or "bỏ dim=2" in p.text.lower():
            p.text = p.text.replace(" (bỏ dim=2)", "").replace(" (Bỏ dim=2)", "").replace("Bỏ số chiều dim=2 do không gian quá đơn giản; ", "")
        for r in p.runs:
            r.font.name = "Times New Roman"

    doc.save(str(DOCX_PATH))
    print(f"[OK] Successfully rebuilt and saved {DOCX_PATH}")

if __name__ == "__main__":
    update_week5_6_docx()
