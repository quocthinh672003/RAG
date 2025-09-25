# POST /charts
import os
import re
import uuid
import json
import base64
from fastapi import HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from app.core.openai_client import client
from app.core.schemas import ChartIn

router = APIRouter(prefix="/charts", tags=["charts"])

STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)
router.mount("/static", StaticFiles(directory=STORAGE_DIR), name="static")

async def _download_openai_file(file_id: str) -> bytes:
    try:
        return await client.files.download(file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {e}")

def _parse_base64_payload(text: str):
    if not text:
        return None
    candidates = []
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped, count=1).strip()
        stripped = re.sub(r"```$", "", stripped, count=1).strip()
    candidates.append(stripped)
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidates.append(match.group(0))
    seen = set()
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            data = json.loads(candidate)
            if isinstance(data, dict) and data.get("base64"):
                return data
        except json.JSONDecodeError:
            continue
    return None

@router.post("/")
async def create_chart(payload: ChartIn):
    chart_id = uuid.uuid4().hex[:8]

    raw_filename = f"data_{chart_id}.txt"
    raw_path = os.path.join(STORAGE_DIR, raw_filename)
    try:
        data_text = payload.data if isinstance(payload.data, str) else json.dumps(payload.data, ensure_ascii=False)
        with open(raw_path, "w", encoding="utf-8") as raw_file:
            raw_file.write(data_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save raw data: {e}")

    pdf_filename = f"data_{chart_id}.pdf"
    pdf_path = os.path.join(STORAGE_DIR, pdf_filename)
    try:
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        text_obj = c.beginText(40, height - 50)
        for line in data_text.splitlines() or [""]:
            text_obj.textLine(line)
            if text_obj.getY() <= 40:
                c.drawText(text_obj)
                c.showPage()
                text_obj = c.beginText(40, height - 50)
        c.drawText(text_obj)
        c.save()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to convert data to PDF: {e}")

    try:
        with open(pdf_path, "rb") as f:
            uploaded_file = await client.files.create(file=f, purpose="user_data")
        file_id = uploaded_file.id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload data file: {e}")

    target_filename = f"chart_{chart_id}.{payload.output_format}"
    instruction = f"""
You are a python data scientist running inside Code Interpreter.

Steps:
1. Read and parse the attached input_file (PDF with the dataset text/JSON).
2. Create a {payload.chart_type} chart using matplotlib (seaborn optional).
3. Add labels and title:
   - Title: {payload.title or f"{payload.chart_type.title()} Chart"}
   - X-axis: {payload.x_label or "X"}
   - Y-axis: {payload.y_label or "Y"}
4. Save the chart as '{target_filename}'.
5. Open the saved file in binary mode, base64-encode its contents, and output ONLY a JSON object with keys:
   {{"filename": "{target_filename}", "base64": "<base64>"}}.
6. Do not include markdown, links, or extra narration.
"""

    try:
        tools_cfg = [{"type": "code_interpreter"}]
        if os.getenv("OPENAI_REQUIRE_CONTAINER", "0") in ("1", "true", "True"):
            tools_cfg = [{"type": "code_interpreter", "container": {"type": "auto"}}]

        response = await client.responses.create(
            model="gpt-4.1-mini",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_file", "file_id": file_id},
                    {"type": "input_text", "text": instruction},
                ],
            }],
            tools=tools_cfg,
            temperature=0,
        )

        artifacts = [
            {"id": getattr(c.file, "id", None), "name": getattr(c.file, "filename", None)}
            for block in getattr(response, "output", []) or []
            for c in getattr(block, "content", []) or []
            if getattr(c, "type", None) == "output_file" and getattr(c, "file", None)
        ]

        output_text = getattr(response, "output_text", None) or ""

        blob = None
        filename = target_filename

        if artifacts:
            picked = next(
                (a for a in artifacts if (a.get("name") or "").lower().endswith(("png", "jpg", "jpeg", "svg", "pdf"))),
                artifacts[0]
            )
            blob = await _download_openai_file(picked["id"])
            filename = picked.get("name") or target_filename
        else:
            payload_json = _parse_base64_payload(output_text)
            if not payload_json:
                raise HTTPException(
                    status_code=502,
                    detail=f"No chart artifact or base64 payload returned. AI output: {output_text[:500]}"
                )
            try:
                blob = base64.b64decode(payload_json["base64"], validate=True)
            except Exception as err:
                raise HTTPException(status_code=502, detail=f"Failed to decode chart base64: {err}")
            filename = payload_json.get("filename") or target_filename

        filename = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)
        if "." not in filename:
            filename = f"{filename}.{payload.output_format}"

        path = os.path.join(STORAGE_DIR, filename)
        with open(path, "wb") as fh:
            fh.write(blob)

        return {
            "chart_id": chart_id,
            "download_url": f"/static/{filename}",
            "response_id": getattr(response, "id", None),
            "filename": filename,
            "chart_type": payload.chart_type,
            "output_format": payload.output_format,
            "content_preview": output_text[:500] if output_text else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))