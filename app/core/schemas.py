# app/core/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatStreamIn(BaseModel):
    thread_id: Optional[str] = None
    message: str
    model: str = "gpt-4o-mini"
    system: Optional[str] = None
    metadata: Dict[str, Any] = {}