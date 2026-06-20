"""
PDF e-challan generator using ReportLab.

Generates a formal, printable traffic e-challan document with:
  - Government-style header
  - Vehicle details
  - Violation details with MV Act sections
  - Bilingual content (English + Hindi)
  - Total fine summary
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def generate_pdf(challan_data: dict) -> bytes:
    """
    Generate a PDF challan.

    Args:
        challan_data: dict with keys:
            plate, violations (list[str]), total_fine (int),
            timestamp (str), facts (dict), riders (int)

    Returns: PDF as bytes
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ChallanTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=HexColor("#1a1a2e"),
        spaceAfter=4*mm,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "ChallanSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=6*mm,
    )
    heading_style = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=HexColor("#1a1a2e"),
        spaceBefore=6*mm,
        spaceAfter=3*mm,
    )
    body_style = ParagraphStyle(
        "ChallanBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
    )
    fine_style = ParagraphStyle(
        "FineLine",
        parent=styles["Normal"],
        fontSize=13,
        textColor=HexColor("#c0392b"),
        spaceBefore=4*mm,
        alignment=TA_RIGHT,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=HexColor("#999999"),
        alignment=TA_CENTER,
        spaceBefore=10*mm,
    )

    plate = challan_data.get("plate", "NOT READABLE")
    violations = challan_data.get("violations", [])
    total_fine = challan_data.get("total_fine", 0)
    ts = challan_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    facts = challan_data.get("facts", {})
    riders = challan_data.get("riders", 1)

    elements = []

    # ── Header ──
    elements.append(Paragraph("TRAFFIC E-CHALLAN", title_style))
    elements.append(Paragraph(
        "Motor Vehicles Act 1988 (as amended by MV Amendment Act 2019)",
        subtitle_style,
    ))
    elements.append(HRFlowable(
        width="100%", thickness=1.5,
        color=HexColor("#1a1a2e"), spaceAfter=6*mm,
    ))

    # ── Vehicle Info Table ──
    info_data = [
        ["Challan No.", f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"],
        ["Date & Time", ts],
        ["Vehicle No.", plate or "NOT READABLE"],
        ["Riders Detected", str(riders)],
    ]
    info_table = Table(info_data, colWidths=[5*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#333333")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(info_table)

    # ── Violations ──
    elements.append(Paragraph("VIOLATION DETAILS", heading_style))

    for v in violations:
        f = facts.get(v, {}) if facts else {}
        sec = f.get("section", "—")
        title = f.get("title", "—")
        fine = f.get("fine_inr", 0)
        dis = f.get("disqualification", "None")
        comp = "Yes (compoundable on spot)" if f.get("compoundable") else "No"

        viol_data = [
            ["Violation", v.replace("_", " ").title()],
            ["Section", f"{sec} — {title}"],
            ["Fine", f"₹ {fine}"],
            ["Disqualification", dis or "None"],
            ["Compoundable", comp],
        ]
        viol_table = Table(viol_data, colWidths=[4*cm, 13*cm])
        viol_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BACKGROUND", (0, 0), (0, 0), HexColor("#fee2e2")),
            ("TEXTCOLOR", (1, 0), (1, 0), HexColor("#c0392b")),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#dddddd")),
        ]))
        elements.append(viol_table)
        elements.append(Spacer(1, 3*mm))

    # ── Total Fine ──
    elements.append(HRFlowable(
        width="100%", thickness=1, color=HexColor("#cccccc"), spaceBefore=4*mm,
    ))
    elements.append(Paragraph(f"<b>TOTAL FINE: ₹ {total_fine}</b>", fine_style))

    # ── Footer ──
    elements.append(Spacer(1, 10*mm))
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=HexColor("#cccccc"),
    ))
    elements.append(Paragraph(
        "This e-challan is auto-generated from photographic evidence using AI-based "
        "violation detection. Legal provisions sourced from Motor Vehicles Act 1988 "
        "(as amended 2019). For disputes, contact the local RTO.",
        footer_style,
    ))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"System: Bangalore Traffic Violation AI (Flipkart GRiD Theme 3)",
        footer_style,
    ))

    doc.build(elements)
    return buf.getvalue()
