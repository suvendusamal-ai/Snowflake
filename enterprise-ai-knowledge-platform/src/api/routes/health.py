"""Health check and readiness endpoints."""

from __future__ import annotations

import os
from datetime import datetime

from fastapi import APIRouter

from src.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for SPCS and load balancers."""
    sf_connected = False
    try:
        from src.shared.session import get_session
        with get_session() as session:
            session.sql("SELECT 1").collect()
            sf_connected = True
    except Exception:
        pass

    return HealthResponse(
        status="healthy" if sf_connected else "degraded",
        version="1.0.0",
        environment=os.environ.get("ENVIRONMENT", "dev"),
        snowflake_connected=sf_connected,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/ready")
async def readiness_check():
    """Readiness probe - indicates service can accept traffic."""
    return {"ready": True}
