from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path


def sanitize_filename(value):
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("_.-")
    return cleaned or "expedition_briefing"


def build_markdown_filename(route_name, trip_profile=None):
    route_part = sanitize_filename(route_name)
    days = trip_profile.get("number_of_days") if trip_profile else None
    preference = trip_profile.get("pack_weight_preference", "balanced").lower() if trip_profile else "balanced"
    if days:
        return f"{route_part}_{days}d_{preference}_briefing.md"
    return f"{route_part}_briefing.md"


def build_pdf_filename(route_name, trip_profile=None):
    route_part = sanitize_filename(route_name)
    days = trip_profile.get("number_of_days") if trip_profile else None
    preference = trip_profile.get("pack_weight_preference", "balanced").lower() if trip_profile else "balanced"
    if days:
        return f"{route_part}_{days}d_{preference}_briefing.pdf"
    return f"{route_part}_briefing.pdf"


def markdown_bytes(markdown_text):
    return markdown_text.encode("utf-8")


def pdf_bytes(markdown_text: str, title: str = "Expedition Briefing") -> bytes:
    """
    Convert markdown text to a PDF using reportlab platypus.
    Text wraps correctly at the page margin; headings, bullets, and
    horizontal rules are all rendered properly.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem
        )
    except ImportError as exc:
        raise ImportError(
            "reportlab is required for PDF export. Install it with 'pip install reportlab'."
        ) from exc

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )

    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "DocTitle",
            parent=base["Title"],
            fontSize=18,
            spaceAfter=14,
            textColor=colors.HexColor("#1a1a2e"),
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=14,
            spaceBefore=14,
            spaceAfter=6,
            textColor=colors.HexColor("#2171B5"),
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor("#2171B5"),
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontSize=11,
            spaceBefore=8,
            spaceAfter=3,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=10,
            leading=15,
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontSize=10,
            leading=15,
            leftIndent=16,
            spaceAfter=2,
        ),
        "bold_label": ParagraphStyle(
            "BoldLabel",
            parent=base["Normal"],
            fontSize=10,
            leading=15,
            spaceAfter=2,
        ),
    }

    story = []
    story.append(Paragraph(title, styles["title"]))

    bullet_buffer: list[str] = []
    table_buffer: list[str] = []

    def flush_bullets():
        if not bullet_buffer:
            return
        items = [
            ListItem(Paragraph(_escape(b), styles["bullet"]), leftIndent=16)
            for b in bullet_buffer
        ]
        story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=16))
        bullet_buffer.clear()

    def flush_table():
        if not table_buffer:
            return
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors as rl_colors

        rows = []
        for row_line in table_buffer:
            cells = [c.strip() for c in row_line.strip().strip("|").split("|")]
            rows.append(cells)

        # Drop separator rows (e.g. |---|---|)
        rows = [r for r in rows if not all(re.match(r"^-+$", c.strip()) for c in r)]
        if not rows:
            table_buffer.clear()
            return

        col_count = max(len(r) for r in rows)
        # Pad short rows
        rows = [r + [""] * (col_count - len(r)) for r in rows]

        # Wrap cell text in Paragraph for word-wrap
        body_style = ParagraphStyle("TC", parent=base["Normal"], fontSize=9, leading=12)
        header_style = ParagraphStyle("TH", parent=base["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold")
        para_rows = []
        for i, row in enumerate(rows):
            st = header_style if i == 0 else body_style
            para_rows.append([Paragraph(_inline_bold(_escape(cell)), st) for cell in row])

        col_width = (doc.width) / col_count
        tbl = Table(para_rows, colWidths=[col_width] * col_count, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#2171B5")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), rl_colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.HexColor("#f5f8fc"), rl_colors.white]),
            ("GRID",       (0, 0), (-1, -1), 0.4, rl_colors.HexColor("#d0d0d0")),
            ("VALIGN",     (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(Spacer(1, 4))
        story.append(tbl)
        story.append(Spacer(1, 6))
        table_buffer.clear()

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()

        # Markdown table row — collect until blank or non-table line
        if line.strip().startswith("|"):
            flush_bullets()
            table_buffer.append(line)
            continue
        else:
            flush_table()

        if line.startswith("# "):
            flush_bullets()
            story.append(Paragraph(_escape(line[2:]), styles["h1"]))

        elif line.startswith("## "):
            flush_bullets()
            story.append(Paragraph(_escape(line[3:]), styles["h2"]))

        elif line.startswith("### "):
            flush_bullets()
            story.append(Paragraph(_escape(line[4:]), styles["h3"]))

        elif line.startswith("- ") or line.startswith("* "):
            bullet_buffer.append(line[2:])

        elif line.strip() == "---":
            flush_bullets()
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
            story.append(Spacer(1, 4))

        elif line.strip() == "":
            flush_bullets()
            story.append(Spacer(1, 5))

        else:
            flush_bullets()
            story.append(Paragraph(_inline_bold(_escape(line)), styles["body"]))

    flush_bullets()
    flush_table()

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _escape(text: str) -> str:
    """Escape XML special chars for reportlab Paragraph."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline_bold(text: str) -> str:
    """Convert **word** markdown bold to <b>word</b> for reportlab."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def export_markdown_to_file(markdown_text, file_path):
    path = Path(file_path)
    path.write_text(markdown_text, encoding="utf-8")
    return path


def export_pdf_to_file(markdown_text, file_path, title="Expedition Briefing"):
    path = Path(file_path)
    path.write_bytes(pdf_bytes(markdown_text, title=title))
    return path
