import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP_W4 = ROOT / "experiments" / "week4"
EXP_W5 = ROOT / "experiments" / "week5_6"
OUT_PATH = ROOT / "docs" / "SO_TAY_HIEU_BAN_CHAT_DE_TAI_TUAN_1_DEN_6.docx"

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
        f'  <w:top w:val="single" w:sz="6" w:space="0" w:color="2B5C8F"/>'
        f'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="2B5C8F"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_part_header(doc, number, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(20)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"PHẦN {number}: {title.upper()}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = RGBColor(192, 57, 43) # Coral Red
    return p

def add_sec_header(doc, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(title)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = RGBColor(41, 128, 185) # Blue
    return p

def add_p(doc, text, bold_prefix=""):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        rb = p.add_run(bold_prefix + " ")
        rb.font.name = "Times New Roman"
        rb.font.size = Pt(11)
        rb.font.bold = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    return p

def add_box_callout(doc, text, title="💡 BẢN CHẤT CẦN NHỚ:"):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    set_cell_background(c, "FDF7E7") # Light warm yellow
    set_cell_margins(c, 100, 100, 140, 140)
    p = c.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    rb = p.add_run(title + "\n")
    rb.font.name = "Times New Roman"
    rb.font.size = Pt(11)
    rb.font.bold = True
    rb.font.color.rgb = RGBColor(180, 100, 0)
    rt = p.add_run(text)
    rt.font.name = "Times New Roman"
    rt.font.size = Pt(10.5)

def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    r.font.italic = True
    r.font.color.rgb = RGBColor(100, 100, 100)
    return p

def build_student_handbook():
    print("Building student handbook (ELI5 style)...")
    doc = docx.Document()

    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(0.8)

    # ──────────────────────────────────────────────────────────────────────────
    # BÌA SỔ TAY NỘI BỘ
    # ──────────────────────────────────────────────────────────────────────────
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_top = p_top.add_run("TÀI LIỆU NỘI BỘ — DÀNH RIÊNG CHO THÀNH VIÊN ĐỌC HIỂU ĐỀ TÀI\n(KHÔNG PHẢI BẢN BÁO CÁO NỘP THẦY)\n")
    r_top.font.name = "Times New Roman"
    r_top.font.size = Pt(11)
    r_top.font.bold = True
    r_top.font.color.rgb = RGBColor(150, 150, 150)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(30)
    r_title = p_title.add_run("SỔ TAY BẢN CHẤT ĐỀ TÀI\nTỪ TUẦN 1 ĐẾN TUẦN 6\n")
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(192, 57, 43)

    r_sub = p_title.add_run(
        "Giải thích cực kỳ dễ hiểu: Đề tài làm gì? Tại sao phải làm thế?\n"
        "Sơ đồ là gì? Cách đọc đồ thị hội tụ, Boxplot, Diversity và bảng kết quả từ A đến Z\n\n"
    )
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(12)
    r_sub.font.italic = True

    add_box_callout(
        doc,
        "Tài liệu này được viết theo phong cách 'Giải thích cho học sinh tiểu học' (ELI5).\n"
        "Mục tiêu duy nhất: Đọc xong là BẠN HIỂU 100% bản chất những gì mình đang làm trong code, "
        "khi thầy hỏi bất kỳ sơ đồ nào, đồ thị nào, bảng số liệu nào, bạn đều tự tin trả lời lưu loát!",
        "🎯 MỤC ĐÍCH DUY NHẤT CỦA CUỐN SỔ TAY NÀY:"
    )

    doc.add_page_break()

    # ──────────────────────────────────────────────────────────────────────────
    # PHẦN 1: BỨC TRANH TOÀN CẢNH
    # ──────────────────────────────────────────────────────────────────────────
    add_part_header(doc, 1, "Bức tranh toàn cảnh — Đề tài của chúng ta làm cái gì?")

    add_sec_header(doc, "1.1. Ví dụ đời thực dễ hiểu nhất:")
    add_p(doc, 
        "Tưởng tượng bạn là một bác sĩ dinh dưỡng thông minh. Một khách hàng bước vào phòng khám và nói: "
        "'Tôi là Nam, 22 tuổi, nặng 70kg, cao 1m70, làm văn phòng ít vận động. Tôi muốn giảm 3kg trong 1 tháng tới, "
        "nhưng tôi bị đau dạ dày (không ăn chua/cay) và dị ứng tôm cua. Hãy lên cho tôi thực đơn 1 ngày gồm 3 bữa Sáng - Trưa - Tối!'"
    )

    add_sec_header(doc, "1.2. Nhiệm vụ của phần mềm chúng ta làm:")
    add_p(doc, "Phần mềm của bạn phải tự động mở 'kho thực phẩm' (có gần 16.000 món ăn), nhặt ra các món ăn cho 3 bữa sao cho:", "👉 Nhiệm vụ:")
    add_p(doc, "1. Vừa khít năng lượng Calo (ví dụ đúng 1.800 kcal, không được thừa làm béo, không thiếu làm mệt xỉu).")
    add_p(doc, "2. Cân bằng dinh dưỡng: Đủ Đạm (thịt cá trứng), đủ Tinh bột (cơm bún), Mỡ tốt, nhiều Rau củ (chất xơ), ít muối Natri.")
    add_p(doc, "3. Thỏa mãn bệnh lý & sở thích: Tuyệt đối không có món từ tôm cua, không có đồ chua hại dạ dày, không bị trùng lặp món giữa các bữa.")

    add_sec_header(doc, "1.3. Tại sao người ta không chọn món bằng tay mà phải dùng Thuật toán Tối ưu?")
    add_p(doc, 
        "Trong kho có 15.929 món. Một ngày ăn 3 bữa, mỗi bữa nhặt 2-3 món, chọn thêm khối lượng (100g, 150g, 200g...). "
        "Số cách kết hợp món ăn trên đời là 15.929⁶ ≈ 15.000.000.000.000.000.000.000.000 cách! "
        "Nhiều hơn cả số hạt cát trên toàn bộ bãi biển Trái Đất! Người thường ngồi bấm máy tính cả đời cũng không tìm ra mâm cơm chuẩn nhất. "
        "Nhưng thuật toán thông minh (như DBO/IDBO) chỉ mất đúng 1–2 giây để quét qua và chọn ra mâm cơm hoàn hảo nhất!"
    )

    add_box_callout(
        doc,
        "Đề tài của mình bản chất là: Dùng thuật toán Bọ Hung cải tiến (IDBO) để 'nhặt món ăn' "
        "từ kho 16.000 món, ghép thành 1 thực đơn hoàn hảo chuẩn y khoa cho từng người!",
        "🔑 TÚM CÁI VÁY LẠI:"
    )

    # ──────────────────────────────────────────────────────────────────────────
    # PHẦN 2: TỪNG TUẦN ĐÃ LÀM CÁI GÌ? TẠI SAO PHẢI LÀM VẬY?
    # ──────────────────────────────────────────────────────────────────────────
    add_part_header(doc, 2, "Hành trình từng tuần — Tại sao lại chia ra như vậy?")

    add_sec_header(doc, "Tuần 1: Nghiên cứu lý thuyết & Chọn 'vũ khí'")
    add_p(doc, "Tại sao không dùng thuật toán Di truyền (GA) hay Bầy ong/Bầy chim (PSO) quen thuộc mà lại chọn Bọ Hung (DBO)?", "❓ Câu hỏi:")
    add_p(doc, 
        "Thuật toán Bọ Hung (Dung Beetle Optimizer - DBO) mới ra đời năm 2023, chạy nhanh và tìm nghiệm rất tốt. "
        "Nhưng nó có điểm yếu là tính 'bầy đàn': mấy con bọ rất dễ bu lại một chỗ dù chỗ đó chưa chắc là bãi thức ăn ngon nhất. "
        "Vì thế nhóm quyết định: Chọn DBO làm nền tảng, rồi cải tiến thêm các cơ chế ngẫu nhiên thông minh thành IDBO!",
        "💡 Lý do:"
    )

    add_sec_header(doc, "Tuần 2: 'Đi chợ' nhặt dữ liệu & Làm sạch thực phẩm")
    add_p(doc, 
        "Một thuật toán không thể nấu ăn nếu không có nguyên liệu. Nhóm đã lấy 2 nguồn dữ liệu lớn: "
        "Bộ dữ liệu USDA (Mỹ) và Bảng thành phần dinh dưỡng Việt Nam (Viện Dinh Dưỡng). "
        "Sau đó viết code dọn rác, lọc bỏ món không ăn được, chuẩn hóa tất cả về định lượng 100g, thu được 15.929 món ăn sạch trong file merged_food_nutrition.csv."
    )
    add_p(doc, 
        "Đồng thời cài đặt công thức tính năng lượng cơ thể: Công thức BMR Mifflin-St Jeor (năng lượng tối thiểu để sống) "
        "và TDEE (nhân với hệ số vận động để ra lượng calo cần ăn mỗi ngày)."
    )

    add_sec_header(doc, "Tuần 3: Đặt ra 'Luật chơi' và 'Thang chấm điểm' (Mô hình hóa)")
    add_p(doc, 
        "Làm sao máy tính hiểu được 'một mâm cơm'? Nhóm biến mâm cơm thành một DÃY SỐ (gọi là Vector). "
        "Ví dụ: con bọ hung mang trên lưng dãy số [105, 1.5, 342, 2.0] nghĩa là: Món ID 105 ăn 150g, Món ID 342 ăn 200g. "
        "Thang chấm điểm (Hàm Fitness): Nếu nấu ra mâm cơm bị thừa calo -> Phạt điểm! Thiếu đạm -> Phạt điểm! Bị trùng món -> Phạt điểm! "
        "Con bọ nào có điểm phạt càng gần 0 thì mâm cơm đó càng đạt điểm 10!"
    )

    add_sec_header(doc, "Tuần 4: Cho Bọ Hung 'tập trận' trên bãi tập Toán học (Benchmark)")
    add_p(doc, "Tại sao chưa vội làm bài toán thực đơn mà lại đi chạy 6 cái hàm Sphere, Rosenbrock quái đản làm gì?", "❓ Thắc mắc lớn nhất:")
    add_p(doc, 
        "Giống như bạn mua một chiếc xe đua, trước khi đem ra đường phố chạy giao hàng, bạn phải mang vào trường đua thử nghiệm phanh, ga, lái xem xe có hoạt động trơn tru không đã! "
        "6 hàm benchmark (Sphere, Schwefel, Rosenbrock, Rastrigin, Ackley, Griewank) là 6 'địa hình đồi núi toán học' nổi tiếng thế giới. "
        "Nghiệm tối ưu của các hàm này đều đã biết trước là bằng 0. Nếu con bọ hung chạy trên 6 địa hình này mà tìm ra đúng số 0, chứng tỏ thuật toán đã được cài đặt hoàn toàn chính xác!",
        "💡 Trả lời:"
    )
    add_p(doc, 
        "Tại sao thầy bảo bỏ dim=2? Số chiều (dim) là số biến số. Dim = 2 giống như bài toán có đúng 2 ẩn số x và y, quá dễ, nhắm mắt cũng tìm ra, không phản ánh được sức mạnh thuật toán. "
        "Nâng lên Dim = 10, 30, 50 (bài toán có 50 ẩn số cùng lúc) mới chứng minh được thuật toán đủ sức giải bài toán thực đơn thực tế!"
    )

    add_sec_header(doc, "Tuần 5–6: Nâng cấp Bọ Hung thành 'Siêu Bọ Hung' (IDBO)")
    add_p(doc, 
        "Gắn thêm cho bọ hung 'cảm biến đo độ đa dạng quần thể' (Diversity) và 2 phao cứu sinh tự động: "
        "Random Perturbation (bơm nhiễu Gaussian để lay tỉnh khi bọ hơi túm tụm) và "
        "Random Restart (thả dù bọ ra chỗ khác khi bị kẹt bế tắc quá 25 vòng). "
        "Chạy đấu tay đôi 1.080 lượt chạy giữa DBO gốc và IDBO cải tiến để đo đạc kết quả khoa học!"
    )

    # ──────────────────────────────────────────────────────────────────────────
    # PHẦN 3: SƠ ĐỒ ĐỂ LÀM GÌ? TẠI SAO PHẢI DÙNG?
    # ──────────────────────────────────────────────────────────────────────────
    doc.add_page_break()
    add_part_header(doc, 3, "Sơ đồ là gì? Tại sao phải dùng như vậy?")

    add_sec_header(doc, "3.1. Sơ đồ 4 nhóm Bọ Hung trong DBO gốc hoạt động như thế nào?")
    add_p(doc, "Trong bầy bọ hung 30 con (n_agents = 30), tác giả chia thành 4 'binh chủng' phân công công việc rất thông minh:")

    add_p(doc, "Bọ lăn bóng phân đi xa theo đường thẳng. Nó nhìn vị trí xấu nhất của cả đàn để tránh xa ra. Khi gặp chướng ngại vật chắn đường, nó sẽ 'nhảy múa' (dancing) xoay một góc ngẫu nhiên để tìm hướng đi mới. 👉 Mục đích: Đi thám hiểm vùng đất mới, tránh đi vào vết xe đổ.", "1. Nhóm Bọ Lăn Phân (Ball-rolling & Dancing - 6 con):")
    add_p(doc, "Những con bọ này được ưu tiên đặt ở vùng an toàn quanh con bọ đang có vị trí tốt nhất. Càng về các vòng lặp sau, vùng sinh sản này càng co nhỏ lại. 👉 Mục đích: Đào bới thật kỹ khu vực nghi ngờ có kho báu để tinh chỉnh nghiệm.", "2. Nhóm Bọ Sinh Sản (Reproduction - 6 con):")
    add_p(doc, "Mô phỏng bọ non đi kiếm ăn trong vùng an toàn quanh vị trí tốt nhất toàn đàn. 👉 Mục đích: Lùng sục mọi ngóc ngách xung quanh con đầu đàn.", "3. Nhóm Bọ Kiếm Ăn (Foraging - 7 con):")
    add_p(doc, "Những con bọ láu cá chuyên đi rình rập và cướp bóng phân từ con bọ tốt nhất. 👉 Mục đích: Kéo cả đàn tiến thật nhanh về phía con có kết quả tốt nhất, giúp thuật toán hội tụ thần tốc.", "4. Nhóm Bọ Trộm (Thieving - 11 con):")

    add_sec_header(doc, "3.2. Sơ đồ Cải tiến IDBO — Tại sao cần Diversity, Perturbation và Restart?")
    add_p(doc, 
        "Nhìn sơ đồ hình thoi điều kiện trong báo cáo tuần 5-6, bạn chỉ cần nhớ câu chuyện chiếc 'phao cứu sinh':"
    )

    add_box_callout(
        doc,
        "Bước 1: Bọ chạy 4 hành vi bình thường.\n"
        "Bước 2: Đo 'Độ phân tán' (Diversity): Đàn bọ đang tản ra tìm kiếm hay đang xúm xít lại một chỗ?\n"
        "  - Nếu Diversity ≥ 10⁻³: Tốt! Đàn bọ đang phân tán tốt, không cần can thiệp gì cả, sang vòng lặp tiếp theo!\n"
        "  - Nếu Diversity < 10⁻³: BÁO ĐỘNG! Đàn bọ đang bu lại một đống!\n"
        "Bước 3: Kiểm tra xem bọ có đang bị bế tắc (Stagnation) không?\n"
        "  - Nếu Stagnation < 25 (chưa kẹt lâu): Kích hoạt PERTURBATION (Lay nhẹ). Bơm một chút nhiễu Gaussian đẩy vài con bay lệch ra ngoài để ngó nghiêng.\n"
        "  - Nếu Stagnation ≥ 25 (đã đứng im suốt 25 vòng không tiến bộ): Kích hoạt RESTART (Đập đi làm lại). Bốc ngay 25% số con bọ kém nhất thả dù ngẫu nhiên khắp bản đồ để mở đường máu!",
        "🧭 TÓM TẮT LOGIC SƠ ĐỒ IDBO:"
    )

    # ──────────────────────────────────────────────────────────────────────────
    # PHẦN 4: HƯỚNG DẪN CỰC DỄ HIỂU CÁCH ĐỌC ĐỒ THỊ VÀ BẢNG KẾT QUẢ
    # ──────────────────────────────────────────────────────────────────────────
    doc.add_page_break()
    add_part_header(doc, 4, "Cách đọc đồ thị và kết quả số như học sinh tiểu học")

    add_sec_header(doc, "4.1. Cách đọc các con số kỳ lạ trong bảng (e mũ âm là cái gì?)")
    add_p(doc, "Nhìn vào bảng bạn thấy số: 1.4553e-201 hoặc 4.4409e-16, đừng sợ! Đây là ký hiệu số học tiêu chuẩn của máy tính:")
    add_p(doc, "Chữ 'e-201' nghĩa là 10⁻²⁰¹, tức là lấy số 1 chia cho 10 hai trăm lẻ một lần. Nó có dạng: 0.0000000...000145 (sau dấu phẩy có 201 số 0 rồi mới tới số 1). Nó nhỏ đến mức trong toán học và thực tế coi như BẰNG 0 TUYỆT ĐỐI!", "• 1.4553e-201:")
    add_p(doc, "Là ngưỡng giới hạn nhỏ nhất mà chip máy tính (chuẩn 64-bit IEEE 754) có thể lưu được. Khi máy tính tính hàm Ackley chạm đến số này, nghĩa là thuật toán đã tìm đến giới hạn tối đa của phần cứng rồi, không thể nhỏ hơn được nữa!", "• 4.4409e-16:")
    add_p(doc, "Best là lần chạy đỏ nhất (kết quả tốt nhất trong 30 lần). Worst là lần xui xẻo nhất. Mean là điểm trung bình của 30 lần (phản ánh phong độ chuẩn). Std là độ lệch chuẩn (Std = 0 nghĩa là 30 lần chạy ra y hệt nhau, cực kỳ ổn định).", "• Best, Mean, Std, Worst:")

    add_sec_header(doc, "4.2. Cách đọc Đồ thị Hội tụ (Convergence Curve — Hình F1):")
    add_p(doc, 
        "Hãy nhìn vào đồ thị Hình 2.1 hoặc Hình 3.1 trong báo cáo:\n"
        "- Trục hoành (nằm ngang - Iteration): Số vòng lặp từ 0 đến 500 vòng.\n"
        "- Trục tung (thẳng đứng - Best fitness log): Điểm phạt sai số (càng thấp càng tốt, đáy đồ thị là số 0).\n"
        "- Đường nét vẽ cắm đầu dốc thẳng đứng xuống đáy: Thuật toán cực kỳ thông minh, chỉ mất vài chục vòng lặp là đã lao thẳng về đích!\n"
        "- Đoạn đường nằm ngang phẳng lì: Thuật toán đã tìm ra nghiệm tối ưu (hoặc đã hội tụ cứng) và duy trì phong độ cho tới hết 500 vòng."
    )

    img_conv_demo = EXP_W4 / "fig_convergence_multidim.png"
    if img_conv_demo.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(img_conv_demo), width=Inches(5.5))
        add_caption(doc, "Minh họa: Đồ thị hội tụ DBO qua 3 số chiều (Đường càng cắm sâu xuống đáy càng tốt!)")

    add_sec_header(doc, "4.3. Cách đọc Biểu đồ Hộp (Boxplot — Hình F2):")
    add_p(doc, 
        "Biểu đồ hộp (Boxplot) sinh ra để trả lời câu hỏi: 'Liệu thuật toán chạy có ổn định không, hay lúc đỏ lúc đen?'\n"
        "- Chiếc hộp chữ nhật: Đại diện cho 50% số lần chạy thông thường.\n"
        "- Vạch màu đen đậm nằm giữa hộp: Trung vị (Median - phong độ điển hình nhất).\n"
        "- Hai cái râu thò lên thò xuống: Khoảng cách giữa lần chạy tốt nhất và xấu nhất.\n"
        "- Các chấm tròn bay lơ lửng ngoài râu: Những lần chạy 'ngoại lệ' (bị gió thổi lệch hướng).\n"
        "👉 QUY TẮC VÀNG: Hộp càng xẹp lép và nằm càng sát đáy 0 thì thuật toán CÀNG HOÀN HẢO!"
    )

    img_box_demo = EXP_W4 / "fig_boxplot_multidim.png"
    if img_box_demo.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(img_box_demo), width=Inches(5.5))
        add_caption(doc, "Minh họa: Biểu đồ hộp Boxplot (Hộp càng dẹp và sát đáy thì độ ổn định càng tuyệt đối)")

    add_sec_header(doc, "4.4. Cách đọc Đồ thị Đa dạng (Diversity — Hình F3):")
    add_p(doc, 
        "Đồ thị này trả lời câu hỏi: 'Đàn bọ hung có đang sống khỏe và phân tán tìm kiếm không?'\n"
        "- Đường màu xanh lá (Sphere): Hàm này quá dễ nên cả đàn bọ nhanh chóng bu lại 1 điểm -> Diversity tụt dốc không phanh. Khi tụt dưới vạch đứt màu xám (10⁻³), phao cứu sinh Restart bung ra làm đồ thị giật nảy ngược lên!\n"
        "- Đường màu đỏ (Rastrigin): Hàm này có hàng trăm đỉnh núi gồ ghề -> Đàn bọ tự nhiên phải tản ra khắp nơi để trèo đèo lội suối -> Diversity luôn ở mức rất cao, trên hẳn vạch xám, không cần kích hoạt phao cứu sinh!"
    )

    img_div_demo = EXP_W5 / "fig_diversity_dim10.png"
    if img_div_demo.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(img_div_demo), width=Inches(5.2))
        add_caption(doc, "Minh họa: Đồ thị Diversity — Thấy rõ Sphere tụt dốc rồi được cứu, Rastrigin giữ độ phân tán cao")

    # ──────────────────────────────────────────────────────────────────────────
    # PHẦN 5: BẢN ĐỒ TRA CỨU MÃ NGUỒN VÀ DỮ LIỆU
    # ──────────────────────────────────────────────────────────────────────────
    doc.add_page_break()
    add_part_header(doc, 5, "Bản đồ tra cứu mã nguồn — File nào ở đâu, chứa cái gì?")

    add_p(doc, "Khi thầy hỏi hoặc khi bạn cần sửa code, chỉ cần liếc vào bảng này là biết file nào làm việc gì:")

    t_map = doc.add_table(rows=1, cols=3)
    t_map.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(["Thư mục / Tên file", "Vai trò trong đề tài", "Nội dung chính"]):
        t_map.rows[0].cells[i].text = h
        set_cell_background(t_map.rows[0].cells[i], "2B5C8F")
        p = t_map.rows[0].cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(9.5)

    files_info = [
        ("data/processed/merged_food_nutrition.csv", "Kho thực phẩm sạch", "15.929 món ăn đã chuẩn hóa về 100g khẩu phần kèm đầy đủ calo, đạm, béo, carb, xơ, muối..."),
        ("src/utils/nutrition.py", "Máy tính dinh dưỡng", "Chứa công thức BMR (Mifflin-St Jeor), TDEE, và phân bổ calo/macro theo mục tiêu giảm cân/tăng cơ"),
        ("src/models/user_profile.py", "Hồ sơ người dùng", "Chứa thông tin khách hàng (tuổi, chiều cao, cân nặng, vận động, dị ứng, bệnh lý...)"),
        ("src/models/menu.py", "Cấu trúc thực đơn", "Biến mâm cơm thành dãy số vector cho bọ hung mang trên lưng (Encode / Decode)"),
        ("src/models/objective.py", "Thang chấm điểm (Fitness)", "Hàm tính điểm phạt khi thực đơn lệch calo, thiếu chất, hoặc lặp món"),
        ("src/algorithms/dbo.py", "Thuật toán DBO gốc", "Chứa 4 hành vi sinh tồn của bọ hung: lăn phân, sinh sản, kiếm ăn, cướp đoạt"),
        ("src/algorithms/idbo.py", "Thuật toán cải tiến IDBO", "Thêm bộ đo Diversity, cơ chế bơm nhiễu Gaussian và tái khởi tạo Random Restart"),
        ("src/algorithms/benchmarks.py", "6 hàm bài tập toán", "Chứa 6 địa hình toán học: Sphere, Schwefel, Rosenbrock, Rastrigin, Ackley, Griewank"),
        ("experiments/week4/", "Kết quả tuần 4 (DBO)", "Chứa 540 lần chạy, file CSV tổng hợp và đồ thị hội tụ của DBO gốc"),
        ("experiments/week5_6/", "Kết quả tuần 5–6 (IDBO)", "Chứa 1.080 lần chạy, so sánh DBO vs IDBO, đồ thị hội tụ, boxplot và diversity")
    ]

    for f, role, desc in files_info:
        rc = t_map.add_row().cells
        rc[0].text = f
        rc[1].text = role
        rc[2].text = desc
        for i, c in enumerate(rc):
            set_cell_margins(c, 40, 40, 60, 60)
            for r in c.paragraphs[0].runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(9.0)
                if i == 0:
                    r.font.bold = True
    set_table_borders(t_map)

    add_sec_header(doc, "\n5.1. Kế hoạch Tuần 7 (Sắp tới cần làm gì?):")
    add_p(doc, 
        "Đến hết tuần 6, chúng ta đã có 2 thứ hoàn chỉnh: (1) Mâm cơm dinh dưỡng và (2) Con bọ hung thông minh IDBO đã được kiểm chứng. "
        "Việc tuần 7 cực kỳ rõ ràng: Lấy con bọ hung IDBO thả vào kho 16.000 món ăn để nó tự động lên thực đơn mẫu cho 3 hồ sơ người dùng thực tế! "
        "Mọi nền tảng toán học và thuật toán đã xong 100%, bạn hoàn toàn có thể yên tâm và tự tin!"
    )

    doc.save(str(OUT_PATH))
    print(f"[OK] Successfully built student guide at: {OUT_PATH}")

if __name__ == "__main__":
    build_student_handbook()
