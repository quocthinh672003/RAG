# app/services/chat_history.py
from __future__ import annotations

import time
from asyncio import Lock
from typing import Any, Dict, List, Optional, Tuple

_HISTORY: Dict[str, Dict[str, Any]] = {}
_LOCK = Lock()


def _build_user_message(response_id: str, text: Optional[str], created_at: float) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    return {
        "id": f"{response_id}_user",
        "role": "user",
        "content": text,
        "created_at": created_at,
        "model": None,
        "metadata": None,
    }


def _build_assistant_message(response_id: str, text: Optional[str], created_at: float, model: Optional[str]) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    return {
        "id": response_id,
        "role": "assistant",
        "content": text,
        "created_at": created_at,
        "model": model,
        "metadata": None,
    }


async def save_entry(
    *,
    response_id: Optional[str],
    previous_response_id: Optional[str],
    user_text: Optional[str],
    assistant_text: Optional[str],
    model: Optional[str],
    created_at: Optional[float],
) -> None:
    if not response_id:
        return

    timestamp = created_at if created_at is not None else time.time()
    user_msg = _build_user_message(response_id, user_text, timestamp)
    assistant_msg = _build_assistant_message(response_id, assistant_text, timestamp, model)

    async with _LOCK:
        _HISTORY[response_id] = {
            "previous_response_id": previous_response_id,
            "user": user_msg,
            "assistant": assistant_msg,
        }


async def build_thread_messages(response_id: str, limit: int = 50) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    messages: List[Dict[str, Any]] = []
    current_id: Optional[str] = response_id

    async with _LOCK:
        for _ in range(limit):
            if not current_id:
                break

            entry = _HISTORY.get(current_id)
            if not entry:
                break

            user_msg = entry.get("user")
            assistant_msg = entry.get("assistant")

            if user_msg:
                messages.append(user_msg)
            if assistant_msg:
                messages.append(assistant_msg)

            current_id = entry.get("previous_response_id")

    return list(reversed(messages)), current_id
