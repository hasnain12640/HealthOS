"""
Generates a synthetic Pakistani lab report PDF for HealthOS demo.
Run once: python create_demo_pdf.py
Output: demo_lab_report.pdf  (place in backend/data/ or project root)
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "demo_lab_report.pdf")

def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ---- Header ----
    header_style = ParagraphStyle("header", fontSize=18, fontName="Helvetica-Bold",
                                  alignment=TA_CENTER, textColor=colors.HexColor("#1a3a5c"))
    sub_style = ParagraphStyle("sub", fontSize=10, fontName="Helvetica",
                               alignment=TA_CENTER, textColor=colors.HexColor("#555555"))
    label_style = ParagraphStyle("label", fontSize=9, fontName="Helvetica",
                                 textColor=colors.HexColor("#333333"))
    value_style = ParagraphStyle("value", fontSize=9, fontName="Helvetica-Bold",
                                 textColor=colors.HexColor("#000000"))
    normal = ParagraphStyle("norm", fontSize=9, fontName="Helvetica",
                            textColor=colors.HexColor("#333333"))

    story.append(Paragraph("CHUGHTAI LAB", header_style))
    story.append(Paragraph("Lahore | Karachi | Islamabad | www.chughtailab.com", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 0.3*cm))

    # ---- Patient Info ----
    story.append(Paragraph("<b>LABORATORY REPORT</b>", ParagraphStyle("rpt", fontSize=11,
                            fontName="Helvetica-Bold", alignment=TA_CENTER)))
    story.append(Spacer(1, 0.3*cm))

    patient_data = [
        ["Patient Name:", "Bilal Ahmed", "Report No:", "LHR-2024-081547"],
        ["Age / Gender:", "34 Years / Male", "Report Date:", "15-Aug-2024"],
        ["Ref. Doctor:", "Dr. Ayesha Tariq", "Sample Date:", "15-Aug-2024"],
        ["Patient ID:", "BLR-00342", "Lab Branch:", "Gulberg III, Lahore"],
    ]
    pt = Table(patient_data, colWidths=[3.5*cm, 7*cm, 3*cm, 5*cm])
    pt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#333333")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f5f8fc"), colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(pt)
    story.append(Spacer(1, 0.5*cm))

    # ---- Helper to add a test section ----
    def section_header(title):
        return Paragraph(f"<b>{title}</b>", ParagraphStyle("sh", fontSize=10,
                         fontName="Helvetica-Bold", textColor=colors.white,
                         backColor=colors.HexColor("#1a3a5c"), leftIndent=6,
                         spaceBefore=4, spaceAfter=2))

    col_header = ["TEST NAME", "RESULT", "UNIT", "REFERENCE RANGE", "FLAG"]
    header_style_t = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f0f7")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#222222")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fbfd")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
    ])

    def flag_color(flag):
        if flag == "L":
            return colors.HexColor("#e67e00")
        if flag == "H":
            return colors.HexColor("#cc0000")
        return colors.HexColor("#1a7a1a")

    def make_result_row(name, result, unit, ref_range, flag):
        fc = flag_color(flag)
        return [name, result, unit, ref_range, Paragraph(f'<font color="#{fc.hexval()[2:]}"><b>{flag}</b></font>',
                ParagraphStyle("f", fontSize=8.5, fontName="Helvetica-Bold", alignment=TA_CENTER))]

    # ---- COMPLETE BLOOD COUNT ----
    story.append(section_header("COMPLETE BLOOD COUNT (CBC)"))
    cbc_data = [col_header] + [
        make_result_row("Hemoglobin",      "11.8",   "g/dL",   "13.0 - 17.0",   "L"),
        make_result_row("WBC Count",       "7,200",  "/µL",    "4000 - 11000",  "N"),
        make_result_row("Platelets",       "245,000","/µL",    "150000 - 400000","N"),
        make_result_row("Hematocrit (PCV)","36.0",   "%",      "40.0 - 52.0",   "L"),
        make_result_row("MCV",             "72.0",   "fL",     "80.0 - 100.0",  "L"),
        make_result_row("MCH",             "22.5",   "pg",     "27.0 - 33.0",   "L"),
    ]
    cbc_table = Table(cbc_data, colWidths=[6*cm, 2.5*cm, 2*cm, 4.5*cm, 1.5*cm])
    cbc_table.setStyle(header_style_t)
    story.append(cbc_table)
    story.append(Spacer(1, 0.4*cm))

    # ---- METABOLIC PANEL ----
    story.append(section_header("METABOLIC PANEL"))
    met_data = [col_header] + [
        make_result_row("Fasting Blood Glucose", "108",  "mg/dL", "70 - 100",   "H"),
        make_result_row("Creatinine",             "0.9",  "mg/dL", "0.7 - 1.2",  "N"),
        make_result_row("Urea (BUN)",             "14.0", "mg/dL", "7.0 - 20.0", "N"),
        make_result_row("Uric Acid",              "5.8",  "mg/dL", "3.4 - 7.0",  "N"),
        make_result_row("SGPT (ALT)",             "28.0", "U/L",   "0 - 40",     "N"),
        make_result_row("SGOT (AST)",             "24.0", "U/L",   "0 - 40",     "N"),
    ]
    met_table = Table(met_data, colWidths=[6*cm, 2.5*cm, 2*cm, 4.5*cm, 1.5*cm])
    met_table.setStyle(header_style_t)
    story.append(met_table)
    story.append(Spacer(1, 0.4*cm))

    # ---- LIPID PROFILE ----
    story.append(section_header("LIPID PROFILE"))
    lip_data = [col_header] + [
        make_result_row("Total Cholesterol",    "215",  "mg/dL", "< 200",        "H"),
        make_result_row("HDL Cholesterol",       "42.0", "mg/dL", "> 40",         "N"),
        make_result_row("LDL Cholesterol",       "148.0","mg/dL", "< 130",        "H"),
        make_result_row("Triglycerides",         "124.0","mg/dL", "< 150",        "N"),
    ]
    lip_table = Table(lip_data, colWidths=[6*cm, 2.5*cm, 2*cm, 4.5*cm, 1.5*cm])
    lip_table.setStyle(header_style_t)
    story.append(lip_table)
    story.append(Spacer(1, 0.4*cm))

    # ---- THYROID & VITAMINS ----
    story.append(section_header("THYROID FUNCTION & VITAMINS"))
    thy_data = [col_header] + [
        make_result_row("TSH",              "2.4",  "mIU/L",  "0.4 - 4.0",   "N"),
        make_result_row("Vitamin D (25-OH)","18.0", "ng/mL",  "30.0 - 100.0","L"),
        make_result_row("Vitamin B12",      "310.0","pg/mL",  "200 - 900",   "N"),
        make_result_row("Ferritin",         "8.5",  "ng/mL",  "12 - 300",    "L"),
    ]
    thy_table = Table(thy_data, colWidths=[6*cm, 2.5*cm, 2*cm, 4.5*cm, 1.5*cm])
    thy_table.setStyle(header_style_t)
    story.append(thy_table)
    story.append(Spacer(1, 0.5*cm))

    # ---- Footer ----
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2*cm))
    footer_style = ParagraphStyle("ft", fontSize=7.5, fontName="Helvetica",
                                  textColor=colors.HexColor("#777777"), alignment=TA_CENTER)
    story.append(Paragraph(
        "This report is generated for the registered patient only. Results should be interpreted in clinical context.",
        footer_style))
    story.append(Paragraph(
        "For queries: 0311-CHUGHTAI (0311-2484824) | helpdesk@chughtailab.com",
        footer_style))

    doc.build(story)
    print(f"PDF created: {OUTPUT_PATH}")

if __name__ == "__main__":
    build_pdf()
