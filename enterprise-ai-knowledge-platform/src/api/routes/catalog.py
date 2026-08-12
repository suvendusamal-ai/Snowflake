"""Catalog API endpoints - browse knowledge catalog."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.middleware.auth import get_current_user
from src.api.schemas import CatalogEntry, CatalogResponse
from src.shared.session import get_session

router = APIRouter()


@router.get("", response_model=CatalogResponse)
async def get_catalog(
    request: Request,
    department: str | None = None,
    limit: int = 50,
):
    """Browse the knowledge catalog.

    Returns document-level summaries for discovery and navigation.
    Results respect department-level access controls.
    """
    user = get_current_user(request)

    with get_session(role=user.get("role")) as session:
        from src.knowledge_repository import KnowledgeRepositoryService

        service = KnowledgeRepositoryService(session)
        entries = service.get_catalog(
            department=department or user.get("department"),
            limit=limit,
        )

        return CatalogResponse(
            entries=[
                CatalogEntry(
                    document_id=e.get("DOCUMENT_ID", ""),
                    title=e.get("TITLE", ""),
                    department=e.get("DEPARTMENT", ""),
                    document_type=e.get("DOCUMENT_TYPE"),
                    sensitivity_level=e.get("SENSITIVITY_LEVEL"),
                    chunk_count=e.get("CHUNK_COUNT"),
                    total_tokens=e.get("TOTAL_TOKENS"),
                    last_updated=str(e.get("LAST_UPDATED_AT", "")),
                )
                for e in entries
            ],
            total_count=len(entries),
        )
