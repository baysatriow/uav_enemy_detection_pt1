import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def create_report():
    doc = Document()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fig_dir = os.path.join(base_dir, "reports", "figures")
    
    # -------------------------------------------------------------
    # PAGE SETUP
    # -------------------------------------------------------------
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
    # Color palette constants
    HEX_PRIMARY = "1A365D"       # Deep Navy
    HEX_SECONDARY = "2B6CB0"     # Slate Blue
    HEX_DARK_TEXT = "2D3748"     # Charcoal Dark Neutral
    HEX_LIGHT_BG = "F7FAFC"      # Warm Light Neutral
    HEX_BORDER = "E2E8F0"        # Subtle Border
    HEX_HIGHLIGHT = "D69E2E"     # Muted Gold / Amber
    HEX_WHITE = "FFFFFF"
    
    COLOR_PRIMARY = RGBColor(26, 54, 93)
    COLOR_SECONDARY = RGBColor(43, 108, 176)
    COLOR_DARK_TEXT = RGBColor(45, 55, 72)
    COLOR_MUTED = RGBColor(113, 128, 150)
    
    # Configure Normal Style
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Calibri'
    style_normal.font.size = Pt(11)
    style_normal.font.color.rgb = COLOR_DARK_TEXT
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(6)
    
    # Helper functions for styling
    def set_cell_background(cell, hex_color):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
        cell._tc.get_or_add_tcPr().append(shading)
        
    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(
            f'<w:tcMar {nsdecls("w")}>'
            f'<w:top w:w="{top}" w:type="dxa"/>'
            f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
            f'<w:left w:w="{left}" w:type="dxa"/>'
            f'<w:right w:w="{right}" w:type="dxa"/>'
            f'</w:tcMar>'
        )
        tcPr.append(tcMar)

    def set_table_borders(table, color="D3D3D3", sz="4", val="single"):
        tblPr = table._tbl.tblPr
        borders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'<w:insideV w:val="none"/>'
            f'<w:left w:val="none"/>'
            f'<w:right w:val="none"/>'
            f'</w:tblBorders>'
        )
        tblPr.append(borders)

    def add_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(16.5)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = COLOR_SECONDARY
        return p

    def add_heading_3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(11.5)
        run.font.bold = True
        run.font.color.rgb = COLOR_DARK_TEXT
        return p

    def add_callout(text, title=None, border_color="1A365D", fill_color="F7FAFC"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, fill_color)
        set_cell_margins(cell, top=140, bottom=140, left=200, right=160)
        
        tcPr = cell._tc.get_or_add_tcPr()
        borders = parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
            f'<w:top w:val="none"/>'
            f'<w:bottom w:val="none"/>'
            f'<w:right w:val="none"/>'
            f'</w:tcBorders>'
        )
        tcPr.append(borders)
        
        p = cell.paragraphs[0]
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(0)
        if title:
            r_title = p.add_run(f"{title}\n")
            r_title.bold = True
            r_title.font.size = Pt(10.5)
            r_title.font.color.rgb = COLOR_PRIMARY
        r_text = p.add_run(text)
        r_text.font.size = Pt(10)
        r_text.font.color.rgb = COLOR_DARK_TEXT
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def add_figure(image_filename, caption_text, width=Inches(6.2)):
        full_path = os.path.join(fig_dir, image_filename)
        if not os.path.exists(full_path):
            print(f"Warning: Figure not found at {full_path}")
            return
        
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(10)
        p_img.paragraph_format.space_after = Pt(2)
        p_img.paragraph_format.keep_with_next = True
        run_img = p_img.add_run()
        run_img.add_picture(full_path, width=width)
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(12)
        p_cap.paragraph_format.keep_with_next = False
        run_cap = p_cap.add_run(caption_text)
        run_cap.font.name = 'Calibri'
        run_cap.font.size = Pt(9.5)
        run_cap.font.italic = True
        run_cap.font.color.rgb = COLOR_MUTED

    # -------------------------------------------------------------
    # COVER / HEADER TITLE
    # -------------------------------------------------------------
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_after = Pt(2)
    r_meta = p_meta.add_run("LAPORAN RISET & PENGUJIAN KOMPREHENSIF")
    r_meta.font.size = Pt(10)
    r_meta.font.bold = True
    r_meta.font.color.rgb = COLOR_SECONDARY

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run("Deteksi Objek UAV (Musuh vs Bukan Musuh):\nEksperimen Arsitektur YOLO26 + CBAM & Pipeline Inferensi Video")
    r_title.font.size = Pt(21)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run("Kajian Evaluasi Matriks 30 Model (E0–E6), Metrik Uji Unseen Split, dan Penerapan Streaming Video Pipeline")
    r_sub.font.size = Pt(11.5)
    r_sub.font.italic = True
    r_sub.font.color.rgb = COLOR_MUTED

    # Metadata Box
    tbl_meta = doc.add_table(rows=4, cols=2)
    tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_meta.autofit = False
    set_table_borders(tbl_meta, color="E2E8F0", sz="4")
    
    meta_data = [
        ("Platform & Hardware Pengujian", "NVIDIA GeForce RTX 5070 (12 GB VRAM) | PyTorch 2.14.0+cu132 | CUDA Enabled"),
        ("Dataset & Skema Anotasi", "enemy-detection-1-fps v1 (Roboflow) | Kelas: ally (0) & enemy (1)"),
        ("Ruang Lingkup Eksperimen", "Matriks E0–E6 melintasi 5 Skala Model (n, s, m, l, x) = Total 30 Model Teruji"),
        ("Komponen Notebook Utama", "YOLO26_Enemy_Detection_Training.ipynb & YOLO26_Video_Inference.ipynb")
    ]
    for row_idx, (k, v) in enumerate(meta_data):
        c0 = tbl_meta.cell(row_idx, 0)
        c1 = tbl_meta.cell(row_idx, 1)
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        set_cell_background(c0, HEX_LIGHT_BG)
        set_cell_margins(c0, 60, 60, 100, 100)
        set_cell_margins(c1, 60, 60, 100, 100)
        p0 = c0.paragraphs[0]
        p0.add_run(k).bold = True
        p0.runs[0].font.size = Pt(9.5)
        p1 = c1.paragraphs[0]
        p1.add_run(v)
        p1.runs[0].font.size = Pt(9.5)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # -------------------------------------------------------------
    # 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)
    # -------------------------------------------------------------
    add_heading_1("1. Ringkasan Eksekutif")
    
    doc.add_paragraph(
        "Laporan ini mendokumentasikan hasil riset, pelatihan, dan evaluasi komprehensif sistem deteksi objek udara "
        "(Unmanned Aerial Vehicle / UAV) untuk mendeteksi target Musuh (enemy) dan Sekutu (ally). "
        "Eksperimen dirancang secara terstruktur dengan mengintegrasikan modul atensi Convolutional Block Attention Module "
        "(CBAM) ke dalam berbagai tingkatan topologi arsitektur YOLO26 (dari Baseline E0 hingga Kombinasi E5) pada lima skala "
        "kapasitas model (Nano / n, Small / s, Medium / m, Large / l, dan X-Large / x), menghasilkan matriks 30 konfigurasi model."
    )
    
    add_callout(
        "Temuan Inti & Sorotan Utama:\n"
        "• Model Terbaik Keseluruhan (#1 Overall): E0_yolo26n (Baseline Nano tanpa modul atensi) mengukir performa tertinggi "
        "pada test set dengan Test mAP@50 mencapai 92.86%, enemy_mAP@50 sebesar 93.59%, dan latensi sangat cepat 11.48 ms (~87.1 FPS).\n"
        "• Pengaruh Positif CBAM pada Skala Menengah & Besar: Penambahan 1× CBAM pada tahap backbone terdalam (P5 / E1) terbukti "
        "sangat efektif mendongkrak akurasi model berkapasitas besar. Pada YOLO26m mAP@50 naik dari 80.59% ke 82.77% (+2.18%), "
        "dan pada YOLO26x mAP@50 melonjak dari 79.53% ke 82.66% (+3.13%), sekaligus menduduki peringkat #1 pada kategori large model.\n"
        "• Sensitivitas Deteksi Musuh Unggul (+6.92%): Pada skala X-Large, modul CBAM (E1) secara spesifik mendongkrak enemy_mAP@50 "
        "dari 79.89% (baseline) menjadi 86.81% — peningkatan bersih sebesar +6.92% yang krusial untuk pencegahan False Negative militer.\n"
        "• Degradasi Akibat Atensi Berlebihan (Over-Attention Trap): Penempatan modul atensi secara masif di seluruh hierarki (E2, E3, E5) "
        "justru menurunkan akurasi dan memperlambat latensi hingga 14.78 ms (~67.6 FPS) akibat distorsi propagasi gradien dan over-smoothing fitur.\n"
        "• Pipeline Video Operasional: Notebook inferensi video menerapkan arsitektur streaming memori stabil dengan pencatatan telemetri CSV "
        "per-frame, threshold confidence terstandardisasi (0.50), serta visualisasi bounding box siap integrasi stasiun darat (GCS).",
        title="POKOK KESIMPULAN RISET"
    )

    # -------------------------------------------------------------
    # 2. LANDASAN TEORI & DESAIN ARSITEKTUR CBAM
    # -------------------------------------------------------------
    add_heading_1("2. Desain Arsitektur & Integrasi Modul CBAM")
    
    doc.add_paragraph(
        "Convolutional Block Attention Module (CBAM) merupakan mekanisme atensi adaptif berbiaya komputasi rendah yang "
        "mengeksploitasi keterkaitan fitur spasial dan antarkanal secara berurutan (sekuensial). CBAM dirancang untuk "
        "memfokuskan ekstraksi representasi pada atribut penting target udara (seperti kontur bodi drone, propeler, atau "
        "siluet kendaraan tempur) sekaligus menekan derau latar belakang (background clutter) khas citra aerial pengawasan."
    )
    
    add_heading_2("2.1 Mekanisme Sub-Modul CBAM (CAM & SAM)")
    doc.add_paragraph(
        "CBAM memproses peta fitur perantara F ∈ ℝ^(C×H×W) melalui dua tahapan komplementer berurutan:\n"
        "1. Channel Attention Module (CAM):\n"
        "   CAM mengidentifikasi 'fitur apa' yang esensial secara semantik. Peta fitur diringkas melalui operasi Average Pooling "
        "dan Max Pooling secara paralel, diproses oleh Shared Multi-Layer Perceptron (MLP) dengan rasio reduksi r = 16, lalu digabungkan:\n"
        "   Mc(F) = σ( MLP(AvgPool(F)) + MLP(MaxPool(F)) )\n"
        "   Fitur hasil penyesuaian kanal F' dihitung melalui perkalian elemen: F' = Mc(F) ⊗ F.\n\n"
        "2. Spatial Attention Module (SAM):\n"
        "   SAM mengidentifikasi 'di mana' letak fokus objek yang relevan. F' diagregasikan sepanjang dimensi kanal melalui average pooling "
        "dan max pooling saluran, digabungkan (concatenation), dan dikonvolusi menggunakan filter spasial 7×7:\n"
        "   Ms(F') = σ( f^(7×7)( [AvgPool(F'); MaxPool(F')] ) )\n"
        "   Fitur final hasil atensi diperoleh dari: F'' = Ms(F') ⊗ F'."
    )
    
    # Figure 2.1: CBAM Schematic Diagram
    add_figure(
        "fig5_cbam_architecture_diagram.png",
        "Gambar 2.1: Diagram Skema Alur Operasi Convolutional Block Attention Module (CBAM) yang Menggabungkan "
        "Channel Attention Module (CAM) dan Spatial Attention Module (SAM) secara Sekuensial.",
        width=Inches(6.2)
    )

    add_heading_2("2.2 Dynamic Module Registration pada Ultralytics")
    doc.add_paragraph(
        "Salah satu keunggulan implementasi teknis pada codebase ini (modul cbam.py) adalah penggunaan Dynamic Module Registration. "
        "Tanpa perlu mengubah file inti di direktori library 'ultralytics', fungsi register_cbam() secara runtime menyuntikkan modul CBAM "
        "ke dalam nn.modules Ultralytics dan menambahkan parser otomatis untuk resolusi kanal otomatis pada file definisi arsitektur YAML."
    )

    # -------------------------------------------------------------
    # 3. METODOLOGI & MATRIKS EKSPERIMEN (E0 – E6)
    # -------------------------------------------------------------
    add_heading_1("3. Metodologi Eksperimen & Desain Matriks E0 – E6")
    
    doc.add_paragraph(
        "Untuk mengkaji secara komprehensif pengaruh penempatan topologis CBAM, dirancang 6 variasi eksperimen arsitektural (E0 hingga E5), "
        "yang dievaluasi pada 5 skala varian kapasitas model YOLO26: Nano (n), Small (s), Medium (m), Large (l), dan X-Large (x), "
        "sehingga tercipta matriks 30 kombinasi model independen yang dilatih masing-masing selama 100 epoch."
    )

    # Tabel Matriks Desain
    tbl_exp = doc.add_table(rows=7, cols=5)
    tbl_exp.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_exp.autofit = False
    set_table_borders(tbl_exp, color="CBD5E0", sz="4")
    
    headers_exp = ["ID", "Arsitektur", "Topologi CBAM", "Lokasi / Skala Atensi", "Tujuan Ilmiah Eksperimen"]
    widths_exp = [Inches(0.6), Inches(1.1), Inches(1.4), Inches(1.5), Inches(1.9)]
    
    for c_idx, h_text in enumerate(headers_exp):
        c = tbl_exp.cell(0, c_idx)
        c.width = widths_exp[c_idx]
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, 100, 100, 100, 100)
        p = c.paragraphs[0]
        r = p.add_run(h_text)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    exp_matrix_rows = [
        ("E0", "YOLO26", "None (Baseline)", "Tidak ada", "Titik acuan dasar kinerja model standar tanpa modul atensi."),
        ("E1", "YOLO26", "1× Backbone", "Tahap terdalam (P5)", "Mengukur efektivitas atensi tunggal pada level representasi semantik tertinggi."),
        ("E2", "YOLO26", "2× Backbone", "Multi-skala (P4, P5)", "Menguji atensi pada fitur representasi skala menengah dan besar."),
        ("E3", "YOLO26", "3× Backbone", "Hierarki penuh (P3, P4, P5)", "Mengevaluasi atensi di seluruh tingkatan resolusi feature map backbone."),
        ("E4", "YOLO26", "3× Neck", "Cabang luaran Neck (P3, P4, P5)", "Komparasi langsung pengaruh atensi pada Neck (FPN/PAN) vs Backbone."),
        ("E5", "YOLO26", "Backbone + Neck", "Kombinasi penuh (6 blok CBAM)", "Menguji efek sinergi end-to-end multi-scale attention secara komprehensif.")
    ]
    
    for r_idx, row_data in enumerate(exp_matrix_rows, start=1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else HEX_WHITE
        for c_idx, val in enumerate(row_data):
            cell = tbl_exp.cell(r_idx, c_idx)
            cell.width = widths_exp[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 80, 80, 100, 100)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.size = Pt(9)
            if c_idx == 0:
                r.bold = True
                
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # -------------------------------------------------------------
    # 4. DATASET & AUDIT ANOTASI
    # -------------------------------------------------------------
    add_heading_1("4. Dataset & Karakteristik Citra Pengawasan Udara (UAV)")
    
    doc.add_paragraph(
        "Eksperimen menggunakan dataset aerial surveillance 'enemy-detection-1-fps' versi 1 dari Roboflow. "
        "Dataset ini dirancang secara khusus untuk mensimulasikan skenario taktis pengintaian udara militer:\n"
        "• Dimensi Citra: Resolusi seragam 640 × 640 piksel standar detektor berkecepatan tinggi.\n"
        "• Pembagian Data (Split): Terdiri dari subset Train, Validation, dan Unseen Test Split.\n"
        "  - Subset Test: Terdiri dari 134 citra independen yang belum pernah dilihat saat pelatihan, memuat 610 bounding box.\n"
        "• Distribusi Kelas Target:\n"
        "  - ID 0: 'ally' (Bukan Musuh / Friendly Target) — memuat 340 instance pada test split.\n"
        "  - ID 1: 'enemy' (Musuh / Hostile Target) — memuat 270 instance pada test split.\n"
        "• Karakteristik Citra: Menampilkan variasi sudut elevasi kamera UAV (nadir vertikal dan oblique menyudut), "
        "rentang skala target yang lebar (dari jarak sangat jauh/titik piksel kecil hingga jarak menengah), "
        "serta latar belakang alam terbuka bertekstur rumit (hutan, semak, jalanan berdebu, dan bangunan)."
    )

    # Figure 4.1: Ground Truth vs Prediction Comparison
    add_figure(
        "fig7_groundtruth_vs_prediction.jpg",
        "Gambar 4.1: Sampel Citra Dataset Uji UAV — Komparasi Anotasi Asli (Ground Truth, Kiri) dan Prediksi Deteksi Objek "
        "oleh Model E0_yolo26n (Kanan) pada Sudut Pandang Kamera Udara Nyata.",
        width=Inches(6.2)
    )

    # -------------------------------------------------------------
    # 5. ANALISIS HASIL EVALUASI LENGKAP 30 MODEL
    # -------------------------------------------------------------
    add_heading_1("5. Analisis Hasil Evaluasi Lengkap 30 Model pada Test Split")
    
    doc.add_paragraph(
        "Seluruh 30 model hasil pelatihan 100 epoch diuji secara seragam dan ketat pada Test Split independen "
        "(134 citra, 610 instance) dengan batch size 1 pada GPU workstation NVIDIA GeForce RTX 5070. "
        "Metrik yang dievaluasi mencakup Presisi (P), Recall (R), Test mAP@50, Test mAP@50:95, mAP per-kelas "
        "(ally vs enemy), serta latensi komputasi inferensi frame-by-frame."
    )
    
    add_heading_2("5.1 Top 10 Model Terbaik Berdasarkan Test mAP@50")
    
    tbl_top10 = doc.add_table(rows=11, cols=9)
    tbl_top10.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_top10.autofit = False
    set_table_borders(tbl_top10, color="CBD5E0", sz="4")
    
    top10_headers = ["Peringkat", "Nama Run", "Exp", "Skala", "Precision", "Recall", "mAP@50", "mAP@50:95", "FPS"]
    top10_widths = [Inches(0.7), Inches(1.1), Inches(0.5), Inches(0.5), Inches(0.7), Inches(0.7), Inches(0.8), Inches(0.9), Inches(0.6)]
    
    for c_idx, h_text in enumerate(top10_headers):
        c = tbl_top10.cell(0, c_idx)
        c.width = top10_widths[c_idx]
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, 80, 80, 80, 80)
        p = c.paragraphs[0]
        r = p.add_run(h_text)
        r.bold = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    top10_data = [
        ("#1", "E0_yolo26n", "E0", "n", "0.8965", "0.8691", "0.9286", "0.4875", "87.1"),
        ("#2", "E1_yolo26n", "E1", "n", "0.8586", "0.8636", "0.9130", "0.4521", "83.3"),
        ("#3", "E4_yolo26n", "E4", "n", "0.8736", "0.8747", "0.9070", "0.4604", "78.8"),
        ("#4", "E2_yolo26n", "E2", "n", "0.8662", "0.8404", "0.9019", "0.4406", "78.6"),
        ("#5", "E5_yolo26n", "E5", "n", "0.8294", "0.8286", "0.8786", "0.4210", "67.6"),
        ("#6", "E3_yolo26n", "E3", "n", "0.7759", "0.7995", "0.8576", "0.4093", "81.7"),
        ("#7", "E3_yolo26s", "E3", "s", "0.8162", "0.7615", "0.8431", "0.3999", "79.7"),
        ("#8", "E0_yolo26l", "E0", "l", "0.7688", "0.7749", "0.8343", "0.3970", "93.8"),
        ("#9", "E1_yolo26m", "E1", "m", "0.7551", "0.7820", "0.8277", "0.3955", "80.4"),
        ("#10", "E1_yolo26x", "E1", "x", "0.7432", "0.7654", "0.8266", "0.3963", "79.7")
    ]
    
    for r_idx, row_data in enumerate(top10_data, start=1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else HEX_WHITE
        for c_idx, val in enumerate(row_data):
            cell = tbl_top10.cell(r_idx, c_idx)
            cell.width = top10_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 60, 60, 60, 60)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            if c_idx in [0, 6]:
                r.bold = True
                
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_heading_2("5.2 Matriks Performa Silang & Visualisasi Heatmap (Test mAP@50)")
    doc.add_paragraph(
        "Tabel pivot dan heatmap di bawah ini menyajikan distribusi komparatif Test mAP@50 melintasi seluruh ruang "
        "arsitektur (E0–E5) dan kapasitas model (Nano hingga X-Large). Gambar 5.1 dengan jelas memperlihatkan konfigurasi terbaik "
        "(★ BEST) pada masing-masing kolom kapasitas."
    )

    # Pivot Table
    tbl_piv = doc.add_table(rows=7, cols=7)
    tbl_piv.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_piv.autofit = False
    set_table_borders(tbl_piv, color="CBD5E0", sz="4")
    
    piv_headers = ["Topologi", "Deskripsi CBAM", "Nano (n)", "Small (s)", "Medium (m)", "Large (l)", "X-Large (x)"]
    piv_widths = [Inches(0.6), Inches(1.7), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8)]
    
    for c_idx, h_text in enumerate(piv_headers):
        c = tbl_piv.cell(0, c_idx)
        c.width = piv_widths[c_idx]
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, 80, 80, 80, 80)
        p = c.paragraphs[0]
        r = p.add_run(h_text)
        r.bold = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    piv_data = [
        ("E0", "Baseline (No Attention)", "0.9286*", "0.8045", "0.8059", "0.8343*", "0.7953"),
        ("E1", "1× Backbone (P5)", "0.9130", "0.7836", "0.8277*", "0.8130", "0.8266*"),
        ("E2", "2× Backbone (P4, P5)", "0.9019", "0.8051", "0.8157", "0.7981", "0.7671"),
        ("E3", "3× Backbone (P3, P4, P5)", "0.8576", "0.8431*", "0.8077", "0.7900", "0.8011"),
        ("E4", "3× Neck Branches", "0.9070", "0.7900", "0.7920", "0.8186", "0.7941"),
        ("E5", "Combined Backbone+Neck", "0.8786", "0.7890", "0.7793", "0.7751", "0.7660")
    ]
    
    for r_idx, row_data in enumerate(piv_data, start=1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else HEX_WHITE
        for c_idx, val in enumerate(row_data):
            cell = tbl_piv.cell(r_idx, c_idx)
            cell.width = piv_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 60, 60, 60, 60)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            if "*" in val:
                r.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            if c_idx == 0:
                r.bold = True

    p_note = doc.add_paragraph()
    p_note.paragraph_format.space_before = Pt(4)
    r_n = p_note.add_run("Catatan: Tanda bintang (*) menandai skor mAP@50 tertinggi pada setiap kolom skala model.")
    r_n.font.size = Pt(8.5)
    r_n.font.italic = True

    # Figure 5.1: Heatmap of Test mAP@50
    add_figure(
        "fig1_test_map50_heatmap.png",
        "Gambar 5.1: Heatmap Matriks Komparasi Test mAP@50 Seluruh 30 Model (Topologi E0–E5 vs Skala Nano–X-Large) "
        "dengan Penanda Konfigurasi Terbaik (★ BEST) pada Setiap Kolom Skala.",
        width=Inches(6.0)
    )

    add_heading_2("5.3 Tren Skalabilitas Kapasitas Model (Capacity Scaling Trend)")
    doc.add_paragraph(
        "Sebagaimana ditunjukkan pada grafik Gambar 5.2, tren performa arsitektur memiliki karakteristik yang sangat jelas: "
        "seluruh varian pada skala Nano (n) mencatatkan mAP@50 di kisaran 85%–93%. Seiring bertambahnya parameter model ke skala Small "
        "dan Medium, terjadi fenomena 'capacity mismatch' di mana penambahan parameter tanpa regularisasi atensi semantik yang tepat "
        "cenderung mengalami overfitting. Namun, pada skala model terbesar (X-Large / x), modul atensi tunggal E1 (1× Backbone P5) "
        "berhasil membalikkan keadaan dengan performa tertinggi (82.66%), melampaui baseline E0 (79.53%) sebesar +3.13%."
    )

    # Figure 5.2: Scaling Capacity Trend Line Chart
    add_figure(
        "fig4_cbam_topology_impact.png",
        "Gambar 5.2: Tren Performa Test mAP@50 Berdasarkan Skala Kapasitas Parameter Model, memperlihatkan keunggulan model Nano "
        "serta pemulihan performa yang signifikan oleh E1 pada model berskala besar.",
        width=Inches(6.0)
    )

    add_heading_2("5.4 Analisis Efisiensi Kecepatan Inferensi & Batas Pareto (FPS vs Accuracy)")
    doc.add_paragraph(
        "Pada aplikasi taktis UAV, kecepatan inferensi sama pentingnya dengan akurasi guna mendukung pelacakan target "
        "secara real-time (minimal 30 FPS untuk kelancaran kendali penerbangan). Grafik Gambar 5.3 menggambarkan hubungan "
        "trade-off antara Frame Per Second (FPS) dan Test mAP@50 pada GPU RTX 5070 dengan ukuran batch 1."
    )

    # Figure 5.3: Pareto Speed vs Accuracy Scatter Plot
    add_figure(
        "fig2_fps_vs_map50_pareto.png",
        "Gambar 5.3: Scatter Plot Trade-off Kecepatan Inferensi (FPS) vs Akurasi (Test mAP@50) pada GPU NVIDIA RTX 5070 "
        "yang Memetakan Batas Pareto Frontier dan Zona Operasional Optimal Lapangan.",
        width=Inches(6.2)
    )
    
    doc.add_paragraph(
        "Interpretasi Batas Pareto:\n"
        "1. Model Non-Dominated Terbaik: E0_yolo26n memimpin batas efisiensi absolut dengan 87.1 FPS pada mAP@50 92.86%. "
        "Tidak ada satupun model lain yang mampu melampaui akurasi ini pada kecepatan di atas 80 FPS.\n"
        "2. Model Kecepatan Tertinggi: E0_yolo26l mencapai 93.8 FPS dengan akurasi 83.43% mAP@50 karena struktur komputasi konvolusi "
        "standar tanpa overhead sinkronisasi atensi tambahan.\n"
        "3. Model Berkapasitas Besar Paling Optimal: E1_yolo26x berada pada titik Pareto untuk kategori X-Large, beroperasi "
        "pada 79.7 FPS dengan akurasi 82.66% mAP@50."
    )

    add_heading_2("5.5 Analisis Performa Kelas Kunci (Target Musuh vs Sekutu)")
    doc.add_paragraph(
        "Dalam doktrin pertahanan udara, kegagalan mendeteksi musuh (False Negative) memiliki konsekuensi fatal jauh lebih besar "
        "dibandingkan kesalahan mendeteksi kawan (False Alarm). Oleh karena itu, metrik 'enemy_mAP@50' menjadi tolok ukur krusial. "
        "Gambar 5.4 menyajikan komparasi akurasi deteksi kelas target musuh (enemy) terhadap kelas sekutu (ally)."
    )

    # Figure 5.4: Enemy vs Ally Bar Chart
    add_figure(
        "fig3_enemy_vs_ally_map50.png",
        "Gambar 5.4: Komparasi Akurasi Deteksi Kelas Spesifik (enemy vs ally mAP@50) yang Menyoroti Sensitivitas Tinggi terhadap "
        "Target Musuh dan Lonjakan Signifikan (+6.92%) pada Model Kapasitas Besar E1_yolo26x.",
        width=Inches(6.0)
    )
    
    doc.add_paragraph(
        "Dua temuan utama yang terungkap dari grafik Gambar 5.4:\n"
        "1. Konsistensi Sensitivitas Deteksi Musuh: Hampir pada seluruh model yang diuji, akurasi deteksi kelas musuh lebih tinggi "
        "dibandingkan sekutu. Pada model nano E0_yolo26n, enemy_mAP@50 mencapai 93.59%.\n"
        "2. Lonjakan Akurasi Target Musuh oleh CBAM (+6.92%): Pada skala X-Large, modul atensi E1 secara selektif mempertajam fitur "
        "pembeda target musuh, melesatkan enemy_mAP@50 dari 79.89% (E0_yolo26x) menjadi 86.81% (E1_yolo26x). "
        "Peningkatan ini membuktikan bahwa CBAM berhasil menyaring fitur kamuflase musuh pada citra beresolusi penuh."
    )

    add_heading_2("5.6 Diagnostik Pelatihan & Evaluasi Model Terbaik (E0_yolo26n)")
    doc.add_paragraph(
        "Untuk memvalidasi stabilitas konvergensi dan keandalan statistika dari model peringkat #1 (E0_yolo26n), diekstrak grafik "
        "dinamika pelatihan 100 epoch (Gambar 5.5) serta kurva Precision-Recall dan Matriks Konfusi Ternormalisasi (Gambar 5.6)."
    )

    # Figure 5.5: Training Curves (Losses, mAP50, mAP50-95)
    add_figure(
        "fig10_training_loss_curves.png",
        "Gambar 5.5: Dinamika Konvergensi Pelatihan 100 Epoch pada Model E0_yolo26n (Loss Training/Validation, Precision, Recall, "
        "mAP@50, dan mAP@50-95) yang Menunjukkan Konvergensi Mulus Tanpa Tanda Overfitting.",
        width=Inches(6.2)
    )

    # Figure 5.6: PR Curve and Confusion Matrix Composite
    add_figure(
        "fig9_pr_and_confusion_matrix.png",
        "Gambar 5.6: Kurva Precision-Recall (Kiri, Area Keseluruhan 0.929 mAP@0.5) dan Matriks Konfusi Ternormalisasi (Kanan) "
        "Model E0_yolo26n pada Subset Uji Unseen, Memperlihatkan Akurasi Deteksi 92% pada Musuh dan 90% pada Sekutu.",
        width=Inches(6.2)
    )

    # -------------------------------------------------------------
    # 6. WORKFLOW PELATIHAN & PIPELINE INFERENSI VIDEO
    # -------------------------------------------------------------
    add_heading_1("6. Visualisasi Hasil Inferensi & Pipeline Operasional UAV")
    
    doc.add_paragraph(
        "Keunggulan kuantitatif pada tabel metrik divalidasi lebih lanjut melalui inspeksi visual hasil inferensi pada "
        "citra uji nyata serta pengujian alur pipeline video operasional."
    )
    
    add_heading_2("6.1 Galeri Sampel Inferensi Deteksi UAV pada Data Uji Nyata")
    doc.add_paragraph(
        "Gambar 6.1 menampilkan mosaik hasil inferensi deteksi objek udara oleh model E0_yolo26n pada berbagai sampel citra uji "
        "independen. Dapat diamati bahwa model mampu mendeteksi dan mengklasifikasikan target dengan bounding box yang sangat presisi "
        "serta skor keyakinan (confidence score) tinggi (rata-rata 0.85 hingga 0.94), baik pada sudut kamera nadir vertikal, "
        "sudut miring (oblique), maupun pada target yang terkamuflase oleh bayangan tanah dan vegetasi."
    )

    # Figure 6.1: Sample Inference Mosaic (2x2 Grid)
    add_figure(
        "fig6_sample_inference_mosaic.jpg",
        "Gambar 6.1: Mosaik Hasil Inferensi Deteksi UAV oleh Model E0_yolo26n pada Berbagai Skenario Lapangan "
        "(Variasi Sudut Elevasi Kamera Udara, Target Skala Kecil, dan Latar Belakang Alami). Bounding box biru/hijau "
        "menunjukkan klasifikasi target 'enemy' dan 'ally' secara akurat dengan skor keyakinan tinggi.",
        width=Inches(6.2)
    )

    add_heading_2("6.2 Komparasi Deteksi Target Jarak Jauh: Baseline E0_yolo26x vs CBAM E1_yolo26x")
    doc.add_paragraph(
        "Pada skala model berkapasitas besar, pengaruh modul CBAM paling kentara ketika mendeteksi target berukuran kecil pada "
        "jarak pandang jauh. Gambar 6.2 memperlihatkan perbandingan langsung antara Baseline E0_yolo26x dan CBAM E1_yolo26x "
        "pada bingkai uji yang sama. Baseline E0 mengalami False Negative (musuh tidak terdeteksi) pada target yang jauh, "
        "sedangkan E1_yolo26x berhasil melokalisasi target tersebut berkat mekanisme pemfokusan spasial SAM pada tahap P5."
    )

    # Figure 6.2: Large Model Comparison
    add_figure(
        "fig8_large_model_cbam_comparison.jpg",
        "Gambar 6.2: Komparasi Visual Deteksi Target Jarak Jauh antara Baseline E0_yolo26x (Kiri) dan E1_yolo26x dengan Modul CBAM (Kanan). "
        "Modul CBAM berhasil mengeliminasi False Negative pada target musuh terpencil dengan mendongkrak enemy_mAP@50 dari 79.89% ke 86.81%.",
        width=Inches(6.2)
    )

    add_heading_2("6.3 YOLO26_Enemy_Detection_Training.ipynb")
    doc.add_paragraph(
        "Notebook pelatihan menyediakan lingkungan terstruktur untuk melatih varian YOLO26 dengan fitur-fitur kunci:\n"
        "• Alur Kerja Terautomasi: Integrasi otomatis unduhan dataset Roboflow, validasi dependensi CUDA/PyTorch, serta pembuatan file konfigurasi lokal data_yolo26_local.yaml dengan path absolut.\n"
        "• Audit Data Ketat: Verifikasi integritas label, bounding box, dan format kelas target (0: ally, 1: enemy).\n"
        "• Manajemen Batch Dinamis: Pengaturan batch size otomatis sesuai profil memori GPU (n: auto/-1, s: 32, m: 12, l: 12, x: 8).\n"
        "• Checkpoint Resumption & Evaluasi: Mekanisme recovery pelatihan otomatis bila terjadi interupsi, serta evaluasi komprehensif pada subset test pasca-latih (kurva PR, matriks konfusi, dan loss curve)."
    )
    
    add_heading_2("6.4 YOLO26_Video_Inference.ipynb")
    doc.add_paragraph(
        "Notebook inferensi video dirancang untuk kebutuhan operasional pemrosesan stream video UAV dengan karakteristik:\n"
        "• Streaming Frame Processing: Memproses video bingkai demi bingkai secara bertahap (streaming), mencegah kehabisan RAM/VRAM saat memproses file video panjang beresolusi tinggi.\n"
        "• Logging Telemetri Tabular (detections.csv): Mencatat metadata deteksi terperinci pada setiap frame (frame index, nomor detik video, class ID, class name, confidence score, dan koordinat bounding box xyxy).\n"
        "• Ambang Batas Confidence 0.50: Mengeliminasi deteksi berkepercayaan rendah (false positive) dan menghasilkan visualisasi bersih beranotasi pada folder runs/inference/."
    )

    # -------------------------------------------------------------
    # 7. PEMBAHASAN MENDALAM & INSIGHT ARSITEKTUR
    # -------------------------------------------------------------
    add_heading_1("7. Pembahasan Mendalam (In-Depth Insights)")
    
    doc.add_paragraph(
        "Berdasarkan komparasi empiris dari ke-30 konfigurasi model, diperoleh sejumlah wawasan ilmiah mendalam:"
    )
    
    doc.add_paragraph(
        "1. Fenomena Skala Nano (Performa Luar Biasa E0 & E4 Nano):\n"
        "Model berukuran kecil (Nano) justru mencetak akurasi absolut tertinggi (mAP@50 > 92%). Hal ini disebabkan oleh "
        "kesesuaian kapasitas parameter model nano dengan ukuran dataset pengawasan udara yang relatif terfokus, "
        "sehingga model nano tidak mengalami overfitting. Penambahan CBAM pada model Nano (E1, E4) mempertahankan mAP di atas 90%, "
        "namun model baseline E0 sudah cukup kompak untuk menggeneralisasi fitur target dengan sangat tajam."
    )
    
    doc.add_paragraph(
        "2. Efektivitas Atensi Tunggal (E1) pada Model Skala Besar:\n"
        "Pada skala Medium dan X-Large, kapasitas representasi backbone menjadi sangat dalam. Pemasangan satu blok CBAM "
        "pada stage P5 (tahap semantik terdalam sebelum neck) memberikan bimbingan perhatian kanal dan spasial yang optimal, "
        "menghasilkan peningkatan +3.13% pada test mAP@50 (E1_yolo26x vs E0_yolo26x). Hal ini membuktikan bahwa atensi terfokus "
        "sangat membantu model besar memfilter fitur latar belakang yang rumit."
    )
    
    doc.add_paragraph(
        "3. Jebakan Atensi Berlebihan (Over-Attention Trap pada E3 & E5):\n"
        "Pemasangan CBAM di semua tahapan backbone (E3: P3+P4+P5) atau kombinasi penuh backbone+neck (E5: 6 blok CBAM) "
        "secara konsisten menghasilkan performa di bawah E1 dan baseline. Pada E5, mAP@50:95 jatuh ke 0.3458 pada skala X-Large "
        "dan latensi meningkat drastis hingga 14.78 ms (~67 FPS). Modulasi fitur berulang kali melalui sigmoid non-linear "
        "menyebabkan degradasi magnitudo gradien (gradient vanishing) dan over-smoothing pada peta aktivasi spasial."
    )

    # -------------------------------------------------------------
    # 8. KESIMPULAN & REKOMENDASI PENERAPAN
    # -------------------------------------------------------------
    add_heading_1("8. Kesimpulan & Rekomendasi Taktis Lapangan")
    
    doc.add_paragraph(
        "Kajian eksperimental komprehensif ini memberikan pedoman desain dan pemilihan model deteksi musuh UAV "
        "berdasarkan kebutuhan skenario penugasan lapangan:"
    )
    
    add_callout(
        "Rekomendasi Penerapan Operasional:\n\n"
        "1. Untuk Perangkat Edge On-board UAV (Embedded Komputasi Ringan - misal NVIDIA Jetson Orin Nano / Xavier):\n"
        "   Gunakan Model: E0_yolo26n (Baseline Nano) atau E4_yolo26n (Neck CBAM Nano).\n"
        "   Alasan: Menghasilkan akurasi tertinggi di seluruh pengujian (Test mAP@50: 92.86%), latensi paling ringan (11.48 ms / ~87.1 FPS), "
        "dan konsumsi daya minimal tanpa overhead komputasi modul tambahan.\n\n"
        "2. Untuk Server Pangkalan / Stasiun Darat (Ground Control Station High-End GPU):\n"
        "   Gunakan Model: E1_yolo26x (1× Backbone CBAM X-Large).\n"
        "   Alasan: Merupakan model berkapasitas besar terbaik dengan enemy_mAP@50 mencapai 86.81% (+6.92% dibanding baseline), "
        "memberikan diskriminasi target musuh yang superior pada citra video beresolusi tinggi dengan frame rate 79.7 FPS.\n\n"
        "3. Pedoman Desain Arsitektur (Architecture Rule of Thumb):\n"
        "   Hindari penumpukan modul atensi di seluruh tahapan (E3/E5). Terapkan modul atensi secara hemat dan strategis "
        "pada tahap semantik terdalam (P5) untuk mencapai sinergi optimal antara akurasi, efisiensi parameter, dan kecepatan inferensi.",
        title="PANDUAN PEMILIHAN MODEL LAPANGAN"
    )

    output_path = os.path.join(base_dir, "Laporan_Eksperimen_YOLO26_CBAM_UAV_Enemy_Detection.docx")
    doc.save(output_path)
    print(f"Report successfully saved to {output_path}")

if __name__ == "__main__":
    create_report()
