"""Dependency injection for file tool."""

from __future__ import annotations

from pathlib import Path

from app.agent.tools.file.service import FileToolkit
from app.agent.tools.file.storage import FileStorage
from app.agent.tools.file.tool import FileTool


def create_file_tool(storage_dir: Path) -> FileTool:
    """Create file tool with dependencies."""
    storage = FileStorage(storage_dir)
    service = FileToolkit(storage)
    return FileTool(service)
