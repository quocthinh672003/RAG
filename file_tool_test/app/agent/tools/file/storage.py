"""File storage for PDF, Excel, Word files."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional


class FileStorage:
    """File storage with support for different file types."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self, 
        content: bytes, 
        filename: str,
        subdir: Optional[str] = None
    ) -> Path:
        """Save file content."""
        if subdir:
            target_dir = self.base_dir / subdir
            target_dir.mkdir(parents=True, exist_ok=True)
            path = target_dir / filename
        else:
            path = self.base_dir / filename
        
        path.write_bytes(content)
        return path

    def get_file_info(self, path: Path) -> dict:
        """Get file metadata."""
        stat = path.stat()
        return {
            "size_bytes": stat.st_size,
            "mime_type": self._guess_mime_type(path),
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime
        }

    def _guess_mime_type(self, path: Path) -> str:
        """Guess MIME type from file extension."""
        ext = path.suffix.lower()
        mime_map = {
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain'
        }
        return mime_map.get(ext, 'application/octet-stream')
