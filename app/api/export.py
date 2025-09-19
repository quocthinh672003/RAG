# POST /export
import os, json, uuid, pandas as pd
from fastapi import HTTPException, APIRouter
from app.core.schemas import ExportIn
import markdown as md
router = APIRouter(prefix="/export", tags=["export"])

@router.post("/")
async def export_content(payload: ExportIn):
    """Export content to markdown, html, csv, xlsx, pdf"""
    os.makedirs("storage", exist_ok=True)
    export_id = uuid.uuid4().hex[:8]

    if payload.format == "md":
        path = f"storage/export_{export_id}.md";
        open(path, "w", encoding="utf-8").write(payload.content)
        return {
            "download_url": f"/static/export_{export_id}.md"
        }

    if payload.format == "html":
        path = f"storage/export_{export_id}.html";
        html = md.markdown(payload.content)
        html = f"<!doctype html>"