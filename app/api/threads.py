# GET /threads/:response_id/messages — history via Responses API
from fastapi import HTTPException, APIRouter
from app.core.openai_client import client

router = APIRouter(prefix="/threads", tags=["threads"])

@router.get("/{response_id}/messages")
async def get_messages(response_id: str, limit: int = 50):
    """Get conversation history by traversing previous_response_id chain"""
    
    try:
        messages = []
        current_id = response_id
        
        for _ in range(limit):
            if not current_id:
                break
                
            response = await client.responses.retrieve(current_id)

            #output text
            assistant_text = getattr(response, "output_text", None)
            if not assistant_text:
                chunks = []
                for item in getattr(response, "output", []) or []:
                    for c in getattr(item, "content", []) or []:
                        text = getattr(c, "text", None)
                        if text:
                            chunks.append(text)
                assistant_text = "".join(chunks) if chunks else ""

            # get user_text from input_items
            user_text = ""
            try:
                inputs = await client.responses.input_items.list(response.id)
                for it in getattr(inputs, "data", []) or []:
                    for part in getattr(it, "content", []) or []:
                        # part.text may be is string or object have .text
                        text = getattr(getattr(part, "text", None), "text", None) or getattr(part, "text", None)
                        if text:
                            user_text += text
                    break
            except Exception:
                pass

            if user_text:
                messages.append({
                    "id": f"{response.id}_user",
                    "role": "user",
                    "content": user_text,
                    "created_at": response.created_at,
                    "model": None,
                    "metadata": None,
                })
            if assistant_text:
                messages.append({
                    "id": response.id,
                    "role": "assistant",
                    "content": assistant_text,
                    "created_at": response.created_at,
                    "model": response.model,
                    "metadata": response.metadata,
                })
            # Move to previous response
            current_id = getattr(response, "previous_response_id", None)
        
        return {"response_id": response_id, "messages": list(reversed(messages))}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))