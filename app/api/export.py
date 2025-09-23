# POST /export
import os, uuid
from fastapi import HTTPException, APIRouter
import markdown as md
from app.core.schemas import ExportIn
from app.core.openai_client import client

router = APIRouter(prefix="/export", tags=["export"])


async def _download_openai_file(file_id: str) -> bytes:
    stream = await client.files.content(file_id)
    if hasattr(stream, "aread"):
        return await stream.aread()
    if hasattr(stream, "read"):
        return stream.read()
    if isinstance(stream, (bytes, bytearray)):
        return bytes(stream)
    raise RuntimeError("Unsupported file content stream type")


@router.post("/")
async def export_content(payload: ExportIn):
    """Export content with OpenAI Responses API + Code Interpreter.
    Formats: md, html, csv, xlsx.
    For pdf/docx/pptx: return 501 (pending sandbox libs).
    """
    os.makedirs("storage", exist_ok=True)
    export_id = uuid.uuid4().hex[:8]
    fmt = payload.format.lower()

    # Build instruction for Code Interpreter to generate an artifact
    instruction = f"""
You are a code interpreter. Create an export file in format: {fmt}.
- Programmatically generate and save the file.
- The content to include is below:
---
{payload.content}
---
- Return the saved file as an output file artifact (e.g., export.{fmt}).
""".strip()

    # If user requests formats not guaranteed in sandbox, reject early
    if fmt in ("pdf", "docx", "pptx"):
        raise HTTPException(status_code=501, detail=f"Format '{fmt}' not guaranteed in Code Interpreter sandbox. Try md/html/csv/xlsx.")

    try:
        response = await client.responses.create(
            model="gpt-4o",
            input=instruction,
            tools=[{"type": "code_interpreter"}],
            temperature=0.2,
            max_tokens=1000,
        )

        # Collect file artifacts
        artifacts = []
        output_text = getattr(response, "output_text", None) or ""
        for item in getattr(response, "output", []) or []:
            for c in getattr(item, "content", []) or []:
                f = getattr(c, "file", None)
                if f:
                    artifacts.append({"id": getattr(f, "id", None), "name": getattr(f, "filename", None)})

        if artifacts:
            picked = None
            for a in artifacts:
                name = (a.get("name") or "").lower()
                if name.endswith(f".{fmt}"):
                    picked = a
                    break
            if not picked:
                picked = artifacts[0]

            blob = await _download_openai_file(picked["id"])
            filename = picked.get("name") or f"export_{export_id}.{fmt}"
            if "." not in filename:
                filename = f"export_{export_id}.{fmt}"
            path = os.path.join("storage", filename)
            with open(path, "wb") as fh:
                fh.write(blob)

            return {
                "download_url": f"/static/{os.path.basename(path)}",
                "response_id": response.id,
                "filename": os.path.basename(path),
                "content_preview": output_text[:500] if output_text else None,
            }

        # No artifact: for md/html we can write output_text
        if fmt in ("md", "html"):
            filename = f"export_{export_id}.{fmt}"
            path = os.path.join("storage", filename)
            if fmt == "md":
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(output_text or (payload.content or ""))
            else:
                content_md = output_text or (payload.content or "")
                html = md.markdown(content_md)
                html = f"""<!doctype html>
<html><head><meta charset=\"utf-8\"><title>Export</title></head>
<body>{html}</body></html>"""
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(html)
            return {
                "download_url": f"/static/{os.path.basename(path)}",
                "response_id": response.id,
                "filename": os.path.basename(path),
            }

        raise HTTPException(status_code=502, detail=f"No artifact returned for format '{fmt}'. Retry or adjust prompt.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))