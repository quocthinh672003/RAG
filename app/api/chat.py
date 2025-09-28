# POST /chat/stream
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.core.openai_client import client
from app.core.schemas import ChatStreamIn
from app.core.sse import sse_headers, sse_event
from app.services.chat_history import save_entry

router = APIRouter(prefix="/chat", tags=["chat"])

async def event_generator_responses(payload: ChatStreamIn):
    try:
        request_data = {
            "model": payload.model,
            "input": payload.message,
            "instructions": payload.system or "You are a helpful assistant.",
        }
        if payload.previous_response_id:
            request_data["previous_response_id"] = payload.previous_response_id

        async with client.responses.stream(**request_data) as stream:
            final = None
            async for event in stream:
                event_type = getattr(event, "type", None)
                if event_type == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if delta:
                        yield sse_event({"type": "delta", "content": delta})
                elif event_type == "response.error":
                    error = getattr(event, "error", "")
                    msg = getattr(error, "message", "unknown error") if error else "unknown error"
                    yield sse_event({"type": "error", "message": msg})

            final = await stream.get_final_response()
            final_text = getattr(final, "output_text", None)
            if final_text:
                yield sse_event({"type": "final", "content": final_text})

        response_id = getattr(final, "id", None)
        yield sse_event({"type": "response", "response_id": response_id})
        yield sse_event({"type": "done"})

        if response_id:
            user_text = payload.message
            assistant_text = getattr(final, "output_text", None)
            created_at = getattr(final, "created_at", None)
            model = getattr(final, "model", None)
            await save_entry(
                response_id=response_id,
                previous_response_id=payload.previous_response_id,
                user_text=user_text,
                assistant_text=assistant_text,
                model=model,
                created_at=created_at,
            )
    except Exception as e:
        yield sse_event({"type": "error", "message": str(e)})

@router.post("/stream")
async def stream_chat(payload: ChatStreamIn):
    return StreamingResponse(
        event_generator_responses(payload),
        media_type="text/event-stream",
        headers=sse_headers(),
    )