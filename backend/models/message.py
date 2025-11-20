from __future__ import annotations

"""Pydantic models for chat messages and WebSocket payloads."""

from typing import Literal, Optional
from pydantic import BaseModel


class UserMessage(BaseModel):
    """Incoming user message sent over WebSocket."""

    type: Literal["user_message"] = "user_message"
    message_id: str
    content: str
    conversation_id: Optional[str] = None


class AssistantChunk(BaseModel):
    """Outgoing assistant message chunk sent over WebSocket."""

    type: Literal["assistant_chunk"] = "assistant_chunk"
    message_id: str
    content: str
    is_final: bool = False


class HealthResponse(BaseModel):
    """Simple health-check response body."""

    status: Literal["ok"] = "ok"
