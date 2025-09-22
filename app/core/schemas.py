# app/core/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatStreamIn(BaseModel):
    message: str
    model: str = "gpt-4o-mini"
    system: Optional[str] = None
    conversation: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ReportIn(BaseModel):
    schema_id: str
    query: str
    model: str = "gpt-4o-mini"


class ImageIn(BaseModel):
    prompt: str
    size: str = "1024x1024"
    transparent: bool = False


class ExportIn(BaseModel):
    format: str = Field(..., pattern="^(md|html|csv|xlsx|pdf)$")
    content: str
    title: Optional[str] = None
