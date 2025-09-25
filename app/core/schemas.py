# app/core/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union


class ChatStreamIn(BaseModel):
    message: str
    model: str = "gpt-4o-mini"
    system: Optional[str] = None
    previous_response_id: Optional[str] = None
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
    format: str = Field(..., pattern="^(md|html|csv|xlsx|pdf|docx|pptx)$")
    content: str
    title: Optional[str] = None


class ChartIn(BaseModel):
    chart_type: str = Field(..., pattern="^(line|bar|pie|scatter|histogram|heatmap)$")
    data: Union[str, List[Any], Dict[str, Any]]
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    output_format: str = Field(default="png", pattern="^(png|jpg|svg|pdf)$")