# POST /chat/stream
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.core.openai_client import client
from app.core.schemas import ChatStreamIn
from app.core.sse import sse_headers, sse_event

router = APIRouter(prefix="/chat", tags=["chat"])

async def event_generator_responses(conversation_id: str | None, payload: ChatStreamIn):
    # send thread_id first
    if conversation_id:
        yield sse_event({"type": "thread_id", "thread_id": conversation_id})

    try:
        request_data = {
            "model": payload.model,
            "input": payload.message,
            "instructions": payload.system or "You are a helpful assistant.",
        }
        if conversation_id:
            request_data["conversation"] = conversation_id

        # streaming follow docs: use context manager and event.type
        async with client.responses.stream(**request_data) as stream:
            async for event in stream:
                #output chunks
                et = getattr(event, "type", None)
                if et == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if delta:
                        yield sse_event({"type": "delta", "content": delta})
                elif et == "response.error":
                    error = getattr(event, "error", "")
                    msg = getattr(error, "message", "unknown error") if error else "unknown error"
                    yield sse_event({"type": "error", "message": msg})
                elif et == "response.completed":
                    # optimized: get full response
                    final_response = await stream.get_final_response()
                    conversation_id = getattr(final_response, "conversation_id", None) or getattr(final_response, "id", None)
                    yield sse_event({"type": "conversation", "conversation_id": conversation_id})
        yield sse_event({"type": "done", "thread_id": conversation_id})
    except Exception as e:
        yield sse_event({"type": "error", "message": str(e)})


@router.post("/stream")
async def stream_chat(payload: ChatStreamIn):
    # use thread_id like conversation_id
    conversations_id = payload.thread_id or None
    
    return StreamingResponse(
        event_generator_responses(conversations_id, payload),
        media_type="text/event-stream",
        headers=sse_headers(),
    )
