"""File tool DTOs for PDF, Excel, Word generation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FileToolInput(BaseModel):
    """Input schema for file generation tool."""
    
    format: str = Field(..., pattern="^(pdf|excel|word)$", description="File format: pdf, excel, word")
    content: str = Field(..., description="Content to generate file from")
    title: Optional[str] = Field(None, description="Optional title for the document")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Structured data for tabular formats")


class FileToolOutput(BaseModel):
    """Output schema for file generation tool."""
    
    file_path: str = Field(..., description="Path where the file was saved")
    filename: str = Field(..., description="Generated filename")
    mime_type: str = Field(..., description="MIME type of the generated file")
    size_bytes: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="File format that was generated")
