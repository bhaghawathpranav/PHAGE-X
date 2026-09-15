from __future__ import annotations

from io import BytesIO
from typing import Any, Mapping

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .schemas import ResearchRankResponse


INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#667085")
PURPLE = colors.HexColor("#792CCE")
PINK = colors.HexColor("#E13A97")
CYAN = colors.HexColor("#24B7D3")
PALE = colors.HexColor("#F7F5FB")
LINE = colors.HexColor("#E5E7EB")


def _ascii(text: str) -> str:
    return text.replace("—", "-").replace("–", "-").replace("→", "->")


def build_research_rank_pdf(result: ResearchRankResponse, status: Mapping[str, Any]) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title=f"PHAGE-X ranking report - {result.host_id}",
        author="PHAGE-X",
        subject="Explainable phage-host compatibility research ranking",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportKicker", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=PURPLE, spaceAfter=6, tracking=1.2))
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=28, textColor=INK, alignment=TA_LEFT, spaceAfter=6))
    styles.add(ParagraphStyle(name="ReportLead", parent=styles["Normal"], fontSize=10, leading=15, textColor=MUTED, spaceAfter=15))
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INK, spaceBefore=13, spaceAfter=8))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=7.5, leading=10.5, textColor=MUTED))
    styles.add(ParagraphStyle(name="Tiny", parent=styles["Normal"], fontSize=6.7, leading=8.5, textColor=MUTED))
    styles.add(ParagraphStyle(name="Footer", parent=styles["Normal"], fontSize=7, textColor=MUTED, alignment=TA_RIGHT))

    def decorate_page(canvas, doc):
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(16 * mm, height - 13 * mm, width - 16 * mm, height - 13 * mm)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(INK)
        canvas.drawString(16 * mm, height - 10 * mm, "PHAGE-X")
        canvas.setFillColor(CYAN)
        canvas.drawString(42 * mm, height - 10 * mm, "RESEARCH RANKING")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(width - 16 * mm, 10 * mm, f"Page {doc.page}")
        canvas.drawString(16 * mm, 10 * mm, "Generated locally from the frozen PHAGE-X model artifact")
        canvas.restoreState()

    story = [
        Paragraph("HELD-OUT HOST REPORT", styles["ReportKicker"]),
        Paragraph(f"Phage ranking for {result.host_id}", styles["ReportTitle"]),
        Paragraph(
            "An explainable compatibility ranking against the PHAGE-X catalog. Scores prioritize candidates for research follow-up and do not establish susceptibility, safety, or treatment suitability.",
            styles["ReportLead"],
        ),
    ]

    metrics = status.get("test_metrics", {})
    metric_data = [
        ["MODEL", "TEST AUROC", "PR-AUC", "TOP-5 RECALL"],
        [
            Paragraph(_ascii(str(status.get("model", "XGBoost"))), styles["Small"]),
            f"{float(metrics.get('roc_auc', 0)):.3f}",
            f"{float(metrics.get('average_precision', 0)):.3f}",
            f"{float(metrics.get('top_5_host_recall', 0)) * 100:.0f}%",
        ],
    ]
    metric_table = Table(metric_data, colWidths=[65 * mm, 35 * mm, 35 * mm, 35 * mm], rowHeights=[8 * mm, 12 * mm])
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
        ("TEXTCOLOR", (1, 1), (-1, 1), PURPLE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 6.5),
        ("FONTSIZE", (1, 1), (-1, 1), 13),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
    ]))
    story.extend([metric_table, Spacer(1, 4 * mm)])

    metadata = Table([
        ["Host role", _ascii(result.split_role.replace("-", " ").title()), "Model version", _ascii(result.model_version)],
        ["Feature source", _ascii(result.feature_source), "Catalog size", str(status.get("candidate_phages", 105))],
    ], colWidths=[26 * mm, 58 * mm, 28 * mm, 58 * mm])
    metadata.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("TEXTCOLOR", (3, 0), (3, -1), INK),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([metadata, Paragraph("Ranked candidates", styles["SectionTitle"])])

    ranking_rows = [["RANK", "PHAGE ID", "COMPATIBILITY", "MODEL SIGNAL"]]
    for index, candidate in enumerate(result.candidates, 1):
        decision = candidate.decision.replace("higher-priority-research-signal", "Higher priority").replace("lower-priority-research-signal", "Lower priority")
        ranking_rows.append([f"{index:02d}", candidate.phage_id, f"{candidate.compatibility * 100:.1f}%", decision])
    ranking = Table(ranking_rows, repeatRows=1, colWidths=[18 * mm, 63 * mm, 42 * mm, 47 * mm], rowHeights=[8 * mm] + [7.2 * mm] * len(result.candidates))
    ranking_style = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("TEXTCOLOR", (0, 1), (0, -1), MUTED),
        ("TEXTCOLOR", (2, 1), (2, -1), PURPLE),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBFAFD")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]
    for row, candidate in enumerate(result.candidates, 1):
        if candidate.decision.startswith("higher"):
            ranking_style.append(("TEXTCOLOR", (3, row), (3, row), CYAN))
            ranking_style.append(("FONTNAME", (3, row), (3, row), "Helvetica-Bold"))
    ranking.setStyle(TableStyle(ranking_style))
    story.append(ranking)

    explanation_blocks = []
    for index, candidate in enumerate(result.candidates[:3], 1):
        rationale = " | ".join(_ascii(item) for item in candidate.rationale)
        explanation_blocks.extend([
            Paragraph(f"{index:02d}  {candidate.phage_id}  -  {candidate.compatibility * 100:.1f}%", styles["SectionTitle"]),
            Paragraph(rationale, styles["Small"]),
            Spacer(1, 2 * mm),
        ])
    story.extend([Paragraph("Top-candidate explanations", styles["SectionTitle"]), KeepTogether(explanation_blocks)])

    blockers = "<br/>".join(f"- {_ascii(item)}" for item in result.cocktail_blockers)
    safety = Table([[Paragraph("COMBINATION STATUS", styles["ReportKicker"]), Paragraph(f"<b>{result.cocktail_status.upper()}</b><br/>{blockers}", styles["Small"]) ]], colWidths=[43 * mm, 127 * mm])
    safety.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7FA")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#F2B8D4")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([Spacer(1, 4 * mm), safety, Spacer(1, 5 * mm), Paragraph(f"<b>Important:</b> {_ascii(result.disclaimer)}", styles["Tiny"])])
    document.build(story, onFirstPage=decorate_page, onLaterPages=decorate_page)
    return output.getvalue()
