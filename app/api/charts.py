# POST /charts
import os
import uuid
from fastapi import HTTPException, APIRouter
from app.core.openai_client import client
from app.core.schemas import ChartIn

router = APIRouter(prefix="/charts", tags=["charts"])


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
async def create_chart(payload: ChartIn):
    """Generate charts using Code Interpreter with matplotlib/seaborn"""
    
    os.makedirs("storage", exist_ok=True)
    chart_id = uuid.uuid4().hex[:8]
    
    # Build instruction for Code Interpreter to generate a chart
    instruction = f"""
You are a code interpreter. Create a {payload.chart_type} chart with the following data:
- Chart type: {payload.chart_type}
- Data: {payload.data}
- Title: {payload.title or f"{payload.chart_type.title()} Chart"}
- X-axis label: {payload.x_label or "X"}
- Y-axis label: {payload.y_label or "Y"}
- Output format: {payload.output_format}

Instructions:
1. Parse the data (JSON or CSV format)
2. Create a {payload.chart_type} chart using matplotlib or seaborn
3. Add proper labels, title, and formatting
4. Save the chart as an image file
5. Return the saved file as an output file artifact

Make sure the chart is well-formatted and professional-looking.
""".strip()

    try:

        tools_cfg = [{"type": "code_interpreter"}]
        if os.getenv("OPENAI_REQUIRE_CONTAINER", "0") in ("1", "true", "True"):
            tools_cfg = [{"type": "code_interpreter", "container": {"type": "auto"}}]

        response = await client.responses.create(
            model="gpt-4.1",
            input=[{
                "role": "user",
                "content": [{"type": "input_text", "text": instruction}],
            }],
            tools=tools_cfg,
            tool_choice={"type": "code_interpreter"},
            temperature=0,
        )

        # Collect file artifacts
        artifacts = [
            {"id": getattr(c.file, "id", None), "name": getattr(c.file, "filename", None)}
            for block in (getattr(response, "output", []) or [])
            for c in (getattr(block, "content", []) or [])
            if getattr(c, "type", None) == "output_file" and getattr(c, "file", None)
        ]
        output_text = getattr(response, "output_text", None) or ""

        if artifacts:
            # Find the chart file (image format)
            picked = None
            for a in artifacts:
                name = (a.get("name") or "").lower()
                if any(name.endswith(f".{fmt}") for fmt in ["png", "jpg", "jpeg", "svg", "pdf"]):
                    picked = a
                    break
            if not picked:
                picked = artifacts[0]

            blob = await _download_openai_file(picked["id"])
            filename = picked.get("name") or f"chart_{chart_id}.{payload.output_format}"
            if "." not in filename:
                filename = f"chart_{chart_id}.{payload.output_format}"
            path = os.path.join("storage", filename)
            with open(path, "wb") as fh:
                fh.write(blob)

            return {
                "chart_id": chart_id,
                "download_url": f"/static/{os.path.basename(path)}",
                "response_id": response.id,
                "filename": os.path.basename(path),
                "chart_type": payload.chart_type,
                "output_format": payload.output_format,
                "content_preview": output_text[:500] if output_text else None,
            }

        raise HTTPException(status_code=502, detail=f"No chart artifact returned. Retry or adjust data format.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
