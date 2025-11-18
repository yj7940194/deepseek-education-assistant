from __future__ import annotations

"""Pydantic models for chat messages and WebSocket payloads."""

from typing import Optional
from pydantic import BaseModel, Field


class UserMessage(BaseModel):
    """Incoming user message sent over WebSocket."""

    type: str = Field("user_message", const=True)
    message_id: str
    content: str
    conversation_id: Optional[str] = None


class AssistantChunk(BaseModel):
    """Outgoing assistant message chunk sent over WebSocket."""

    type: str = Field("assistant_chunk", const=True)
    message_id: str
    content: str
    is_final: bool = False


class HealthResponse(BaseModel):
    """Simple health-check response body."""

    status: str = "ok"
