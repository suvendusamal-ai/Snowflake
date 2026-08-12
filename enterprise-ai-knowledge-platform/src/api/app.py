"""Enterprise AI Knowledge Platform - REST API Application."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import chat, documents, search, catalog, health, admin
from src.api.middleware.auth import AuthMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown hooks."""
    logger.info("Enterprise AI Knowledge Platform API starting...")
    yield
    logger.info("API shutting down.")


def create_app() -> FastAPI:
    """Application factory - creates and configures the FastAPI app."""
    app = FastAPI(
        title="Enterprise AI Knowledge Platform",
        description=(
            "REST API for the Enterprise AI Knowledge Platform. "
            "Provides AI-powered document search, knowledge management, "
            "and intelligent chat capabilities powered by Snowflake Cortex AI."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    allowed_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth middleware
    app.add_middleware(AuthMiddleware)

    # Register routers
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
    app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
    app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["Catalog"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"])

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
        reload=os.environ.get("ENVIRONMENT", "dev") == "dev",
    )
