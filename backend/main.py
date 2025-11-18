from __future__ import annotations

"""
FastAPI application entrypoint for the DeepSeek Education Assistant backend.
"""

import logging
from logging.config import dictConfig
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.rest_routes import router as rest_router
from backend.api.websocket_routes import router as websocket_router
from backend.config import get_settings


def configure_logging() -> None:
    """Configure basic structured logging for the application."""

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }
    dictConfig(logging_config)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title="DeepSeek Education Assistant Backend",
        version="0.1.0",
    )

    # CORS configuration for the Vue frontend.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers.
    app.include_router(rest_router)
    app.include_router(websocket_router)

    return app


app = create_app()

