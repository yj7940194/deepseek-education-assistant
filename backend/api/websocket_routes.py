from __future__ import annotations

"""WebSocket routes for chat interactions."""

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.config import get_settings
from backend.models.message import AssistantChunk, UserMessage
from backend.services.deepseek_service import DeepSeekService
from backend.services.rag_service import RAGService
from backend.utils.neo4j_client import Neo4jClient


logger = logging.getLogger(__name__)

router = APIRouter(tags=["ws"])

_settings = get_settings()
_neo4j_client: Optional[Neo4jClient]
if (
    _settings.neo4j_uri
    and _settings.neo4j_user
    and _settings.neo4j_password
):
    _neo4j_client = Neo4jClient(
        uri=_settings.neo4j_uri,
        user=_settings.neo4j_user,
        password=_settings.neo4j_password,
    )
else:
    logger.warning("Neo4j configuration incomplete; RAG will run without graph data")
    _neo4j_client = None

_rag_service = RAGService(_neo4j_client)
_deepseek_service = DeepSeekService(
    api_key=_settings.deepseek_api_key,
    api_base=_settings.deepseek_api_base,
)

_SYSTEM_PROMPT = (
    "You are an educational Q&A assistant. "
    "Use the provided knowledge graph context when helpful, and give clear, "
    "concise explanations suitable for students."
)


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for chat with RAG + DeepSeek streaming.
    """

    await websocket.accept()
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload: dict[str, Any] = json.loads(raw_data)
                message = UserMessage.model_validate(payload)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Invalid WebSocket payload: %s", exc)
                await websocket.send_text(
                    AssistantChunk(
                        message_id="unknown",
                        content="Invalid message format.",
                        is_final=True,
                    ).model_dump_json()
                )
                continue

            try:
                context = await _rag_service.build_context(message.content)
                user_prompt = f"{context}\n\nUser question: {message.content}"
            except Exception as exc:  # noqa: BLE001
                logger.error("Error while building RAG context: %s", exc)
                await websocket.send_text(
                    AssistantChunk(
                        message_id=message.message_id,
                        content=(
                            "An error occurred while retrieving context from the "
                            "knowledge graph. I will answer without it."
                        ),
                        is_final=False,
                    ).model_dump_json()
                )
                user_prompt = message.content

            # Stream response from DeepSeek and forward chunks to the client.
            try:
                async for chunk in _deepseek_service.astream_chat(
                    system_prompt=_SYSTEM_PROMPT,
                    user_content=user_prompt,
                ):
                    await websocket.send_text(
                        AssistantChunk(
                            message_id=message.message_id,
                            content=chunk,
                            is_final=False,
                        ).model_dump_json()
                    )

                # Final empty chunk to signal completion.
                await websocket.send_text(
                    AssistantChunk(
                        message_id=message.message_id,
                        content="",
                        is_final=True,
                    ).model_dump_json()
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Error during DeepSeek streaming: %s", exc)
                await websocket.send_text(
                    AssistantChunk(
                        message_id=message.message_id,
                        content=(
                            "An error occurred while generating the answer. "
                            "Please try again later."
                        ),
                        is_final=True,
                    ).model_dump_json()
                )
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected WebSocket error: %s", exc)
        await websocket.close()

