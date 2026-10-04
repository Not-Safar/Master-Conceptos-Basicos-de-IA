"""Genera el reporte de una página a partir de REPORT.md (requiere reportlab)."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "reporte-aula-rag.pdf"

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    style = ParagraphStyle("Body", fontName="Helvetica", fontSize=10.2, leading=14.2,
                           textColor=colors.HexColor("#243449"), spaceAfter=9)
    heading = ParagraphStyle("Heading", parent=style, fontName="Helvetica-Bold", fontSize=10.8,
                             leading=15, textColor=colors.HexColor("#087F8C"), spaceAfter=4)
    title = ParagraphStyle("Title", parent=style, fontName="Helvetica-Bold", fontSize=25,
                           leading=30, textColor=colors.HexColor("#12243B"), spaceAfter=5)
    subtitle = ParagraphStyle("Subtitle", parent=style, fontSize=10, textColor=colors.HexColor("#64748B"))
    story = [Paragraph("Aula RAG", title),
             Paragraph("Proyecto final | Informe de diseño y verificación | 2 de octubre de 2026", subtitle),
             Spacer(1, 5 * mm)]
    for block in (ROOT / "REPORT.md").read_text(encoding="utf-8-sig").split("\n\n"):
        if block.startswith("#") or not block.strip():
            continue
        text = block.replace("\n", " ").strip()
        if text.startswith("**"):
            label, body = text[2:].split("**", 1)
            story.extend([Paragraph(escape(label), heading), Paragraph(escape(body.strip()), style)])
        else:
            story.append(Paragraph(escape(text), style))
    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#D8E3EA"))
        canvas.line(20 * mm, 17 * mm, A4[0] - 20 * mm, 17 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(20 * mm, 12 * mm, "Streamlit  /  FastAPI  /  ChromaDB  /  Google AI")
        canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, str(doc.page))
    SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm,
                      topMargin=18 * mm, bottomMargin=23 * mm).build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)

if __name__ == "__main__":
    main()
