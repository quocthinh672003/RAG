# GET /threads/:id/messages
import os
from fastapi import HTTPException, APIRouter
from app.core.openai_client import client

USE_ASSISTANTS = os.getenv("USE_ASSISTANTS") == "true"

router = APIRouter(prefix="/threads", tags=["threads"])

@router.get("/{thread_id}/messages")
async def get_messages(thread_id: str, limit: int = 50):
    #responses API: list follow conversation = thread_id
    try:
        responses = await client.responses.list(conversation=thread_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    items = []
    # text from output
    for r in reversed(getattr(responses, "output", []) or []):
        text = ""
        for item in getattr((r, "content", []) or []):
            for c in getattr((item, "content", []) or []):
                t = getattr(c, "text", None)
                if t:
                    text += t
        if text:
            items.append({
                "id": r.id,
                "role": "assistant",
                "content": text,
                "created_at": getattr(r, "created_at", None),
                "model": getattr(r, "model", None),
                "metadata": getattr(r, "metadata", None),
            })
    return {"thread_id": thread_id, "messages": items}