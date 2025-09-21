# POST /export
import os, json, uuid, pandas as pd
from fastapi import HTTPException, APIRouter
from app.core.schemas import ExportIn
import markdown as md
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


router = APIRouter(prefix="/export", tags=["export"])


@router.post("/")
async def export_content(payload: ExportIn):
    """Export content to markdown, html, csv, xlsx, pdf"""
    os.makedirs("storage", exist_ok=True)
    export_id = uuid.uuid4().hex[:8]

    if payload.format == "md":
        path = f"storage/export_{export_id}.md"
        open(path, "w", encoding="utf-8").write(payload.content)
        return {"download_url": f"/static/export_{export_id}.md"}

    if payload.format == "html":
        path = f"storage/export_{export_id}.html"
        html = md.markdown(payload.content)
        html = f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>{payload.title or "Export"}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background: #f4f4f4; padding: 2px 4px; }}
        pre {{ background: #f4f4f4; padding: 10px; }}
    </style>
</head>
<body>
{html}
</body>
</html>"""
        open(path, "w", encoding="utf-8").write(html)
        return {"download_url": f"/static/export_{export_id}.html"}

    if payload.format == "csv" or payload.format == "xlsx":
        try:
            data = json.loads(payload.content)
            df = pd.DataFrame(data if isinstance(data, list) else [data])
        except Exception as e:
            df = pd.DataFrame({"content": payload.content})

        if payload.format == "csv":
            path = f"storage/export_{export_id}.csv"
            df.to_csv(path, index=False, encoding="utf-8")
        elif payload.format == "xlsx":
            path = f"storage/export_{export_id}.xlsx"
            df.to_excel(path, index=False)
        return {"download_url": f"/static/export_{export_id}.{payload.format}"}

    if payload.format == "pdf":
        # Create DataFrame from content
        try:
            data = json.loads(payload.content)
            df = pd.DataFrame(data if isinstance(data, list) else [data])
        except Exception as e:
            df = pd.DataFrame({"content": [payload.content]})

        # Create PDF with reportlab
        path = f"storage/export_{export_id}.pdf"
        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add title
        title = Paragraph(f"<b>{payload.title or 'Export Report'}</b>", styles["Title"])
        story.append(title)
        story.append(Spacer(1, 12))

        # Create table from DataFrame
        table_data = [df.columns.tolist()]  # Header
        for _, row in df.iterrows():
            table_data.append([str(cell) for cell in row])

        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        story.append(table)
        doc.build(story)

        return {"download_url": f"/static/export_{export_id}.pdf"}

    raise HTTPException(status_code=400, detail=f"Invalid format: {payload.format}")
