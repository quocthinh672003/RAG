# GET /threads/:id/messages
import os
from fastapi import HTTPException, APIRouter
from app.core.openai_client import client

USE_ASSISTANTS = os.getenv("USE_ASSISTANTS") == "true"

router = APIRouter(prefix="/threads", tags=["threads"])

@router.get("/{thread_id}/messages")
async def get_messages(thread_id: str, limit: int = 50):
    if not USE_ASSISTANTS:
        raise HTTPException(status_code=501, detail="Assistants mode disabled. Set USE_ASSISTANTS=true.")

    msgs = await client.beta.threads.messages.list(thread_id=thread_id, limit=limit)
    items = []
    for m in reversed(msgs.data):
        text = ""
        for part in m.content:
            if getattr(part, "type", None) == "text":
                text += part.text.value
        items.append({
            "id": m.id,
            "role": m.role,
            "content": text,
            "created_at": m.created_at,
            "model": None,
            "metadata": None,
        })
    return {"thread_id": thread_id, "messages": items}