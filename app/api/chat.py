#POST /chat/stream
import os
from fastapi import HTTPException, APIRouter
from fastapi.responses import StreamingResponse
from app.core.openai_client import client
from app.core.schemas import ChatStreamIn
from app.core.sse import sse_headers, sse_event
router = APIRouter(prefix="/chat", tags=["chat"])

USE_ASSISTANTS = os.getenv("USE_ASSISTANTS") == "true"

async def event_generator_assistants(thread_id: str, payload: ChatStreamIn):
    ASSISTANT_ID = os.getenv("ASSISTANT_ID")
    # send thread_id first
    yield sse_event({"type": "thread_id", "thread_id": thread_id})
    
    await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=payload.message,
    )

    assistant_buffer: list[str] = []
    try:
        async with client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
            instructions=(payload.system or None),
        ) as stream:
            async for event in stream:
                # SDK versions may expose `type` or `event`, and `delta` under `data`
                event_name = getattr(event, "type", None) or getattr(event, "event", None)
                if event_name == "thread.message.delta":
                    # assistant api have structured: event.data.delta.content[].text.value
                    event_data = getattr(event, "data", event)
                    if hasattr(event_data, "delta"):
                        delta_content = getattr(event_data.delta, "content", [])
                        for content in delta_content:
                            if content and getattr(content, "type", None) == "text":
                                chunk = getattr(content.text, "value", "")
                                if chunk:
                                    assistant_buffer.append(chunk)
                                    yield sse_event({"type": "delta", "content":chunk})
                elif event_name == "error":
                    err = None
                    if hasattr(event, "error"):
                        err = getattr(event, "error")
                    elif hasattr(event, "data") and hasattr(event.data, "error"):
                        err = event.data.error
                    message = getattr(err, "message", "Unknown error") if err else "Unknown error"
                    yield sse_event({"type": "error", "message": message})
        # If not assistant_buffer, get last message from thread
        # if not assistant_buffer:
        #     try:
        #         msgs = await client.beta.threads.messages.list(thread_id=thread_id, limit=5)
        #         text = ""
        #         for m in msgs.data:
        #             if getattr(m, "role", "") == "assistant":
        #                 # concat text parts
        #                 for part in getattr(m, "content", []) or []:
        #                     if getattr(part, "type", None) == "text":
        #                         text += part.text.value
        #                 break
        #         if text:
        #             yield sse_event({"type": "delta", "content": text})
        #     except Exception:
        #         pass
        # yield sse_event({"type": "done", "thread_id": thread_id})
    except Exception as e:
        yield sse_event({"type": "error", "message": str(e)})

@router.post("/stream")
async def stream_chat(payload: ChatStreamIn):
    if not USE_ASSISTANTS:
        raise HTTPException(status_code=501, detail="Assistants mode disabled. Set USE_ASSISTANTS=true.")

    ASSISTANT_ID = os.getenv("ASSISTANT_ID")
    if not ASSISTANT_ID:
        raise HTTPException(status_code=500, detail="ASSISTANT_ID is not set")

    thread_id = payload.thread_id
    if not thread_id:
        thr = await client.beta.threads.create()
        thread_id = thr.id

    return StreamingResponse(
        event_generator_assistants(thread_id, payload),
        media_type="text/event-stream",
        headers=sse_headers(),
    )