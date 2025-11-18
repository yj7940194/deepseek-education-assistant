from __future__ import annotations

"""REST API routes for the DeepSeek Education Assistant backend."""

from fastapi import APIRouter

from backend.models.message import HealthResponse


router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return a simple health status for the backend."""

    return HealthResponse()

