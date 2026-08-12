"""Administration endpoints - platform stats, monitoring."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.middleware.auth import get_current_user
from src.api.schemas import PlatformStatsResponse
from src.shared.session import get_session

router = APIRouter()


@router.get("/stats", response_model=PlatformStatsResponse)
async def get_platform_stats(request: Request):
    """Get platform-wide statistics (admin only)."""
    user = get_current_user(request)

    with get_session(role="CORTEX_AI_ADMIN") as session:
        doc_count = session.sql(
            "SELECT COUNT(*) AS CNT FROM RAW.DOCUMENT_REGISTRY"
        ).collect()[0]["CNT"]

        chunk_count = session.sql(
            "SELECT COUNT(*) AS CNT FROM KNOWLEDGE.DOCUMENT_CHUNKS"
        ).collect()[0]["CNT"]

        dept_stats = session.sql("""
            SELECT DEPARTMENT, COUNT(*) AS DOC_COUNT
            FROM RAW.DOCUMENT_REGISTRY
            GROUP BY DEPARTMENT ORDER BY DOC_COUNT DESC
        """).collect()

        return PlatformStatsResponse(
            total_documents=doc_count,
            total_chunks=chunk_count,
            departments=[
                {"department": r["DEPARTMENT"], "documents": r["DOC_COUNT"]}
                for r in dept_stats
            ],
            search_service_status="ACTIVE",
        )


@router.get("/conversations/recent")
async def get_recent_conversations(request: Request, limit: int = 20):
    """Get recent conversations across all users (admin only)."""
    with get_session(role="CORTEX_AI_ADMIN") as session:
        result = session.sql(f"""
            SELECT CONVERSATION_ID, USER_ID, DEPARTMENT, TITLE,
                   MESSAGE_COUNT, STARTED_AT, LAST_ACTIVITY_AT
            FROM AGENT.CONVERSATIONS
            ORDER BY LAST_ACTIVITY_AT DESC
            LIMIT {limit}
        """).collect()

        return {"conversations": [dict(r) for r in result]}


@router.get("/guardrails/violations")
async def get_recent_violations(request: Request, limit: int = 50):
    """Get recent guardrail violations (admin only)."""
    with get_session(role="CORTEX_AI_ADMIN") as session:
        result = session.sql(f"""
            SELECT LOG_ID, EVENT_TYPE, CONVERSATION_ID, USER_ID,
                   VIOLATION_TYPE, VIOLATION_DETAILS, ACTION_TAKEN, CREATED_AT
            FROM GOVERNANCE.AI_GOVERNANCE_LOG
            WHERE EVENT_TYPE = 'GUARDRAIL_VIOLATION'
            ORDER BY CREATED_AT DESC
            LIMIT {limit}
        """).collect()

        return {"violations": [dict(r) for r in result]}
