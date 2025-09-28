# GET /threads/:response_id/messages
from fastapi import HTTPException, APIRouter
from app.core.openai_client import client
from app.services.chat_history import build_thread_messages, save_entry

router = APIRouter(prefix="/threads", tags=["threads"])

@router.get("/{response_id}/messages")
async def get_messages(response_id: str, limit: int = 50):
    try:
        cached_messages, missing_id = await build_thread_messages(response_id, limit)
        if cached_messages and not missing_id:
            return {
                "response_id": response_id,
                "messages": cached_messages,
                "source": "cache",
            }

        messages = list(cached_messages)
        current_id = missing_id or response_id
        fetched_any = False

        for _ in range(limit - len(messages)):
            if not current_id:
                break

            response = await client.responses.retrieve(current_id)
            fetched_any = True

            assistant_chunks = []
            for block in getattr(response, "output", []) or []:
                for c in getattr(block, "content", []) or []:
                    if getattr(c, "type", None) == "output_text":
                        text = getattr(c, "text", None)
                        if text:
                            assistant_chunks.append(text)
            assistant_text = "".join(assistant_chunks) if assistant_chunks else ""

            user_chunks = []
            try:
                inputs_list = await client.responses.input_items.list(response.id)
                for input_item in getattr(inputs_list, "data", []) or []:
                    for part in getattr(input_item, "content", []) or []:
                        if getattr(part, "type", None) == "input_text":
                            text = getattr(part, "text", None)
                            if text:
                                user_chunks.append(text)
            except Exception:
                pass
            user_text = "".join(user_chunks) if user_chunks else None

            created_at = getattr(response, "created_at", None)
            model = getattr(response, "model", None)
            previous_id = getattr(response, "previous_response_id", None)

            if user_text:
                messages.append({
                    "id": f"{response.id}_user",
                    "role": "user",
                    "content": user_text,
                    "created_at": created_at,
                    "model": None,
                    "metadata": None,
                })

            if assistant_text:
                messages.append({
                    "id": response.id,
                    "role": "assistant",
                    "content": assistant_text,
                    "created_at": created_at,
                    "model": model,
                    "metadata": getattr(response, "metadata", None),
                })

            # Persist this exchange into cache for future requests
            await save_entry(
                response_id=response.id,
                previous_response_id=previous_id,
                user_text=user_text,
                assistant_text=assistant_text,
                model=model,
                created_at=created_at,
            )

            current_id = previous_id

        # Deduplicate by message id while preserving order by created_at
        messages.sort(key=lambda msg: msg.get("created_at") or 0)
        deduped = []
        seen_ids = set()
        for msg in messages:
            msg_id = msg.get("id")
            if msg_id and msg_id in seen_ids:
                continue
            if msg_id:
                seen_ids.add(msg_id)
            deduped.append(msg)

        source = "cache"
        if fetched_any:
            source = "cache+openai" if cached_messages else "openai"

        return {
            "response_id": response_id,
            "messages": deduped,
            "source": source,
            "missing_from": current_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))