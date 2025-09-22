# POST /chat/stream
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.core.openai_client import client
from app.core.schemas import ChatStreamIn
from app.core.sse import sse_headers, sse_event

router = APIRouter(prefix="/chat", tags=["chat"])


async def event_generator_responses(conversation_id: str | None, payload: ChatStreamIn):
    cid = conversation_id
    if not cid:
        try:
            conv = await client.conversations.create()
            cid = getattr(conv, "id", None)
            if cid:
                yield sse_event({"type": "conversation", "conversation_id": cid})
        except Exception:
            cid = None

    try:
        request_data = {
            "model": payload.model,
            "input": payload.message,
            "instructions": payload.system or "You are a helpful assistant.",
        }
        if cid:
            request_data["conversation"] = cid

        # streaming follow docs: use context manager and event.type
        async with client.responses.stream(**request_data) as stream:
            async for event in stream:
                # output chunks
                et = getattr(event, "type", None)
                if et == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if delta:
                        yield sse_event({"type": "delta", "content": delta})
                elif et == "response.error":
                    error = getattr(event, "error", "")
                    msg = (
                        getattr(error, "message", "unknown error")
                        if error
                        else "unknown error"
                    )
                    yield sse_event({"type": "error", "message": msg})
                elif et == "response.completed":
                    final = await stream.get_final_response()
                    new_cid = getattr(final, "conversation_id", None)
                    if new_cid:
                        yield sse_event(
                            {"type": "conversation", "conversation_id": new_cid}
                        )
        yield sse_event({"type": "done"})
    except Exception as e:
        yield sse_event({"type": "error", "message": str(e)})


@router.post("/stream")
async def stream_chat(payload: ChatStreamIn):
    conversations_id = payload.conversation or None

    return StreamingResponse(
        event_generator_responses(conversations_id, payload),
        media_type="text/event-stream",
        headers=sse_headers(),
    )
