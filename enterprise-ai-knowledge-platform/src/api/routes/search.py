"""Search API endpoints - semantic knowledge base search."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request

from src.api.middleware.auth import get_current_user
from src.api.schemas import SearchRequest, SearchResponse, SearchResultItem
from src.shared.session import get_session

router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search_knowledge(request: Request, body: SearchRequest):
    """Search the enterprise knowledge base.

    Performs hybrid semantic + keyword search across all indexed documents,
    respecting department-level access controls.
    """
    user = get_current_user(request)
    start = time.time()

    with get_session(
        role=user.get("role", "CORTEX_AI_USER"),
        warehouse="CORTEX_AI_SEARCH_WH",
    ) as session:
        from src.knowledge_repository import KnowledgeRepositoryService

        service = KnowledgeRepositoryService(session)
        results = service.search(
            query=body.query,
            department_filter=body.department or user.get("department"),
            sensitivity_filter=body.sensitivity_max,
            limit=body.limit,
        )

        latency = (time.time() - start) * 1000

        return SearchResponse(
            query=body.query,
            results=[
                SearchResultItem(
                    chunk_id=r.chunk_id,
                    document_id=r.document_id,
                    chunk_text=r.chunk_text,
                    file_name=r.document_name,
                    department=r.department.value,
                    section_header=r.metadata.get("section_header"),
                    score=r.score,
                )
                for r in results
            ],
            result_count=len(results),
            latency_ms=latency,
        )
