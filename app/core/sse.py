# SSE helpers( server sent event)
import json
from typing import Dict, Any

def sse_event(data: Dict[str, Any]) -> str:
    """Format data as Server-Sent Event"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

def sse_headers() -> dict:
    """Standard SSE headers"""
    return {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }