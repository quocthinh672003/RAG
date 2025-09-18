# app/main.py
import os, json, uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from app.core.openai_client import client
from app.core.schemas import ChatStreamIn

USE_ASSISTANTS = os.getenv("USE_ASSISTANTS") == "true"
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

if not ASSISTANT_ID:
    raise HTTPException(status_code=500, detail="ASSISTANT_ID is not set")
app = FastAPI(title="RAG API", version="1.0.0")

async def event_generator_assistants(thread_id: str, payload: ChatStreamIn):
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
                if event_name == "response.output_text.delta":
                    delta = getattr(event, "delta", None)
                    if delta is None and hasattr(event, "data"):
                        delta = getattr(event.data, "delta", "")
                    chunk = delta or ""
                    if chunk:
                        assistant_buffer.append(chunk)
                        yield sse_event({"type": "delta", "content": chunk})
                elif event_name == "response.error":
                    err = None
                    if hasattr(event, "error"):
                        err = getattr(event, "error")
                    elif hasattr(event, "data") and hasattr(event.data, "error"):
                        err = event.data.error
                    message = getattr(err, "message", "Unknown error") if err else "Unknown error"
                    yield sse_event({"type": "error", "message": message})
        # If not assistant_buffer, get last message from thread
        if not assistant_buffer:
            try:
                msgs = await client.beta.threads.messages.list(thread_id=thread_id, limit=5)
                text = ""
                for m in msgs.data:
                    if getattr(m, "role", "") == "assistant":
                        # concat text parts
                        for part in getattr(m, "content", []) or []:
                            if getattr(part, "type", None) == "text":
                                text += part.text.value
                        break
                if text:
                    yield sse_event({"type": "delta", "content": text})
            except Exception:
                pass
        yield sse_event({"type": "done", "thread_id": thread_id})
    except Exception as e:
        yield sse_event({"type": "error", "message": str(e)})

# Mount static files
STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STORAGE_DIR, html=False), name="static")

def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

@app.post("/chat/stream")
async def stream_chat(payload: ChatStreamIn):
    if not USE_ASSISTANTS:
        raise HTTPException(status_code=501, detail="Assistants mode disabled. Set USE_ASSISTANTS=true.")

    thread_id = payload.thread_id
    if not thread_id:
        thr = await client.beta.threads.create()
        thread_id = thr.id
    return StreamingResponse(
        event_generator_assistants(thread_id, payload),
        media_type="text/event-stream",
    )

@app.get("/threads/{thread_id}/messages")
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

@app.get("/")
async def root():
    return {"message": "RAG API is running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)