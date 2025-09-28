"""File tool interface."""

from __future__ import annotations

from app.agent.tools.file.dto import FileToolInput, FileToolOutput
from app.agent.tools.file.service import FileToolkit


class FileTool:
    """File tool interface for generating PDF, Excel, and Word files."""

    def __init__(self, service: FileToolkit) -> None:
        self._service = service

    async def __call__(self, payload: FileToolInput) -> FileToolOutput:
        """Generate file based on input payload."""
        return await self._service.generate(payload)
