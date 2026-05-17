from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from app.services.file_preview import DATA_CACHE
from app.services.report_builder import build_report


def _get_report(saved_name: str) -> dict:
    dataframe = DATA_CACHE.get(saved_name)
    if dataframe is None:
        raise ValueError("Session expired or file not found. Please re-upload.")
    return build_report(dataframe)


def _set_cell_shading(cell, color: str):
    shading_elm = cell._element.get_or_add_tcPr()
    shading = shading_elm.makeelement(qn("w:shd"), {
        qn("w:fill"): color,
        qn("w:val"): "clear",
    })
    shading_elm.append(shading)


def export_report_docx(saved_name: str, original_filename: str) -> BytesIO:
    report = _get_report(saved_name)
    doc = Document()
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Arial"
    font.size = Pt(10)

    title = doc.add_heading(f"DataFlowBI Analysis Report", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(f"Source file: {original_filename}")
    doc.add_paragraph("")

    sections = [
        ("Missing Statistics", "missing", None),
        ("Numeric Summary", "numeric_summary", ["count", "mean", "std", "min", "max"]),
        ("Sample Data (First 5 Rows)", "sample_rows", None),
    ]

    for section_title, report_key, col_subset in sections:
        data = report.get(report_key)
        if not data:
            continue

        doc.add_heading(section_title, level=1)

        if report_key == "missing":
            table = doc.add_table(rows=1, cols=3)
            table.style = "Light Grid Accent 1"
            hdr = table.rows[0].cells
            hdr[0].text = "Field"
            hdr[1].text = "Missing Count"
            hdr[2].text = "Missing Rate"
            for field in sorted(data.keys()):
                row_cells = table.add_row().cells
                row_cells[0].text = str(field)
                row_cells[1].text = str(data[field])
                mr = report.get("missing_rate", {}).get(field, 0)
                row_cells[2].text = f"{mr:.2%}" if isinstance(mr, (int, float)) else str(mr)

        elif report_key == "numeric_summary":
            if isinstance(data, dict) and data:
                cols = col_subset or ["count", "mean", "std", "min", "max"]
                table = doc.add_table(rows=1, cols=1 + len(cols))
                table.style = "Light Grid Accent 1"
                hdr = table.rows[0].cells
                hdr[0].text = "Field"
                for i, c in enumerate(cols):
                    hdr[i + 1].text = c.capitalize()
                for field, stats in sorted(data.items()):
                    row_cells = table.add_row().cells
                    row_cells[0].text = str(field)
                    for i, c in enumerate(cols):
                        val = stats.get(c, "")
                        row_cells[i + 1].text = f"{val:.4f}" if isinstance(val, float) else str(val)

        elif report_key == "sample_rows":
            if isinstance(data, list) and data:
                cols = list(data[0].keys())
                table = doc.add_table(rows=1, cols=len(cols))
                table.style = "Light Grid Accent 1"
                hdr = table.rows[0].cells
                for i, c in enumerate(cols):
                    hdr[i].text = str(c)
                for row in data:
                    row_cells = table.add_row().cells
                    for i, c in enumerate(cols):
                        row_cells[i].text = str(row.get(c, ""))

        doc.add_paragraph("")

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def export_report_excel(saved_name: str, original_filename: str) -> BytesIO:
    report = _get_report(saved_name)
    buf = BytesIO()

    sheet_map: list[tuple[str, Any]] = [
        ("Missing Stats", report.get("missing")),
        ("Numeric Summary", report.get("numeric_summary")),
        ("Sample Data", report.get("sample_rows")),
        ("Frequency", report.get("frequencies")),
        ("Pareto", report.get("pareto")),
        ("Boxplot", report.get("boxplot")),
        ("Correlation", report.get("correlation")),
        ("Group Stats", report.get("group_stats")),
        ("Binning", report.get("binning")),
        ("Violin", report.get("violin")),
        ("Scatter Matrix", report.get("scatter_matrix")),
        ("Missing Heatmap", report.get("missing_heatmap")),
        ("Time Series", report.get("timeseries")),
        ("Outliers", report.get("outliers")),
    ]

    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        workbook = writer.book
        for sheet_name, data in sheet_map:
            if not data:
                continue

            safe_name = sheet_name[:31]
            if isinstance(data, list):
                df = pd.DataFrame(data)
                if not df.empty:
                    df.to_excel(writer, sheet_name=safe_name, index=False)
            elif isinstance(data, dict):
                try:
                    df = pd.DataFrame(data).transpose().reset_index()
                    df.columns = ["Field"] + [str(c) for c in df.columns[1:]]
                    df.to_excel(writer, sheet_name=safe_name, index=False)
                except (ValueError, TypeError):
                    rows = []
                    for k, v in data.items():
                        if isinstance(v, dict):
                            row = {"Field": k}
                            row.update(v)
                            rows.append(row)
                        else:
                            rows.append({"Field": k, "Value": v})
                    if rows:
                        pd.DataFrame(rows).to_excel(writer, sheet_name=safe_name, index=False)

    buf.seek(0)
    return buf
