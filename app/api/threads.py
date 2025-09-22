# GET /threads/:conversation/messages — history via Responses API
from fastapi import HTTPException, APIRouter
from app.core.openai_client import client

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("/{conversation_id}/messages")
async def get_messages(conversation_id: str, limit: int = 50):
    try:
        page = await client.responses.list(conversation=conversation_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    items = []
    for m in reversed(getattr(page, "data", []) or []):
        role = getattr(m, "role", None) or "assistant"
        text = ""
        for part in getattr(m, "content", []) or []:
            value = getattr(getattr(part, "text", None), "value", "")
            if value:
                text += value
        if text:
            items.append(
                {
                    "id": getattr(m, "id", None),
                    "role": role,
                    "content": text,
                    "created_at": getattr(m, "created_at", None),
                    "model": getattr(m, "model", None),
                    "metadata": getattr(m, "metadata", None),
                }
            )

    return {"conversation_id": conversation_id, "messages": items}
